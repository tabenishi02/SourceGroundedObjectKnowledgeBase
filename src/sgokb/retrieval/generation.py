"""Generation-aware Search Representation and Vector routing for N05D-04R2."""

from __future__ import annotations

from contextlib import contextmanager, nullcontext
from contextvars import ContextVar
from dataclasses import dataclass

from sgokb.domain import VectorSearchFilter

from .search_representation import SearchRepresentationBuilder
from .vector_index import QdrantVectorIndexAdapter

_PHASE_I_CONTRACT_KEY = "phase-i-search-v1"
_R2_CONTRACT_KEY = "n05d04r2-hierarchical-v2"
_UNRESOLVED = object()


class GenerationAwareSearchRepresentationBuilder(SearchRepresentationBuilder):
    """Materialize the family required by the currently active generation.

    Before R2-07 bootstrap there is no active pointer, so the historical Phase-I
    v1 family remains the compatibility behavior. Once a generation is active,
    newly materialized memberships are linked only to that generation's contract.
    """

    def _active_generation(self) -> dict | None:
        row = self.db.execute(
            """SELECT a.active_generation_id,g.contract_key,g.contract_version,g.state
               FROM knowledge_search_active_generation a
               JOIN knowledge_search_generations g ON g.id=a.active_generation_id
               WHERE a.scope='knowledge'"""
        ).fetchone()
        return dict(row) if row else None

    def _link_version(
        self,
        version_id: str,
        generation_id: str,
        kinds: tuple[str, ...],
    ) -> None:
        marks = ",".join("?" for _ in kinds)
        rows = self.db.execute(
            f"""SELECT id
                FROM knowledge_search_representation_memberships
                WHERE version_id=? AND target_kind IN ({marks})
                ORDER BY id""",
            (version_id, *kinds),
        ).fetchall()
        now = self.db.execute("SELECT strftime('%Y-%m-%dT%H:%M:%fZ','now') AS value").fetchone()[
            "value"
        ]
        self.db.executemany(
            """INSERT OR IGNORE INTO knowledge_search_generation_memberships(
                   generation_id,membership_id,created_at
               ) VALUES(?,?,?)""",
            [(generation_id, row["id"], now) for row in rows],
        )
        self.db.commit()

    def materialize_version(self, version_id: str) -> tuple[str, ...]:
        generation = self._active_generation()
        if generation is None:
            return super().materialize_version(version_id)
        if (generation["contract_key"], generation["contract_version"]) not in {
            (_PHASE_I_CONTRACT_KEY, 1),
            (_R2_CONTRACT_KEY, 2),
        }:
            raise RuntimeError("Unsupported active Knowledge Search generation contract/version")
        if generation["state"] != "ready":
            raise RuntimeError("Active Knowledge Search generation is not ready")
        if generation["contract_key"] == _R2_CONTRACT_KEY:
            stored = super().materialize_version_r2(version_id)
            self._link_version(
                version_id,
                generation["active_generation_id"],
                ("object_overview", "facet", "statement"),
            )
            return stored
        if generation["contract_key"] == _PHASE_I_CONTRACT_KEY:
            stored = super().materialize_version(version_id)
            self._link_version(
                version_id,
                generation["active_generation_id"],
                ("object_overall", "facet", "statement"),
            )
            return stored
        raise RuntimeError(
            "Unsupported active Knowledge Search generation contract: "
            f"{generation['contract_key']} v{generation['contract_version']}"
        )


