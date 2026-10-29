"""Transport-neutral operator dispatcher/session shared by CLI and future GUI."""

from __future__ import annotations

from pathlib import Path

from .application import Application
from .application_admin import ObjectAdminApplication
from .application_evidence import EvidenceReadApplication
from .application_exchange import PackageExchangeApplication, ResultExchangeApplication
from .application_read import RetrievalRuntimeUnavailableError
from .application_registry import RegistryOperatorApplication
from .application_render import RenderApplication
from .application_source import SourceOperatorApplication
from .application_system import RecoveryOperatorApplication, SystemOperatorApplication
from .application_version import VersionReadApplication
from .domain import ObjectSearchFilters
from .exchange.package_builder import DEFAULT_BUILD_ROOT
from .exchange.result_receipt import DEFAULT_INCOMING_ROOT
from .operation_contracts import (
    OUTCOME_BLOCKED,
    OUTCOME_PARTIAL,
    OperationOutcome,
    OperationRequest,
    normalize_operation_error,
)
from .providers import embedder_from_env
from .rendering import DEFAULT_RENDER_ROOT
from .repository import Repository
from .runtime import RuntimeFactory


PUBLIC_OPERATION_IDS = frozenset(
    {
        "source.import",
        "source.process",
        "source.status",
        "source.snapshots",
        "source.select-snapshot",
        "source.select-run",
        "object.add",
        "object.list",
        "object.show",
        "object.rename",
        "object.status",
        "object.alias.list",
        "object.alias.add",
        "object.class.set-primary",
        "object.class.add",
        "object.class.remove",
        "object.events",
        "object.relations",
        "association.list",
        "association.suggest",
        "association.set",
        "association.clear",
        "evidence.candidates",
        "evidence.select",
        "evidence.show",
        "evidence.provenance",
        "evidence.search",
        "registry.class.list",
        "registry.class.show",
        "registry.relation-type.list",
        "registry.relation-type.show",
        "registry.proposal.list",
        "registry.proposal.show",
        "registry.proposal.accept",
        "registry.proposal.reject",
        "registry.proposal.apply",
        "package.build",
        "package.stage",
        "package.preflight",
        "package.export",
        "result.detect",
        "result.receive",
        "result.list",
        "result.pending",
        "result.validate",
        "result.review",
        "result.import",
        "version.show",
        "version.diff",
        "search",
        "similar",
        "render",
        "mcp.serve",
        "system.status",
        "system.integrity",
        "system.derived.status",
        "system.derived.sync",
        "system.index.status",
        "system.index.rebuild",
        "system.backup.status",
        "system.backup.create",
        "system.backup.composite.create",
        "system.backup.composite.verify",
        "system.restore.plan",
        "system.restore.apply",
        "system.restore.composite.plan",
        "system.restore.composite.apply",
    }
)

TRANSPORT_OPERATION_IDS = frozenset({"mcp.serve"})
SHARED_OPERATION_IDS = PUBLIC_OPERATION_IDS - TRANSPORT_OPERATION_IDS

_PATH_ONLY_OPERATION_IDS = frozenset(
    {
        "system.backup.composite.verify",
        "system.restore.plan",
        "system.restore.apply",
        "system.restore.composite.plan",
        "system.restore.composite.apply",
    }
)


