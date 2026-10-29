"""Transport-neutral Runtime health/status Application boundary for Phase P."""

from __future__ import annotations

import importlib.util
from collections import Counter
from dataclasses import asdict, dataclass
from importlib import metadata
from pathlib import Path
from typing import Any

import httpx

from .application_generation import KnowledgeSearchGenerationApplication
from .operation_contracts import CATEGORY_INTEGRITY, CATEGORY_RUNTIME
from .retrieval.embedding import (
    DEFAULT_EMBEDDING_MODEL,
    DEFAULT_EMBEDDING_REVISION,
)

RUNTIME_HEALTH_SCHEMA = "sgokb.runtime-health/1.0"
STATUS_HEALTHY = "healthy"
STATUS_DEGRADED = "degraded"
STATUS_UNAVAILABLE = "unavailable"
STATUS_NOT_CONFIGURED = "not_configured"


@dataclass(frozen=True, slots=True)
class RuntimeHealthIssue:
    category: str
    code: str
    message: str


@dataclass(frozen=True, slots=True)
class RuntimeComponentHealth:
    status: str
    details: dict[str, Any]
    issue: RuntimeHealthIssue | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "status": self.status,
            "details": self.details,
            "issue": asdict(self.issue) if self.issue is not None else None,
        }
        return payload


@dataclass(frozen=True, slots=True)
class RuntimeHealthSnapshot:
    overall_status: str
    sqlite: RuntimeComponentHealth
    embedding: RuntimeComponentHealth
    qdrant: RuntimeComponentHealth
    generation: RuntimeComponentHealth
    derived: RuntimeComponentHealth

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": RUNTIME_HEALTH_SCHEMA,
            "overall_status": self.overall_status,
            "lifecycle": {
                "qdrant_owner": "external",
                "observe": True,
                "start": False,
                "stop": False,
                "restart": False,
            },
            "components": {
                "sqlite": self.sqlite.to_dict(),
                "embedding": self.embedding.to_dict(),
                "qdrant": self.qdrant.to_dict(),
                "generation": self.generation.to_dict(),
                "derived": self.derived.to_dict(),
            },
        }


