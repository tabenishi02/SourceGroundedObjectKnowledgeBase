"""R2 Knowledge Search generation rebuild, cutover, and rollback lifecycle."""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from .retrieval.generation import (
    GenerationAwareSearchRepresentationBuilder,
    GenerationRoutingVectorIndexAdapter,
    route_generation_vector_index,
)
from .retrieval.hybrid_search_r2 import HybridObjectSearch
from .retrieval.similarity_r2 import ObjectSimilaritySearch
from .retrieval.vector_maintenance import KnowledgeVectorMaintenanceBuilder

LEGACY_GENERATION_ID = "search-generation:phase-i-v1"
PHASE_I_CONTRACT_KEY = "phase-i-search-v1"
R2_CONTRACT_KEY = "n05d04r2-hierarchical-v2"


class KnowledgeSearchGenerationError(RuntimeError):
    """Generation lifecycle verification or transition failed closed."""


class KnowledgeSearchGenerationRuntimeUnavailableError(KnowledgeSearchGenerationError):
    """Required local Embedding/Vector runtime was not configured."""


@dataclass(frozen=True, slots=True)
class GenerationBuildResult:
    generation_id: str
    contract_key: str
    state: str
    source_catalog_digest: str
    membership_digest: str
    membership_count: int
    reused_embedding_count: int
    created_embedding_count: int
    backend_key: str
    namespace_key: str
    point_count: int


@dataclass(frozen=True, slots=True)
class GenerationSwitchResult:
    from_generation_id: str | None
    to_generation_id: str
    switch_kind: str
    activation_revision: int
    source_catalog_digest: str