class OperatorSession:
    """Open a Repository per synchronous operation and dispatch shared semantics."""

    def __init__(
        self,
        workspace_path: str | Path,
        *,
        runtime_factory: RuntimeFactory | None = None,
    ) -> None:
        self.workspace_path = Path(workspace_path)
        self.runtime_factory = runtime_factory or RuntimeFactory()

    def execute(self, request: OperationRequest) -> OperationOutcome:
        operation_id = request.operation_id
        if operation_id not in PUBLIC_OPERATION_IDS:
            raise normalize_operation_error(
                operation_id, ValueError(f"Unknown operator operation: {operation_id}")
            )
        if operation_id in TRANSPORT_OPERATION_IDS:
            raise normalize_operation_error(
                operation_id,
                ValueError("mcp.serve is a transport lifecycle operation, not a synchronous operator call"),
            )
        try:
            if operation_id in _PATH_ONLY_OPERATION_IDS:
                return self._execute_recovery(request)
            repository = Repository(self.workspace_path)
            try:
                return self._execute_repository(repository, request)
            finally:
                repository.close()
        except Exception as exc:
            raise normalize_operation_error(operation_id, exc) from exc

    def _execute_recovery(self, request: OperationRequest) -> OperationOutcome:
        a = dict(request.arguments)
        recovery = RecoveryOperatorApplication()
        op = request.operation_id
        if op == "system.backup.composite.verify":
            data = recovery.composite_backup_verify(a["backup"])
        elif op == "system.restore.plan":
            data = recovery.restore_plan(a["backup"], db_target=self.workspace_path)
        elif op == "system.restore.apply":
            data = recovery.restore_apply(
                a["backup"],
                db_target=self.workspace_path,
                acknowledge_overwrite=bool(a.get("acknowledge_overwrite", False)),
            )
        elif op == "system.restore.composite.plan":
            data = recovery.composite_restore_plan(
                a["backup"],
                db_target=a["db_target"],
                raw_root=a["raw_root"],
                incoming_root=a["incoming_root"],
            )
        else:
            data = recovery.composite_restore_apply(
                a["backup"],
                db_target=a["db_target"],
                raw_root=a["raw_root"],
                incoming_root=a["incoming_root"],
                acknowledge_overwrite=bool(a.get("acknowledge_overwrite", False)),
            )
        return OperationOutcome(request.operation_id, data)

    def _execute_repository(self, repository, request: OperationRequest) -> OperationOutcome:
        op = request.operation_id
        a = dict(request.arguments)
        admin = ObjectAdminApplication(repository)

        if op.startswith("source."):
            source = SourceOperatorApplication(repository)
            if op == "source.status":
                return OperationOutcome(op, source.status())
            if op == "source.snapshots":
                return OperationOutcome(op, source.snapshots())
            if op == "source.select-snapshot":
                return OperationOutcome(
                    op, source.select_snapshot(a["source"], a["snapshot"], a["reason"])
                )
            if op == "source.select-run":
                return OperationOutcome(
                    op, source.select_run(a["snapshot"], a["run"], a["reason"])
                )
            if op == "source.import":
                result = source.import_path(a["path"])
            else:
                result = source.process(
                    a.get("snapshot"),
                    size=int(a.get("size", 1000)),
                    overlap=int(a.get("overlap", 100)),
                    include_auxiliary=bool(a.get("include_auxiliary", False)),
                )
            return OperationOutcome(
                op,
                list(result.items),
                state=OUTCOME_PARTIAL if result.partial else "success",
            )

        if op.startswith("object."):
            if op == "object.add":
                return OperationOutcome(
                    op,
                    admin.add_object(a["name"], a["primary_class"], a.get("alias", ())),
                )
            if op == "object.list":
                return OperationOutcome(op, admin.list_objects())
            object_id = admin.resolve_object_id(
                object_id=a.get("object_id"), name=a.get("name")
            )
            if op == "object.show":
                return OperationOutcome(
                    op,
                    admin.show(
                        object_id,
                        include_knowledge=bool(a.get("knowledge", False)),
                        version_id=a.get("version"),
                    ),
                )
            if op == "object.rename":
                return OperationOutcome(op, admin.rename_object(object_id, a["to"]))
            if op == "object.status":
                return OperationOutcome(op, admin.set_status(object_id, a["set"]))
            if op == "object.alias.list":
                return OperationOutcome(op, admin.aliases(object_id))
            if op == "object.alias.add":
                return OperationOutcome(
                    op,
                    admin.add_alias(
                        object_id,
                        a["value"],
                        language=a.get("language"),
                        kind=a.get("kind", "alias"),
                    ),
                )
            if op == "object.class.set-primary":
                return OperationOutcome(op, admin.set_primary_class(object_id, a["class_ref"]))
            if op == "object.class.add":
                return OperationOutcome(op, admin.add_class(object_id, a["class_ref"]))
            if op == "object.class.remove":
                return OperationOutcome(op, admin.remove_class(object_id, a["class_ref"]))
            if op == "object.events":
                return OperationOutcome(op, admin.events(object_id))
            read = self.runtime_factory.build_read_application(repository, with_semantic=False)
            return OperationOutcome(
                op,
                read.get_object_relations(
                    object_id,
                    version_id=a.get("version"),
                    include_evidence_refs=not bool(a.get("no_evidence", False)),
                ),
            )

        if op.startswith("association."):
            semantic = op == "association.suggest" and bool(a.get("semantic", False))
            app = Application(repository, embedder=embedder_from_env() if semantic else None)
            if op == "association.list":
                data = app.list_source_object_associations(a["object"])
            elif op == "association.suggest":
                data = app.suggest_source_associations(
                    a["object"],
                    max_candidates=int(a.get("max_candidates", 500)),
                    semantic=semantic,
                    semantic_batch_size=int(a.get("semantic_batch_size", 32)),
                )
            elif op == "association.set":
                data = app.set_source_object_association(
                    a["object"],
                    a["source"],
                    a["status"],
                    subject_relationship=a.get("subject_relationship"),
                    note=a.get("note"),
                )
            else:
                data = app.clear_source_object_association(a["object"], a["source"])
            return OperationOutcome(op, data)

        if op.startswith("evidence."):
            if op in {"evidence.candidates", "evidence.select"}:
                semantic = bool(a.get("semantic", False))
                app = Application(repository, embedder=embedder_from_env() if semantic else None)
                common = {
                    "max_candidates": int(a.get("max_candidates", 500)),
                    "semantic": semantic,
                    "semantic_batch_size": int(a.get("semantic_batch_size", 32)),
                    "manual_include": a.get("include_evidence", ()),
                    "manual_exclude": a.get("exclude_evidence", ()),
                }
                if op == "evidence.candidates":
                    data = app.retrieve_object_evidence(a["object"], **common)
                else:
                    data = app.select_object_evidence(
                        a["object"],
                        max_estimated_tokens=int(a.get("max_estimated_tokens", 12000)),
                        max_bytes=int(a.get("max_bytes", 65536)),
                        max_items=int(a.get("max_items", 64)),
                        **common,
                    )
                return OperationOutcome(op, data)
            with_semantic = bool(a.get("semantic_runtime", False)) if op == "evidence.search" else False
            read = self.runtime_factory.build_read_application(
                repository, with_semantic=with_semantic
            )
            evidence = EvidenceReadApplication(repository, read_application=read)
            if op == "evidence.show":
                return OperationOutcome(op, evidence.show(a["evidence_id"]))
            if op == "evidence.provenance":
                return OperationOutcome(op, evidence.provenance(a["evidence_id"]))
            return OperationOutcome(
                op,
                evidence.search(
                    a["query"],
                    mode=a.get("mode", "hybrid"),
                    limit=int(a.get("limit", 10)),
                    source_ids=a.get("source", ()),
                    object_id=a.get("object"),
                    association_status=a.get("association_status"),
                    language=a.get("language"),
                    include_historical=bool(a.get("include_historical", False)),
                    semantic_batch_size=int(a.get("semantic_batch_size", 32)),
                ),
            )

        if op.startswith("registry."):
            registry = RegistryOperatorApplication(repository)
            if op == "registry.class.list":
                data = registry.classes()
            elif op == "registry.class.show":
                data = registry.class_show(a["class_ref"])
            elif op == "registry.relation-type.list":
                data = registry.relation_types()
            elif op == "registry.relation-type.show":
                data = registry.relation_type_show(a["relation_ref"])
            elif op == "registry.proposal.list":
                data = registry.proposals(decision=a.get("decision"))
            elif op == "registry.proposal.show":
                data = registry.proposal_show(a["proposal_ref"])
            elif op in {"registry.proposal.accept", "registry.proposal.reject"}:
                data = registry.proposal_decide(
                    a["proposal_ref"],
                    "accepted" if op.endswith("accept") else "rejected",
                    note=a.get("note", ""),
                )
            else:
                data = registry.proposal_apply(a["proposal_ref"])
            return OperationOutcome(op, data)

        if op.startswith("package."):
            package = PackageExchangeApplication(repository)
            if op == "package.build":
                data = package.build(
                    a["object"],
                    build_root=a.get("build_root", DEFAULT_BUILD_ROOT),
                    include_evidence=a.get("include_evidence", ()),
                    exclude_evidence=a.get("exclude_evidence", ()),
                    max_estimated_tokens=int(a.get("max_estimated_tokens", 12000)),
                    max_bytes=int(a.get("max_bytes", 65536)),
                    max_items=int(a.get("max_items", 64)),
                    max_candidates=int(a.get("max_candidates", 500)),
                    knowledge_language=a.get("knowledge_language", "ja"),
                    package_version=a.get("package_version", "v1"),
                    max_total_raw_bytes=int(
                        a.get("max_total_raw_bytes", 16 * 1024 * 1024)
                    ),
                    max_single_raw_bytes=int(
                        a.get("max_single_raw_bytes", 8 * 1024 * 1024)
                    ),
                    max_raw_artifacts=int(a.get("max_raw_artifacts", 64)),
                )
                return OperationOutcome(op, data.to_dict())
            if op == "package.stage":
                data = package.stage(
                    a["source"], staging_root=a.get("staging_root", "exchange/staging")
                )
                return OperationOutcome(op, data.to_dict())
            if op == "package.preflight":
                data = package.preflight(a["package"], destination=a.get("destination"))
                return OperationOutcome(
                    op,
                    data.to_dict(),
                    warnings=("Package preflight is blocked",)
                    if data.disposition == "blocked"
                    else (),
                    state=OUTCOME_BLOCKED if data.disposition == "blocked" else "success",
                )
            data = package.export(
                a["package"],
                destination=a["destination"],
                acknowledge_review=bool(a.get("acknowledge_review", False)),
            )
            return OperationOutcome(op, data)

        if op.startswith("result."):
            result = ResultExchangeApplication(repository)
            incoming_root = a.get("incoming_root", DEFAULT_INCOMING_ROOT)
            if op == "result.detect":
                data = list(result.detect(incoming_root=incoming_root))
            elif op == "result.receive":
                data = result.receive(
                    a["result"],
                    package_id=a["package_id"],
                    incoming_root=incoming_root,
                ).to_dict()
            elif op == "result.list":
                data = list(result.list(package_id=a.get("package_id")))
            elif op == "result.pending":
                data = list(result.pending())
            elif op == "result.validate":
                validation = result.validate(
                    a["receipt_id"],
                    incoming_root=incoming_root,
                    force=bool(a.get("force", False)),
                )
                data = validation.to_dict()
                return OperationOutcome(
                    op,
                    data,
                    warnings=("Result validation did not reach valid state",)
                    if data.get("validation_state") != "valid"
                    else (),
                    state=OUTCOME_BLOCKED
                    if data.get("validation_state") != "valid"
                    else "success",
                )
            elif op == "result.review":
                data = result.review(a["receipt_id"], incoming_root=incoming_root)
            else:
                data = result.import_result(
                    a["receipt_id"],
                    incoming_root=incoming_root,
                    acknowledge_review=bool(a.get("acknowledge_review", False)),
                ).to_dict()
            return OperationOutcome(op, data)

        if op.startswith("version."):
            version = VersionReadApplication(repository)
            if op == "version.show":
                return OperationOutcome(op, version.show(a["version_id"]))
            return OperationOutcome(
                op, version.diff(a["before_version_id"], a["after_version_id"])
            )

        if op == "search":
            if bool(a.get("require_full_runtime", False)) and not bool(
                a.get("semantic_runtime", False)
            ):
                raise RetrievalRuntimeUnavailableError(
                    "--require-full-runtime requires --semantic-runtime"
                )
            read = self.runtime_factory.build_read_application(
                repository, with_semantic=bool(a.get("semantic_runtime", False))
            )
            filters = ObjectSearchFilters(
                primary_class=a.get("primary_class"),
                additional_class=a.get("additional_class"),
                ancestor_class=a.get("ancestor_class"),
                facet=a.get("facet"),
                version_id=a.get("version"),
                temporal_scope_id=a.get("temporal_scope"),
                knowledge_valid_at=a.get("valid_at"),
                derivation_kind=a.get("derivation_kind"),
                include_archived=bool(a.get("include_archived", False)),
            )
            response = read.search_objects(
                a["query"],
                filters=filters,
                limit=int(a.get("limit", 10)),
                mode=a.get("mode", "hybrid"),
                candidate_limit=a.get("candidate_limit"),
            )
            degraded = tuple(response.degraded_channels)
            if bool(a.get("require_full_runtime", False)) and degraded:
                raise RetrievalRuntimeUnavailableError(
                    "Hybrid Search degraded: " + ", ".join(degraded)
                )
            return OperationOutcome(op, response, warnings=degraded)

        if op == "similar":
            object_id = admin.resolve_object_id(
                object_id=a.get("object_id"), name=a.get("name")
            )
            read = self.runtime_factory.build_read_application(repository, with_semantic=True)
            return OperationOutcome(
                op,
                read.find_similar_objects(
                    object_id,
                    facet=a.get("facet"),
                    limit=int(a.get("limit", 10)),
                    cross_class=bool(a.get("cross_class", False)),
                    source_version_id=a.get("version"),
                    include_archived=bool(a.get("include_archived", False)),
                ),
            )

        if op == "render":
            rendered = RenderApplication(repository).render(
                object_id=a.get("object"),
                version_id=a.get("version"),
                output_root=a.get("output_root", DEFAULT_RENDER_ROOT),
            )
            return OperationOutcome(op, rendered.to_dict())

        if op.startswith("system."):
            system = SystemOperatorApplication(
                repository, self.workspace_path, runtime_factory=self.runtime_factory
            )
            if op == "system.status":
                data = system.status()
            elif op == "system.integrity":
                data = system.integrity()
            elif op == "system.derived.status":
                data = system.derived_status(
                    a.get("object_id"),
                    semantic_runtime=bool(a.get("semantic_runtime", False)),
                )
            elif op == "system.derived.sync":
                data = system.derived_sync(
                    a.get("object_id"),
                    semantic_runtime=bool(a.get("semantic_runtime", False)),
                )
                return OperationOutcome(
                    op,
                    data,
                    state=OUTCOME_PARTIAL if data.partial else "success",
                )
            elif op == "system.index.status":
                data = system.index_status()
            elif op == "system.index.rebuild":
                data = system.index_rebuild()
            elif op == "system.backup.status":
                data = system.backup_status(root=a.get("root", "backups"))
            elif op == "system.backup.create":
                data = system.backup_create(
                    output=a.get("output"), root=a.get("root", "backups")
                )
            elif op == "system.backup.composite.create":
                data = system.composite_backup_create(
                    incoming_root=a["incoming_root"],
                    output=a.get("output"),
                    root=a.get("root", "backups"),
                )
            else:
                raise AssertionError(f"Unhandled repository system operation: {op}")
            return OperationOutcome(op, data)

        raise AssertionError(f"Unhandled shared operation: {op}")