class GenerationQdrantVectorIndexAdapter(QdrantVectorIndexAdapter):
    """Bind one Qdrant adapter instance to an exact persisted namespace key."""

    def __init__(self, *, namespace_key: str, base: QdrantVectorIndexAdapter) -> None:
        if not namespace_key.strip():
            raise ValueError("Vector namespace key must be non-empty")
        filter_schema = dict(base.filter_schema)
        filter_schema["generation_id"] = "keyword"
        self.namespace_key = namespace_key
        super().__init__(
            collection_prefix=base.collection_prefix,
            hnsw_m=base.hnsw_m,
            ef_construct=base.ef_construct,
            search_ef=base.search_ef,
            full_scan_threshold=base.full_scan_threshold,
            indexing_threshold=base.indexing_threshold,
            filter_schema=filter_schema,
            client=base._client,
            wait_for_index=base.wait_for_index,
            index_wait_timeout_seconds=base.index_wait_timeout_seconds,
        )

    def _collection(self, space) -> str:
        return self.namespace_key

    def audit_memberships(
        self,
        space,
        expected_membership_ids,
        *,
        generation_id: str | None,
        require_generation_payload: bool,
    ) -> int:
        """Scan one exact namespace and verify point identity/payload integrity."""

        name = self._collection(space)
        if not self._client.collection_exists(name):
            raise RuntimeError("Vector namespace is unavailable")
        expected = set(expected_membership_ids)
        seen: set[str] = set()
        offset = None
        while True:
            records, offset = self._client.scroll(
                name,
                limit=256,
                offset=offset,
                with_payload=True,
                with_vectors=False,
            )
            for record in records:
                payload = dict(record.payload or {})
                if payload.get("__sgokb_space_id") != space.space_id:
                    raise RuntimeError("Vector namespace contains a point from another space")
                membership_id = payload.get("__sgokb_point_id")
                if not membership_id:
                    raise RuntimeError(
                        "Vector namespace contains a point without membership identity"
                    )
                membership_id = str(membership_id)
                if str(record.id) != self._backend_id(space, membership_id):
                    raise RuntimeError("Vector backend point ID differs from membership identity")
                if membership_id in seen:
                    raise RuntimeError("Vector namespace contains duplicate membership identity")
                seen.add(membership_id)
                payload_generation = payload.get("generation_id")
                if require_generation_payload and payload_generation != generation_id:
                    raise RuntimeError("Vector namespace generation payload mismatch")
                if (
                    payload_generation is not None
                    and generation_id is not None
                    and payload_generation != generation_id
                ):
                    raise RuntimeError("Vector namespace generation payload mismatch")
            if offset is None:
                break
        if seen != expected:
            raise RuntimeError(
                "Vector namespace membership identity differs from generation membership set"
            )
        return len(seen)


@dataclass(frozen=True, slots=True)
class _VectorBinding:
    generation_id: str
    contract_key: str
    namespace_key: str