class RuntimeHealthApplication:
    """Read-only health projection shared by CLI and GUI transports.

    The probe never invokes Docker or owns the Qdrant lifecycle. The default
    embedding probe is deliberately shallow: it reports dependency/configuration
    readiness without loading or downloading the configured model.
    """

    def __init__(
        self,
        repository,
        db_path: str | Path,
        runtime_factory,
        *,
        http_timeout_seconds: float = 2.0,
    ) -> None:
        self._repository = repository
        self._db_path = Path(db_path)
        self._runtime_factory = runtime_factory
        self._http_timeout_seconds = http_timeout_seconds

    @staticmethod
    def _issue(category: str, code: str, message: str) -> RuntimeHealthIssue:
        return RuntimeHealthIssue(category=category, code=code, message=message)

    def _sqlite(self) -> RuntimeComponentHealth:
        details: dict[str, Any] = {"path": str(self._db_path)}
        try:
            row = self._repository.db.execute("SELECT 1 AS ok").fetchone()
            details["query_ok"] = bool(row and row["ok"] == 1)
            details["foreign_keys"] = bool(
                self._repository.db.execute("PRAGMA foreign_keys").fetchone()[0]
            )
            details["journal_mode"] = str(
                self._repository.db.execute("PRAGMA journal_mode").fetchone()[0]
            )
        except Exception as exc:
            return RuntimeComponentHealth(
                STATUS_UNAVAILABLE,
                details,
                self._issue(
                    CATEGORY_INTEGRITY,
                    "sqlite_health_unavailable",
                    f"SQLite health probe failed: {type(exc).__name__}: {exc}",
                ),
            )
        if not details["query_ok"] or not details["foreign_keys"]:
            return RuntimeComponentHealth(
                STATUS_DEGRADED,
                details,
                self._issue(
                    CATEGORY_INTEGRITY,
                    "sqlite_runtime_degraded",
                    "SQLite is open but the runtime connection contract is not fully active",
                ),
            )
        return RuntimeComponentHealth(STATUS_HEALTHY, details)

    def _embedding(self) -> RuntimeComponentHealth:
        config = self._runtime_factory.config
        details: dict[str, Any] = {
            "provider_key": "sentence-transformers",
            "model": DEFAULT_EMBEDDING_MODEL,
            "model_revision": DEFAULT_EMBEDDING_REVISION,
            "cache_folder": config.model_cache,
            "local_files_only": config.model_local_only,
            "probe_mode": "shallow",
            "loaded": False,
        }
        cached = self._runtime_factory.cached_semantic_runtime()
        if cached is not None:
            provider = cached[0]
            space = getattr(provider, "space", None)
            details["loaded"] = True
            if space is not None:
                details.update(
                    {
                        "provider_key": space.provider_key,
                        "provider_version": space.provider_version,
                        "model": space.model,
                        "model_revision": space.model_revision,
                        "space_id": space.space_id,
                        "dimension": space.dimension,
                    }
                )
            details["device"] = str(getattr(provider, "device", "unknown"))
            return RuntimeComponentHealth(STATUS_HEALTHY, details)

        preload_failure = self._runtime_factory.semantic_preload_failure()
        if preload_failure:
            return RuntimeComponentHealth(
                STATUS_UNAVAILABLE,
                details,
                self._issue(
                    CATEGORY_RUNTIME,
                    "embedding_dependency_unavailable",
                    preload_failure,
                ),
            )

        missing = [
            package
            for package in ("torch", "sentence_transformers")
            if importlib.util.find_spec(package) is None
        ]
        if missing:
            details["missing_dependencies"] = missing
            return RuntimeComponentHealth(
                STATUS_UNAVAILABLE,
                details,
                self._issue(
                    CATEGORY_RUNTIME,
                    "embedding_dependency_unavailable",
                    "Local embedding dependencies are not installed: " + ", ".join(missing),
                ),
            )
        try:
            details["provider_version"] = metadata.version("sentence-transformers")
            details["torch_version"] = metadata.version("torch")
        except metadata.PackageNotFoundError as exc:
            return RuntimeComponentHealth(
                STATUS_UNAVAILABLE,
                details,
                self._issue(
                    CATEGORY_RUNTIME,
                    "embedding_dependency_unavailable",
                    f"Local embedding package metadata is unavailable: {exc}",
                ),
            )
        details["readiness"] = "configured_not_loaded"
        return RuntimeComponentHealth(STATUS_HEALTHY, details)

    def _generation(self) -> RuntimeComponentHealth:
        app = KnowledgeSearchGenerationApplication(self._repository)
        state = app.status()
        active_pointer = state["active_generation"]
        current_object_count = int(
            self._repository.db.execute(
                "SELECT count(*) FROM objects WHERE current_version_id IS NOT NULL"
            ).fetchone()[0]
        )
        details: dict[str, Any] = {
            "active_generation_id": None,
            "current_object_count": current_object_count,
            "source_catalog_current": None,
            "generation": None,
            "vector_bindings": [],
        }
        if active_pointer is None:
            if current_object_count == 0:
                return RuntimeComponentHealth(STATUS_NOT_CONFIGURED, details)
            return RuntimeComponentHealth(
                STATUS_DEGRADED,
                details,
                self._issue(
                    CATEGORY_RUNTIME,
                    "generation_not_active",
                    "Knowledge exists but no active Search generation is selected",
                ),
            )

        generation_id = active_pointer["active_generation_id"]
        generation = next(
            (item for item in state["generations"] if item["id"] == generation_id),
            None,
        )
        bindings = [
            item for item in state["vector_bindings"] if item["generation_id"] == generation_id
        ]
        details.update(
            {
                "active_generation_id": generation_id,
                "activation_revision": active_pointer.get("activation_revision"),
                "generation": generation,
                "vector_bindings": bindings,
            }
        )
        if generation is None:
            return RuntimeComponentHealth(
                STATUS_DEGRADED,
                details,
                self._issue(
                    CATEGORY_INTEGRITY,
                    "active_generation_missing",
                    "The active generation pointer references a missing generation",
                ),
            )
        current_digest = app.source_catalog_digest()
        source_current = generation.get("source_catalog_digest") == current_digest
        details["source_catalog_current"] = source_current
        details["current_source_catalog_digest"] = current_digest
        bindings_ready = bool(bindings) and all(item.get("status") == "ready" for item in bindings)
        if generation.get("state") != "ready" or not source_current or not bindings_ready:
            return RuntimeComponentHealth(
                STATUS_DEGRADED,
                details,
                self._issue(
                    CATEGORY_INTEGRITY,
                    "generation_runtime_degraded",
                    "Active Search generation or its Vector binding is not current and ready",
                ),
            )
        return RuntimeComponentHealth(STATUS_HEALTHY, details)

    def _derived(self) -> RuntimeComponentHealth:
        rows = self._repository.rows(
            "SELECT id FROM objects WHERE current_version_id IS NOT NULL ORDER BY id"
        )
        status_counts: Counter[str] = Counter()
        kind_counts: dict[str, Counter[str]] = {}
        missing_state_objects: list[str] = []
        for row in rows:
            states = self._repository.version_store.derived_states(row["id"])
            if not states:
                missing_state_objects.append(row["id"])
            for state in states:
                status = state.status.value
                status_counts[status] += 1
                kind_counts.setdefault(state.kind, Counter())[status] += 1
        unhealthy = sum(
            count for status, count in status_counts.items() if status != "ready"
        ) + len(missing_state_objects)
        details: dict[str, Any] = {
            "current_object_count": len(rows),
            "status_counts": dict(sorted(status_counts.items())),
            "kind_counts": {
                kind: dict(sorted(counts.items())) for kind, counts in sorted(kind_counts.items())
            },
            "missing_state_objects": missing_state_objects,
            "unhealthy_count": unhealthy,
        }
        if unhealthy:
            return RuntimeComponentHealth(
                STATUS_DEGRADED,
                details,
                self._issue(
                    CATEGORY_RUNTIME,
                    "derived_state_incomplete",
                    (
                        "One or more current Objects have pending, stale, failed, "
                        "or missing derived state"
                    ),
                ),
            )
        return RuntimeComponentHealth(STATUS_HEALTHY, details)

    def _qdrant(self, generation: RuntimeComponentHealth) -> RuntimeComponentHealth:
        config = self._runtime_factory.config
        endpoint = config.qdrant_url.rstrip("/")
        expected_collections = sorted(
            {
                item["namespace_key"]
                for item in generation.details.get("vector_bindings", [])
                if item.get("backend_key") == "qdrant" and item.get("namespace_key")
            }
        )
        details: dict[str, Any] = {
            "endpoint": endpoint,
            "grpc_port": config.qdrant_grpc_port,
            "prefer_grpc": config.qdrant_prefer_grpc,
            "collection_prefix": config.qdrant_collection_prefix,
            "ready": False,
            "version": None,
            "expected_collections": expected_collections,
            "available_collections": [],
            "missing_collections": [],
        }
        try:
            with httpx.Client(timeout=self._http_timeout_seconds) as client:
                ready = client.get(endpoint + "/readyz")
                if ready.status_code != 200:
                    return RuntimeComponentHealth(
                        STATUS_UNAVAILABLE,
                        details,
                        self._issue(
                            CATEGORY_RUNTIME,
                            "qdrant_readiness_failed",
                            f"Qdrant /readyz returned HTTP {ready.status_code}",
                        ),
                    )
                details["ready"] = True
                root = client.get(endpoint + "/")
                root.raise_for_status()
                root_payload = root.json()
                if not isinstance(root_payload, dict):
                    raise ValueError("Qdrant root response must be an object")
                details["version"] = root_payload.get("version")
                collections = client.get(endpoint + "/collections")
                collections.raise_for_status()
                collection_payload = collections.json()
                if not isinstance(collection_payload, dict):
                    raise ValueError("Qdrant collections response must be an object")
        except (httpx.HTTPError, ValueError, KeyError, TypeError) as exc:
            return RuntimeComponentHealth(
                STATUS_UNAVAILABLE,
                details,
                self._issue(
                    CATEGORY_RUNTIME,
                    "qdrant_endpoint_unavailable",
                    f"Qdrant endpoint probe failed: {type(exc).__name__}: {exc}",
                ),
            )

        names = sorted(
            str(item["name"])
            for item in collection_payload.get("result", {}).get("collections", [])
            if isinstance(item, dict) and item.get("name")
        )
        details["available_collections"] = names
        missing = [name for name in expected_collections if name not in names]
        details["missing_collections"] = missing
        details["matching_prefix_collections"] = [
            name for name in names if name.startswith(config.qdrant_collection_prefix)
        ]
        if missing:
            return RuntimeComponentHealth(
                STATUS_DEGRADED,
                details,
                self._issue(
                    CATEGORY_RUNTIME,
                    "qdrant_collection_unavailable",
                    "Active Search generation references a missing Qdrant collection",
                ),
            )
        return RuntimeComponentHealth(STATUS_HEALTHY, details)

    @staticmethod
    def _overall(components: tuple[RuntimeComponentHealth, ...]) -> str:
        if components[0].status == STATUS_UNAVAILABLE:
            return STATUS_UNAVAILABLE
        if any(item.status in {STATUS_DEGRADED, STATUS_UNAVAILABLE} for item in components[1:]):
            return STATUS_DEGRADED
        return STATUS_HEALTHY

    def status(self) -> dict[str, Any]:
        sqlite = self._sqlite()
        embedding = self._embedding()
        generation = self._generation()
        derived = self._derived()
        qdrant = self._qdrant(generation)
        components = (sqlite, embedding, qdrant, generation, derived)
        return RuntimeHealthSnapshot(
            overall_status=self._overall(components),
            sqlite=sqlite,
            embedding=embedding,
            qdrant=qdrant,
            generation=generation,
            derived=derived,
        ).to_dict()