class KnowledgeSearchGenerationApplication:
    """Operator boundary for side-by-side Derived Search generation lifecycle."""

    def __init__(
        self,
        repository,
        *,
        embedding_provider=None,
        vector_index=None,
        embedding_batch_size: int = 32,
    ) -> None:
        if embedding_batch_size <= 0:
            raise ValueError("embedding_batch_size must be positive")
        self.repository = repository
        self.db = repository.db
        self.embedding_provider = embedding_provider
        self.vector_index = route_generation_vector_index(repository, vector_index)
        self.embedding_batch_size = embedding_batch_size
        self.builder = GenerationAwareSearchRepresentationBuilder(repository)

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    @staticmethod
    def _hash_rows(rows) -> str:
        payload = json.dumps(
            rows,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()

    def _accepted_versions(self) -> tuple[str, ...]:
        return tuple(
            row["version_id"]
            for row in self.db.execute(
                """SELECT l.version_id
                   FROM object_version_lifecycle l
                   WHERE l.state='accepted'
                   ORDER BY l.version_id"""
            ).fetchall()
        )

    def source_catalog_digest(self) -> str:
        rows = []
        for row in self.db.execute(
            """SELECT o.id AS object_id,o.status,o.current_version_id,
                      l.version_id,cs.primary_class_id
               FROM object_version_lifecycle l
               JOIN object_versions v ON v.id=l.version_id
               JOIN objects o ON o.id=v.object_id
               JOIN object_version_classification_snapshots cs ON cs.version_id=l.version_id
               WHERE l.state='accepted'
               ORDER BY o.id,l.version_id"""
        ).fetchall():
            additional = [
                item["class_id"]
                for item in self.db.execute(
                    """SELECT class_id
                       FROM object_version_additional_class_snapshots
                       WHERE version_id=?
                       ORDER BY class_id""",
                    (row["version_id"],),
                ).fetchall()
            ]
            rows.append(
                {
                    "object_id": row["object_id"],
                    "object_status": row["status"],
                    "current_version_id": row["current_version_id"],
                    "version_id": row["version_id"],
                    "primary_class_id": row["primary_class_id"],
                    "additional_class_ids": additional,
                }
            )
        return self._hash_rows(rows)

    def _generation_row(self, generation_id: str) -> dict:
        row = self.db.execute(
            "SELECT * FROM knowledge_search_generations WHERE id=?",
            (generation_id,),
        ).fetchone()
        if row is None:
            raise KnowledgeSearchGenerationError(
                f"Unknown Knowledge Search generation: {generation_id}"
            )
        return dict(row)

    def _generation_membership_rows(self, generation_id: str) -> list[dict]:
        return [
            dict(row)
            for row in self.db.execute(
                """SELECT m.id AS membership_id,m.object_id,m.version_id,m.target_kind,
                          m.facet_id,m.statement_id,r.kind AS representation_kind,
                          r.builder_key,r.builder_version,r.content_hash,
                          m.representation_id
                   FROM knowledge_search_generation_memberships gm
                   JOIN knowledge_search_representation_memberships m ON m.id=gm.membership_id
                   JOIN search_representations r ON r.id=m.representation_id
                   WHERE gm.generation_id=?
                   ORDER BY m.object_id,m.version_id,m.target_kind,
                            coalesce(m.facet_id,''),coalesce(m.statement_id,''),m.id""",
                (generation_id,),
            ).fetchall()
        ]

    def membership_digest(self, generation_id: str) -> str:
        projection = [
            {
                "object_id": row["object_id"],
                "version_id": row["version_id"],
                "target_kind": row["target_kind"],
                "facet_id": row["facet_id"],
                "statement_id": row["statement_id"],
                "representation_kind": row["representation_kind"],
                "builder_key": row["builder_key"],
                "builder_version": row["builder_version"],
                "content_hash": row["content_hash"],
            }
            for row in self._generation_membership_rows(generation_id)
        ]
        return self._hash_rows(projection)

    def _eligible_statement_keys(self) -> set[tuple[str, str]]:
        return {
            (row["version_id"], row["statement_id"])
            for row in self.db.execute(
                """SELECT s.version_id,s.id AS statement_id
                   FROM knowledge_statements s
                   JOIN object_version_lifecycle l ON l.version_id=s.version_id
                   LEFT JOIN object_version_facets vf
                     ON vf.version_id=s.version_id AND vf.facet_id=s.facet_id
                   WHERE l.state='accepted'
                     AND (s.facet_id IS NULL OR vf.status='content')"""
            ).fetchall()
        }

    def _eligible_facet_keys(self) -> set[tuple[str, str]]:
        return {
            (row["version_id"], row["facet_id"])
            for row in self.db.execute(
                """SELECT DISTINCT vf.version_id,vf.facet_id
                   FROM object_version_facets vf
                   JOIN object_version_lifecycle l ON l.version_id=vf.version_id
                   JOIN knowledge_statements s
                     ON s.version_id=vf.version_id AND s.facet_id=vf.facet_id
                   WHERE l.state='accepted' AND vf.status='content'"""
            ).fetchall()
        }

    def _validate_generation_shape(self, generation_id: str, contract_key: str) -> int:
        rows = self._generation_membership_rows(generation_id)
        accepted_versions = set(self._accepted_versions())
        row_versions = {row["version_id"] for row in rows}
        if not row_versions.issubset(accepted_versions):
            raise KnowledgeSearchGenerationError(
                "Generation contains membership for a non-accepted Version"
            )

        object_kind = (
            "object_overview" if contract_key == R2_CONTRACT_KEY else "object_overall"
        )
        forbidden_kind = (
            "object_overall" if contract_key == R2_CONTRACT_KEY else "object_overview"
        )
        if any(row["target_kind"] == forbidden_kind for row in rows):
            raise KnowledgeSearchGenerationError(
                f"Generation contains forbidden membership kind: {forbidden_kind}"
            )

        object_counts: dict[str, int] = {}
        for row in rows:
            if row["target_kind"] == object_kind:
                object_counts[row["version_id"]] = object_counts.get(row["version_id"], 0) + 1
        missing_object = sorted(
            version_id
            for version_id in accepted_versions
            if object_counts.get(version_id) != 1
        )
        if missing_object:
            raise KnowledgeSearchGenerationError(
                f"Generation does not have exactly one {object_kind} per accepted Version; "
                f"count={len(missing_object)}"
            )

        actual_statements = {
            (row["version_id"], row["statement_id"])
            for row in rows
            if row["target_kind"] == "statement"
        }
        expected_statements = self._eligible_statement_keys()
        if actual_statements != expected_statements:
            raise KnowledgeSearchGenerationError(
                "Generation Statement membership set differs from accepted canonical Knowledge"
            )

        actual_facets = {
            (row["version_id"], row["facet_id"])
            for row in rows
            if row["target_kind"] == "facet"
        }
        expected_facets = self._eligible_facet_keys()
        if actual_facets != expected_facets:
            raise KnowledgeSearchGenerationError(
                "Generation Facet membership set differs from accepted canonical Knowledge"
            )
        return len(rows)

    def _runtime(self):
        if self.embedding_provider is None or self.vector_index is None:
            raise KnowledgeSearchGenerationRuntimeUnavailableError(
                "Generation build/cutover requires an explicitly configured local semantic runtime"
            )
        return self.embedding_provider.space, self.vector_index

    def _bound_index(self, namespace_key: str):
        vector_index = self.vector_index
        if isinstance(vector_index, GenerationRoutingVectorIndexAdapter):
            return vector_index.bind_namespace(namespace_key)
        binder = getattr(vector_index, "bind_namespace", None)
        if binder is None:
            raise KnowledgeSearchGenerationRuntimeUnavailableError(
                "Configured Vector backend cannot create an isolated generation namespace"
            )
        return binder(namespace_key)

    def _legacy_namespace(self, space) -> tuple[str, object]:
        vector_index = self.vector_index
        if isinstance(vector_index, GenerationRoutingVectorIndexAdapter):
            key = vector_index.legacy_namespace_key(space)
            return key, vector_index.bind_namespace(key)
        getter = getattr(vector_index, "namespace_key", None)
        if getter is None:
            raise KnowledgeSearchGenerationRuntimeUnavailableError(
                "Configured Vector backend cannot identify its legacy namespace"
            )
        key = str(getter(space))
        return key, vector_index

    def _audit_namespace(
        self,
        index,
        space,
        generation_id: str,
        contract_key: str,
    ) -> int:
        expected_ids = tuple(
            row["membership_id"] for row in self._generation_membership_rows(generation_id)
        )
        auditor = getattr(index, "audit_memberships", None)
        if auditor is not None:
            try:
                return int(
                    auditor(
                        space,
                        expected_ids,
                        generation_id=generation_id,
                        require_generation_payload=(contract_key == R2_CONTRACT_KEY),
                    )
                )
            except Exception as exc:
                raise KnowledgeSearchGenerationError(
                    f"Vector namespace identity audit failed: {exc}"
                ) from exc

        points = getattr(index, "points", None)
        if points is None:
            raise KnowledgeSearchGenerationError(
                "Vector backend cannot prove generation membership identity"
            )
        if set(points) != set(expected_ids):
            raise KnowledgeSearchGenerationError(
                "Vector namespace membership identity differs from generation membership set"
            )
        if contract_key == R2_CONTRACT_KEY:
            for point in points.values():
                if point.metadata.get("generation_id") != generation_id:
                    raise KnowledgeSearchGenerationError(
                        "Vector namespace generation payload mismatch"
                    )
        return len(points)

    def _candidate_namespace(self, generation_id: str, space_id: str) -> str:
        base = getattr(
            getattr(self.vector_index, "base_vector_index", self.vector_index),
            "collection_prefix",
            "sgokb_vector",
        )
        suffix = hashlib.sha256(f"{generation_id}:{space_id}".encode("utf-8")).hexdigest()[:24]
        return f"{base}_generation_{suffix}"

    def _complete_embeddings(self, generation_id: str) -> tuple[int, int]:
        space, _ = self._runtime()
        self.repository.embedding_store.ensure_space(space)
        rows = self._generation_membership_rows(generation_id)
        representation_ids = tuple(dict.fromkeys(row["representation_id"] for row in rows))
        existing = {
            row["representation_id"]
            for row in self.repository.embedding_store.embedding_rows(
                space.space_id,
                representation_ids,
            )
        }
        missing = [
            representation_id
            for representation_id in representation_ids
            if representation_id not in existing
        ]
        for start in range(0, len(missing), self.embedding_batch_size):
            batch_ids = missing[start : start + self.embedding_batch_size]
            records = [
                self.repository.semantic_store.search_representation(representation_id)
                for representation_id in batch_ids
            ]
            vectors = self.embedding_provider.embed_documents(
                [record.content for record in records]
            )
            if len(vectors) != len(records):
                raise KnowledgeSearchGenerationError(
                    "Embedding provider returned a different number of vectors than documents"
                )
            for record, vector in zip(records, vectors):
                self.repository.embedding_store.save_representation_embedding(
                    space,
                    record.representation_id,
                    vector,
                )
        completed = {
            row["representation_id"]
            for row in self.repository.embedding_store.embedding_rows(
                space.space_id,
                representation_ids,
            )
        }
        if completed != set(representation_ids):
            raise KnowledgeSearchGenerationError(
                "Generation Embedding completion left missing Search Representations"
            )
        return len(existing), len(missing)

    def _upsert_binding(
        self,
        generation_id: str,
        *,
        space_id: str,
        backend_key: str,
        namespace_key: str,
        status: str,
        membership_digest: str | None,
        point_count: int | None,
        last_error: str | None = None,
    ) -> None:
        now = self._now()
        self.db.execute(
            """INSERT INTO knowledge_search_generation_vector_indexes(
                   generation_id,embedding_space_id,backend_key,namespace_key,status,
                   membership_digest,point_count,created_at,updated_at,last_error
               ) VALUES(?,?,?,?,?,?,?,?,?,?)
               ON CONFLICT(generation_id,embedding_space_id,backend_key) DO UPDATE SET
                   namespace_key=excluded.namespace_key,
                   status=excluded.status,
                   membership_digest=excluded.membership_digest,
                   point_count=excluded.point_count,
                   updated_at=excluded.updated_at,
                   last_error=excluded.last_error""",
            (
                generation_id,
                space_id,
                backend_key,
                namespace_key,
                status,
                membership_digest,
                point_count,
                now,
                now,
                last_error,
            ),
        )
        self.db.commit()

    def bootstrap_legacy(
        self,
        *,
        reason: str = "R2-07 legacy bootstrap",
    ) -> GenerationSwitchResult:
        space, vector_index = self._runtime()
        generation = self._generation_row(LEGACY_GENERATION_ID)
        if generation["contract_key"] != PHASE_I_CONTRACT_KEY:
            raise KnowledgeSearchGenerationError("Legacy generation contract identity is invalid")

        source_digest = self.source_catalog_digest()
        count = self._validate_generation_shape(
            LEGACY_GENERATION_ID,
            PHASE_I_CONTRACT_KEY,
        )
        membership_digest = self.membership_digest(LEGACY_GENERATION_ID)
        namespace_key, legacy_index = self._legacy_namespace(space)
        metadata = legacy_index.metadata(space)
        if metadata.points_count != count:
            raise KnowledgeSearchGenerationError(
                "Legacy Vector namespace point count does not match generation membership count"
            )
        if self._audit_namespace(
            legacy_index,
            space,
            LEGACY_GENERATION_ID,
            PHASE_I_CONTRACT_KEY,
        ) != count:
            raise KnowledgeSearchGenerationError(
                "Legacy Vector namespace identity audit count mismatch"
            )

        self._upsert_binding(
            LEGACY_GENERATION_ID,
            space_id=space.space_id,
            backend_key=vector_index.backend_key,
            namespace_key=namespace_key,
            status="ready",
            membership_digest=membership_digest,
            point_count=count,
        )
        now = self._now()
        with self.db:
            self.db.execute(
                """UPDATE knowledge_search_generations
                   SET state='ready',source_catalog_digest=?,membership_digest=?,
                       ready_at=?,retired_at=NULL,last_error=NULL
                   WHERE id=?""",
                (source_digest, membership_digest, now, LEGACY_GENERATION_ID),
            )
        active = self.db.execute(
            """SELECT active_generation_id,activation_revision
               FROM knowledge_search_active_generation
               WHERE scope='knowledge'"""
        ).fetchone()
        if active is not None:
            return GenerationSwitchResult(
                from_generation_id=active["active_generation_id"],
                to_generation_id=active["active_generation_id"],
                switch_kind="bootstrap",
                activation_revision=active["activation_revision"],
                source_catalog_digest=source_digest,
            )
        return self._switch(
            LEGACY_GENERATION_ID,
            switch_kind="bootstrap",
            reason=reason,
            require_contract=PHASE_I_CONTRACT_KEY,
        )

    def build_r2_candidate(self) -> GenerationBuildResult:
        space, vector_index = self._runtime()
        source_digest = self.source_catalog_digest()
        generation_id = f"search-generation:r2:{uuid.uuid4()}"
        created_at = self._now()
        self.db.execute(
            """INSERT INTO knowledge_search_generations(
                   id,contract_key,contract_version,state,source_catalog_digest,created_at
               ) VALUES(?,?,?,?,?,?)""",
            (
                generation_id,
                R2_CONTRACT_KEY,
                2,
                "building",
                source_digest,
                created_at,
            ),
        )
        self.db.commit()

        namespace_key = self._candidate_namespace(generation_id, space.space_id)
        try:
            for version_id in self._accepted_versions():
                self.builder.materialize_version_r2(version_id)

            now = self._now()
            self.db.execute(
                """INSERT OR IGNORE INTO knowledge_search_generation_memberships(
                       generation_id,membership_id,created_at
                   )
                   SELECT ?,m.id,?
                   FROM knowledge_search_representation_memberships m
                   JOIN object_version_lifecycle l ON l.version_id=m.version_id
                   WHERE l.state='accepted'
                     AND m.target_kind IN ('object_overview','facet','statement')
                   ORDER BY m.id""",
                (generation_id, now),
            )
            self.db.commit()

            count = self._validate_generation_shape(generation_id, R2_CONTRACT_KEY)
            membership_digest = self.membership_digest(generation_id)
            if self.source_catalog_digest() != source_digest:
                raise KnowledgeSearchGenerationError(
                    "Canonical source catalog changed during candidate membership build"
                )

            self.db.execute(
                "UPDATE knowledge_search_generations SET membership_digest=? WHERE id=?",
                (membership_digest, generation_id),
            )
            self.db.commit()

            reused, created = self._complete_embeddings(generation_id)
            bound_index = self._bound_index(namespace_key)
            self._upsert_binding(
                generation_id,
                space_id=space.space_id,
                backend_key=vector_index.backend_key,
                namespace_key=namespace_key,
                status="building",
                membership_digest=None,
                point_count=None,
            )
            metadata = KnowledgeVectorMaintenanceBuilder(
                self.repository,
                bound_index,
                generation_id=generation_id,
            ).rebuild(space)
            if metadata.points_count != count:
                raise KnowledgeSearchGenerationError(
                    "Candidate Vector namespace point count does not match generation membership count"
                )
            if self._audit_namespace(
                bound_index,
                space,
                generation_id,
                R2_CONTRACT_KEY,
            ) != count:
                raise KnowledgeSearchGenerationError(
                    "Candidate Vector namespace identity audit count mismatch"
                )

            final_digest = self.membership_digest(generation_id)
            if final_digest != membership_digest:
                raise KnowledgeSearchGenerationError(
                    "Candidate generation membership changed during Vector rebuild"
                )
            if self.source_catalog_digest() != source_digest:
                raise KnowledgeSearchGenerationError(
                    "Canonical source catalog changed during candidate Vector rebuild"
                )

            self._upsert_binding(
                generation_id,
                space_id=space.space_id,
                backend_key=vector_index.backend_key,
                namespace_key=namespace_key,
                status="ready",
                membership_digest=membership_digest,
                point_count=count,
            )
            ready_at = self._now()
            with self.db:
                self.db.execute(
                    """UPDATE knowledge_search_generations
                       SET state='ready',source_catalog_digest=?,membership_digest=?,
                           ready_at=?,last_error=NULL
                       WHERE id=?""",
                    (source_digest, membership_digest, ready_at, generation_id),
                )
            return GenerationBuildResult(
                generation_id=generation_id,
                contract_key=R2_CONTRACT_KEY,
                state="ready",
                source_catalog_digest=source_digest,
                membership_digest=membership_digest,
                membership_count=count,
                reused_embedding_count=reused,
                created_embedding_count=created,
                backend_key=vector_index.backend_key,
                namespace_key=namespace_key,
                point_count=count,
            )
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
            with self.db:
                self.db.execute(
                    """UPDATE knowledge_search_generations
                       SET state='failed',last_error=?
                       WHERE id=? AND state='building'""",
                    (error, generation_id),
                )
                self.db.execute(
                    """UPDATE knowledge_search_generation_vector_indexes
                       SET status='failed',updated_at=?,last_error=?
                       WHERE generation_id=? AND status='building'""",
                    (self._now(), error, generation_id),
                )
            if isinstance(exc, KnowledgeSearchGenerationError):
                raise
            raise KnowledgeSearchGenerationError(
                f"R2 candidate generation build failed: {error}"
            ) from exc

    def _verify_switch_target(
        self,
        generation_id: str,
        *,
        require_contract: str | None = None,
    ) -> tuple[dict, str, int]:
        space, vector_index = self._runtime()
        generation = self._generation_row(generation_id)
        if generation["state"] != "ready":
            raise KnowledgeSearchGenerationError("Switch target generation is not ready")
        if require_contract is not None and generation["contract_key"] != require_contract:
            raise KnowledgeSearchGenerationError("Switch target has the wrong generation contract")
        source_digest = self.source_catalog_digest()
        if generation["source_catalog_digest"] != source_digest:
            raise KnowledgeSearchGenerationError("Switch target source catalog digest is stale")
        count = self._validate_generation_shape(generation_id, generation["contract_key"])
        membership_digest = self.membership_digest(generation_id)
        if generation["membership_digest"] != membership_digest:
            raise KnowledgeSearchGenerationError(
                "Switch target membership digest does not match persisted memberships"
            )
        binding = self.db.execute(
            """SELECT * FROM knowledge_search_generation_vector_indexes
               WHERE generation_id=? AND embedding_space_id=? AND backend_key=?""",
            (generation_id, space.space_id, vector_index.backend_key),
        ).fetchone()
        if binding is None or binding["status"] != "ready":
            raise KnowledgeSearchGenerationError("Switch target Vector namespace is not ready")
        if binding["membership_digest"] != membership_digest:
            raise KnowledgeSearchGenerationError(
                "Switch target Vector binding digest does not match generation"
            )
        if int(binding["point_count"]) != count:
            raise KnowledgeSearchGenerationError(
                "Switch target Vector point count does not match generation membership count"
            )
        bound_index = self._bound_index(binding["namespace_key"])
        metadata = bound_index.metadata(space)
        if metadata.points_count != count:
            raise KnowledgeSearchGenerationError(
                "Switch target live Vector namespace point count is inconsistent"
            )
        if self._audit_namespace(
            bound_index,
            space,
            generation_id,
            generation["contract_key"],
        ) != count:
            raise KnowledgeSearchGenerationError(
                "Switch target Vector namespace identity audit count mismatch"
            )
        return generation, source_digest, count

    def _switch(
        self,
        generation_id: str,
        *,
        switch_kind: str,
        reason: str,
        require_contract: str | None = None,
    ) -> GenerationSwitchResult:
        _, source_digest, _ = self._verify_switch_target(
            generation_id,
            require_contract=require_contract,
        )
        now = self._now()
        switch_id = f"search-generation-switch:{uuid.uuid4()}"
        with self.db:
            current = self.db.execute(
                """SELECT active_generation_id,activation_revision
                   FROM knowledge_search_active_generation
                   WHERE scope='knowledge'"""
            ).fetchone()
            from_generation_id = current["active_generation_id"] if current else None
            revision = int(current["activation_revision"]) + 1 if current else 1
            if current is None:
                self.db.execute(
                    """INSERT INTO knowledge_search_active_generation(
                           scope,active_generation_id,activation_revision,activated_at
                       ) VALUES('knowledge',?,?,?)""",
                    (generation_id, revision, now),
                )
            else:
                self.db.execute(
                    """UPDATE knowledge_search_active_generation
                       SET active_generation_id=?,activation_revision=?,activated_at=?
                       WHERE scope='knowledge'""",
                    (generation_id, revision, now),
                )
            self.db.execute(
                """INSERT INTO knowledge_search_generation_switches(
                       id,from_generation_id,to_generation_id,switch_kind,reason,
                       source_catalog_digest,switched_at
                   ) VALUES(?,?,?,?,?,?,?)""",
                (
                    switch_id,
                    from_generation_id,
                    generation_id,
                    switch_kind,
                    reason,
                    source_digest,
                    now,
                ),
            )
        return GenerationSwitchResult(
            from_generation_id=from_generation_id,
            to_generation_id=generation_id,
            switch_kind=switch_kind,
            activation_revision=revision,
            source_catalog_digest=source_digest,
        )

    def _smoke_active_generation(self) -> None:
        space, vector_index = self._runtime()
        routed = route_generation_vector_index(self.repository, vector_index)
        source = self.db.execute(
            """SELECT o.id,o.name
               FROM objects o
               WHERE o.status='active' AND o.current_version_id IS NOT NULL
               ORDER BY o.id LIMIT 1"""
        ).fetchone()
        if source is None:
            return
        HybridObjectSearch(
            self.repository,
            embedding_provider=self.embedding_provider,
            vector_index=routed,
        ).search(source["name"], mode="semantic", limit=1)
        ObjectSimilaritySearch(
            self.repository,
            space=space,
            vector_index=routed,
        ).find_similar_objects(source["id"], limit=1)
        facet = self.db.execute(
            """SELECT f.key
               FROM knowledge_search_active_generation a
               JOIN knowledge_search_generation_memberships gm
                 ON gm.generation_id=a.active_generation_id
               JOIN knowledge_search_representation_memberships m ON m.id=gm.membership_id
               JOIN facet_definitions f ON f.id=m.facet_id
               WHERE a.scope='knowledge' AND m.object_id=? AND m.version_id=(
                   SELECT current_version_id FROM objects WHERE id=?
               ) AND m.target_kind='facet'
               ORDER BY f.key LIMIT 1""",
            (source["id"], source["id"]),
        ).fetchone()
        if facet is not None:
            ObjectSimilaritySearch(
                self.repository,
                space=space,
                vector_index=routed,
            ).find_similar_objects(source["id"], facet=facet["key"], limit=1)

    def cutover(
        self,
        generation_id: str,
        *,
        reason: str = "R2-07 cutover",
        smoke: bool = True,
    ) -> GenerationSwitchResult:
        previous = self.db.execute(
            """SELECT active_generation_id
               FROM knowledge_search_active_generation WHERE scope='knowledge'"""
        ).fetchone()
        if previous is None:
            raise KnowledgeSearchGenerationError(
                "Legacy generation must be bootstrapped before R2 cutover"
            )
        result = self._switch(
            generation_id,
            switch_kind="cutover",
            reason=reason,
            require_contract=R2_CONTRACT_KEY,
        )
        if smoke:
            try:
                self._smoke_active_generation()
            except Exception as exc:
                self._switch(
                    previous["active_generation_id"],
                    switch_kind="recovery",
                    reason=(
                        "Automatic recovery after cutover smoke failure: "
                        f"{type(exc).__name__}: {exc}"
                    ),
                )
                raise KnowledgeSearchGenerationError(
                    f"Cutover smoke failed and previous generation was restored: {exc}"
                ) from exc
        return result

    def rollback(
        self,
        generation_id: str = LEGACY_GENERATION_ID,
        *,
        reason: str = "R2-07 rollback rehearsal",
        smoke: bool = True,
    ) -> GenerationSwitchResult:
        current = self.db.execute(
            """SELECT active_generation_id
               FROM knowledge_search_active_generation WHERE scope='knowledge'"""
        ).fetchone()
        if current is None:
            raise KnowledgeSearchGenerationError("No active generation exists to roll back")
        if current["active_generation_id"] == generation_id:
            raise KnowledgeSearchGenerationError("Rollback target is already active")
        result = self._switch(
            generation_id,
            switch_kind="rollback",
            reason=reason,
            require_contract=PHASE_I_CONTRACT_KEY,
        )
        if smoke:
            try:
                self._smoke_active_generation()
            except Exception as exc:
                self._switch(
                    current["active_generation_id"],
                    switch_kind="recovery",
                    reason=(
                        "Automatic recovery after rollback smoke failure: "
                        f"{type(exc).__name__}: {exc}"
                    ),
                )
                raise KnowledgeSearchGenerationError(
                    f"Rollback smoke failed and previous generation was restored: {exc}"
                ) from exc
        return result

    def recover_interrupted_builds(
        self,
        *,
        reason: str = "R2-07 interrupted build recovery",
    ) -> int:
        active = self.db.execute(
            """SELECT active_generation_id
               FROM knowledge_search_active_generation WHERE scope='knowledge'"""
        ).fetchone()
        active_id = active["active_generation_id"] if active else None
        rows = self.db.execute(
            """SELECT id FROM knowledge_search_generations
               WHERE state='building' ORDER BY created_at,id"""
        ).fetchall()
        ids = [row["id"] for row in rows if row["id"] != active_id]
        if not ids:
            return 0
        now = self._now()
        with self.db:
            for generation_id in ids:
                self.db.execute(
                    """UPDATE knowledge_search_generations
                       SET state='failed',last_error=? WHERE id=? AND state='building'""",
                    (reason, generation_id),
                )
                self.db.execute(
                    """UPDATE knowledge_search_generation_vector_indexes
                       SET status='failed',updated_at=?,last_error=?
                       WHERE generation_id=? AND status='building'""",
                    (now, reason, generation_id),
                )
        return len(ids)

    def status(self) -> dict:
        active = self.db.execute(
            "SELECT * FROM knowledge_search_active_generation WHERE scope='knowledge'"
        ).fetchone()
        generations = [
            dict(row)
            for row in self.db.execute(
                "SELECT * FROM knowledge_search_generations ORDER BY created_at,id"
            ).fetchall()
        ]
        bindings = [
            dict(row)
            for row in self.db.execute(
                """SELECT * FROM knowledge_search_generation_vector_indexes
                   ORDER BY generation_id,embedding_space_id,backend_key"""
            ).fetchall()
        ]
        switches = [
            dict(row)
            for row in self.db.execute(
                "SELECT * FROM knowledge_search_generation_switches ORDER BY switched_at,id"
            ).fetchall()
        ]
        return {
            "active_generation": dict(active) if active else None,
            "generations": generations,
            "vector_bindings": bindings,
            "switches": switches,
        }