class GenerationRoutingVectorIndexAdapter:
    """Route normal Knowledge Vector operations through persisted generation bindings."""

    def __init__(self, repository, base_vector_index) -> None:
        self.repository = repository
        self.db = repository.db
        self.base_vector_index = base_vector_index
        self.backend_key = base_vector_index.backend_key
        self._operation_generation = ContextVar("vector_operation_generation", default=_UNRESOLVED)

    def _active_generation_id(self) -> str | None:
        row = self.db.execute(
            """SELECT active_generation_id
               FROM knowledge_search_active_generation
               WHERE scope='knowledge'"""
        ).fetchone()
        return row["active_generation_id"] if row else None

    @staticmethod
    def _filter_generation_id(filters: VectorSearchFilter | None) -> str | None:
        if filters is None:
            return None
        values = {
            str(value)
            for match in filters.matches
            if match.field == "generation_id"
            for value in match.values
        }
        if not values:
            return None
        if len(values) != 1:
            raise RuntimeError("Vector search contains an ambiguous generation route")
        return next(iter(values))

    def _binding(self, generation_id: str, space_id: str) -> _VectorBinding:
        row = self.db.execute(
            """SELECT v.generation_id,g.contract_key,v.namespace_key,v.status
               FROM knowledge_search_generation_vector_indexes v
               JOIN knowledge_search_generations g ON g.id=v.generation_id
               WHERE v.generation_id=? AND v.embedding_space_id=? AND v.backend_key=?""",
            (generation_id, space_id, self.backend_key),
        ).fetchone()
        if row is None:
            raise RuntimeError("Active Knowledge Search generation has no Vector namespace binding")
        if row["status"] != "ready":
            raise RuntimeError("Active Knowledge Search Vector namespace is not ready")
        return _VectorBinding(
            generation_id=row["generation_id"],
            contract_key=row["contract_key"],
            namespace_key=row["namespace_key"],
        )

    def bind_namespace(self, namespace_key: str):
        if isinstance(self.base_vector_index, QdrantVectorIndexAdapter):
            return GenerationQdrantVectorIndexAdapter(
                namespace_key=namespace_key,
                base=self.base_vector_index,
            )
        binder = getattr(self.base_vector_index, "bind_namespace", None)
        if binder is None:
            raise RuntimeError(
                "Configured Vector backend cannot create an isolated generation namespace"
            )
        return binder(namespace_key)

    def legacy_namespace_key(self, space) -> str:
        if isinstance(self.base_vector_index, QdrantVectorIndexAdapter):
            return self.base_vector_index._collection(space)
        getter = getattr(self.base_vector_index, "namespace_key", None)
        if getter is None:
            raise RuntimeError(
                "Configured Vector backend does not expose its legacy namespace identity"
            )
        value = getter(space)
        if not value:
            raise RuntimeError("Configured Vector backend returned an empty namespace identity")
        return str(value)

    @staticmethod
    def _without_generation_filter(
        filters: VectorSearchFilter | None,
    ) -> VectorSearchFilter | None:
        if filters is None:
            return None
        return VectorSearchFilter(
            matches=tuple(match for match in filters.matches if match.field != "generation_id"),
            excludes=filters.excludes,
            ranges=filters.ranges,
        )

    def _adapter_for(self, space, generation_id: str | None):
        if generation_id is None:
            return self.base_vector_index, None
        binding = self._binding(generation_id, space.space_id)
        return self.bind_namespace(binding.namespace_key), binding

    @contextmanager
    def generation_scope(self, generation_id):
        token = self._operation_generation.set(generation_id)
        try:
            yield
        finally:
            self._operation_generation.reset(token)

    def _operation_generation_id(self):
        pinned = self._operation_generation.get()
        return self._active_generation_id() if pinned is _UNRESOLVED else pinned

    def search(self, space, query_vector, *, limit: int, filters=None):
        explicit = self._filter_generation_id(filters)
        pinned = self._operation_generation.get()
        if pinned is not _UNRESOLVED and explicit is not None and explicit != pinned:
            raise RuntimeError("Vector route differs from operation generation")
        generation_id = explicit if explicit is not None else self._operation_generation_id()
        adapter, binding = self._adapter_for(space, generation_id)
        delegated_filters = filters
        if binding is not None and binding.contract_key == _PHASE_I_CONTRACT_KEY:
            delegated_filters = self._without_generation_filter(filters)
        return adapter.search(
            space,
            query_vector,
            limit=limit,
            filters=delegated_filters,
        )

    def _active_adapter(self, space):
        return self._adapter_for(space, self._operation_generation_id())[0]

    def upsert(self, space, points):
        return self._active_adapter(space).upsert(space, points)

    def delete(self, space, point_ids):
        return self._active_adapter(space).delete(space, point_ids)

    def rebuild(self, space, points):
        return self._active_adapter(space).rebuild(space, points)

    def metadata(self, space):
        return self._active_adapter(space).metadata(space)

    def drop(self, space):
        return self._active_adapter(space).drop(space)


def route_generation_vector_index(repository, vector_index):
    """Wrap Qdrant / namespace-capable backends exactly once."""

    if vector_index is None or isinstance(
        vector_index,
        GenerationRoutingVectorIndexAdapter,
    ):
        return vector_index
    if isinstance(vector_index, QdrantVectorIndexAdapter) or hasattr(
        vector_index,
        "bind_namespace",
    ):
        return GenerationRoutingVectorIndexAdapter(repository, vector_index)
    return vector_index


def vector_generation_scope(vector_index, generation_id):
    """Pin namespace routing for one retrieval/maintenance operation, including v1."""
    scope = getattr(vector_index, "generation_scope", None)
    return scope(generation_id) if scope is not None else nullcontext()
