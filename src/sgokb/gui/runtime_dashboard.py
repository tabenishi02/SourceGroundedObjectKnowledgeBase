"""Pure presentation model for the P-RUNTIME-05 GUI Runtime Dashboard."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

RUNTIME_HEALTH_SCHEMA = "sgokb.runtime-health/1.0"
_COMPONENT_ORDER = ("sqlite", "embedding", "qdrant", "generation", "derived")
_COMPONENT_LABELS = {
    "sqlite": "SQLite",
    "embedding": "Embedding",
    "qdrant": "Qdrant",
    "generation": "Search generation",
    "derived": "Derived state",
}
_TROUBLESHOOTING = {
    "sqlite": "Run the integrity check and verify the selected Workspace database.",
    "embedding": (
        "Check the local embedding dependencies/model cache and the Search "
        "semantic-runtime setting."
    ),
    "qdrant": (
        "Check the externally owned Qdrant process and /readyz. SGOKB does not "
        "start, stop, or restart Qdrant."
    ),
    "generation": (
        "Use System > Advanced Generation to inspect, build, cut over, or repair "
        "Search generation state."
    ),
    "derived": (
        "Use System > Derived and Vector Index to inspect or rebuild replaceable "
        "derived state."
    ),
}


@dataclass(frozen=True, slots=True)
class RuntimeComponentPresentation:
    key: str
    label: str
    status: str
    summary: str
    issue: str | None
    troubleshooting: str | None


@dataclass(frozen=True, slots=True)
class SemanticSearchReadiness:
    status: str
    message: str
    blockers: tuple[str, ...]
    warnings: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class RuntimeDashboardPresentation:
    overall_status: str
    readiness: SemanticSearchReadiness
    components: tuple[RuntimeComponentPresentation, ...]
    lifecycle_note: str
    mcp_note: str


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _issue_message(component: Mapping[str, Any]) -> str | None:
    issue = _mapping(component.get("issue"))
    message = issue.get("message")
    return str(message) if message else None


def _issue_code(component: Mapping[str, Any]) -> str | None:
    issue = _mapping(component.get("issue"))
    code = issue.get("code")
    return str(code) if code else None


def _component_summary(key: str, component: Mapping[str, Any]) -> str:
    details = _mapping(component.get("details"))
    if key == "sqlite":
        path = details.get("path", "unknown")
        journal = details.get("journal_mode", "unknown")
        return f"{path} · journal={journal}"
    if key == "embedding":
        model = details.get("model", "unknown")
        readiness = details.get("readiness") or (
            "loaded" if details.get("loaded") else "configured"
        )
        return f"{model} · {readiness}"
    if key == "qdrant":
        endpoint = details.get("endpoint", "unknown")
        version = details.get("version") or "unknown"
        ready = "ready" if details.get("ready") is True else "not ready"
        missing = details.get("missing_collections") or []
        suffix = f" · missing collections={len(missing)}" if missing else ""
        return f"{endpoint} · {ready} · v{version}{suffix}"
    if key == "generation":
        active = details.get("active_generation_id") or "none (legacy routing)"
        current = details.get("source_catalog_current")
        suffix = "" if current is None else f" · source current={str(bool(current)).lower()}"
        return f"active={active}{suffix}"
    if key == "derived":
        unhealthy = int(details.get("unhealthy_count") or 0)
        current = int(details.get("current_object_count") or 0)
        return f"current objects={current} · unhealthy states={unhealthy}"
    return "No presentation details available."


def _semantic_derived_warning(component: Mapping[str, Any]) -> str | None:
    details = _mapping(component.get("details"))
    kind_counts = _mapping(details.get("kind_counts"))
    affected: list[str] = []
    for kind in ("search_representation", "embedding", "vector_index"):
        counts = _mapping(kind_counts.get(kind))
        non_ready = sum(int(count or 0) for status, count in counts.items() if status != "ready")
        if non_ready:
            affected.append(f"{kind}={non_ready}")
    if affected:
        return "Semantic derived state is incomplete: " + ", ".join(affected)
    return None


def _semantic_readiness(
    schema_version: object,
    components: Mapping[str, Any],
) -> SemanticSearchReadiness:
    if schema_version != RUNTIME_HEALTH_SCHEMA:
        return SemanticSearchReadiness(
            "unknown",
            (
                "Semantic runtime readiness is unknown because the runtime-health "
                "schema is unsupported."
            ),
            (f"Expected {RUNTIME_HEALTH_SCHEMA}; got {schema_version!r}",),
            (),
        )

    missing = [name for name in _COMPONENT_ORDER if not isinstance(components.get(name), Mapping)]
    if missing:
        return SemanticSearchReadiness(
            "unknown",
            "Semantic runtime readiness is unknown because required component data is missing.",
            ("Missing components: " + ", ".join(missing),),
            (),
        )

    blockers: list[str] = []
    warnings: list[str] = []
    sqlite = _mapping(components["sqlite"])
    embedding = _mapping(components["embedding"])
    qdrant = _mapping(components["qdrant"])
    generation = _mapping(components["generation"])
    derived = _mapping(components["derived"])

    if sqlite.get("status") != "healthy":
        blockers.append(_issue_message(sqlite) or "SQLite runtime is not healthy.")
    if embedding.get("status") != "healthy":
        blockers.append(_issue_message(embedding) or "Embedding runtime is not healthy.")

    qdrant_details = _mapping(qdrant.get("details"))
    if qdrant.get("status") not in {"healthy"} or qdrant_details.get("ready") is not True:
        blockers.append(_issue_message(qdrant) or "Qdrant is not ready for semantic retrieval.")

    generation_status = generation.get("status")
    generation_code = _issue_code(generation)
    generation_details = _mapping(generation.get("details"))
    current_objects = int(generation_details.get("current_object_count") or 0)
    if generation_code in {"active_generation_missing", "generation_runtime_degraded"}:
        blockers.append(_issue_message(generation) or "Active Search generation is not usable.")
    elif generation_status != "healthy" and current_objects > 0:
        warnings.append(
            (_issue_message(generation) or "No healthy active Search generation is selected.")
            + " Semantic search may use legacy vector routing."
        )

    derived_warning = _semantic_derived_warning(derived)
    if derived_warning:
        warnings.append(derived_warning)
    elif derived.get("status") == "degraded":
        warnings.append(
            _issue_message(derived)
            or (
                "Non-semantic derived state is incomplete; inspect Derived state "
                "before maintenance work."
            )
        )

    if blockers:
        return SemanticSearchReadiness(
            "blocked",
            "Semantic Search is blocked by one or more runtime dependencies.",
            tuple(dict.fromkeys(blockers)),
            tuple(dict.fromkeys(warnings)),
        )
    if warnings:
        return SemanticSearchReadiness(
            "degraded",
            "Semantic runtime dependencies are available, but degraded state should be reviewed.",
            (),
            tuple(dict.fromkeys(warnings)),
        )
    return SemanticSearchReadiness(
        "ready",
        "Semantic runtime dependencies are ready.",
        (),
        (),
    )


def build_runtime_dashboard(runtime_health: Mapping[str, Any]) -> RuntimeDashboardPresentation:
    """Project the transport-neutral runtime-health snapshot into GUI-oriented text."""

    components = _mapping(runtime_health.get("components"))
    presentations: list[RuntimeComponentPresentation] = []
    for key in _COMPONENT_ORDER:
        component = _mapping(components.get(key))
        status = str(component.get("status") or "unknown")
        issue = _issue_message(component)
        presentations.append(
            RuntimeComponentPresentation(
                key=key,
                label=_COMPONENT_LABELS[key],
                status=status,
                summary=_component_summary(key, component),
                issue=issue,
                troubleshooting=_TROUBLESHOOTING[key] if issue or status != "healthy" else None,
            )
        )

    lifecycle = _mapping(runtime_health.get("lifecycle"))
    lifecycle_note = (
        "Qdrant lifecycle owner: external; SGOKB observes runtime health only "
        f"(observe={str(bool(lifecycle.get('observe'))).lower()}, "
        f"start/stop/restart={str(bool(lifecycle.get('start'))).lower()}/"
        f"{str(bool(lifecycle.get('stop'))).lower()}/"
        f"{str(bool(lifecycle.get('restart'))).lower()})."
    )
    return RuntimeDashboardPresentation(
        overall_status=str(runtime_health.get("overall_status") or "unknown"),
        readiness=_semantic_readiness(runtime_health.get("schema_version"), components),
        components=tuple(presentations),
        lifecycle_note=lifecycle_note,
        mcp_note=(
            "MCP runtime state is not part of sgokb.runtime-health/1.0. "
            "Use the MCP tab for the external stdio launch/configuration contract."
        ),
    )
