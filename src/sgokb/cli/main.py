"""Phase M Object-centered SGOKB CLI."""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
from dataclasses import asdict
from pathlib import Path

import httpx

from sgokb.application import Application
from sgokb.application_admin import ObjectAdminApplication, ObjectSelectorError
from sgokb.application_read import (
    KnowledgeReadApplication,
    KnowledgeRequestError,
    RetrievalRuntimeUnavailableError,
)
from sgokb.domain import ObjectSearchFilters
from sgokb.exchange.package_builder import DEFAULT_BUILD_ROOT, ObjectEvidencePackageBuilder
from sgokb.exchange.package_transfer import PackageTransferService
from sgokb.exchange.result_import import ObjectVersionImportService
from sgokb.exchange.result_receipt import DEFAULT_INCOMING_ROOT, ResultReceiptService
from sgokb.exchange.result_validation import ResultValidationService
from sgokb.providers import embedder_from_env
from sgokb.rendering import DEFAULT_RENDER_ROOT, MarkdownRenderService
from sgokb.repository import Repository
from sgokb.retrieval import KnowledgeVectorIndexBuilder
from sgokb.review import DiffReviewMarkdownRenderer, DiffReviewService
from sgokb.storage import PackageExchangeAuditRepository
from sgokb.system_ops import (
    backup_status,
    create_backup,
    index_status,
    integrity,
    restore_apply,
    restore_plan,
    system_status,
)

from .contracts import (
    EXIT_BLOCKED,
    EXIT_INPUT,
    EXIT_INTEGRITY,
    EXIT_IO,
    EXIT_NOT_FOUND,
    EXIT_PARTIAL,
    EXIT_RUNTIME,
    emit_error,
    emit_success,
)
from .runtime import build_read_application, semantic_runtime


def _selector(parser: argparse.ArgumentParser) -> None:
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--object", dest="object_id")
    group.add_argument("--name")


def _semantic_search_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--mode", choices=("lexical", "semantic", "hybrid"), default="hybrid")
    parser.add_argument(
        "--semantic-runtime",
        action="store_true",
        help="Enable the frozen local embedding + Qdrant runtime; no cloud fallback",
    )


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description="Source Grounded Object Knowledge Base")
    root.add_argument("--db", default=os.environ.get("SGOKB_DB", ".local/sgokb.sqlite"))
    root.add_argument("--format", choices=("json", "text"), default="json")
    domains = root.add_subparsers(dest="domain", required=True)

    source = domains.add_parser("source", help="Canonical Source/Snapshot ingestion and inspection")
    source_actions = source.add_subparsers(dest="action", required=True)
    source_import = source_actions.add_parser("import")
    source_import.add_argument("path", type=Path)
    process = source_actions.add_parser("process")
    process.add_argument("--snapshot")
    process.add_argument("--size", type=int, default=1000)
    process.add_argument("--overlap", type=int, default=100)
    process.add_argument("--include-auxiliary", action="store_true")
    source_actions.add_parser("status")
    source_actions.add_parser("snapshots")

    obj = domains.add_parser("object", help="Object Registry and accepted Knowledge reads")
    object_actions = obj.add_subparsers(dest="action", required=True)
    add = object_actions.add_parser("add")
    add.add_argument("--name", required=True)
    add.add_argument("--primary-class", required=True)
    add.add_argument("--alias", action="append", default=[])
    object_actions.add_parser("list")
    show = object_actions.add_parser("show")
    _selector(show)
    show.add_argument("--knowledge", action="store_true")
    show.add_argument("--version")
    rename = object_actions.add_parser("rename")
    _selector(rename)
    rename.add_argument("--to", required=True)
    status = object_actions.add_parser("status")
    _selector(status)
    status.add_argument("--set", choices=("active", "archived"), required=True)

    alias = object_actions.add_parser("alias")
    alias_actions = alias.add_subparsers(dest="subaction", required=True)
    alias_list = alias_actions.add_parser("list")
    _selector(alias_list)
    alias_add = alias_actions.add_parser("add")
    _selector(alias_add)
    alias_add.add_argument("value")
    alias_add.add_argument("--language")
    alias_add.add_argument("--kind", default="alias")

    classes = object_actions.add_parser("class")
    class_actions = classes.add_subparsers(dest="subaction", required=True)
    set_primary = class_actions.add_parser("set-primary")
    _selector(set_primary)
    set_primary.add_argument("class_ref")
    add_class = class_actions.add_parser("add")
    _selector(add_class)
    add_class.add_argument("class_ref")
    remove_class = class_actions.add_parser("remove")
    _selector(remove_class)
    remove_class.add_argument("class_ref")

    events = object_actions.add_parser("events")
    _selector(events)
    relations = object_actions.add_parser("relations")
    _selector(relations)
    relations.add_argument("--version")
    relations.add_argument("--no-evidence", action="store_true")

    association = domains.add_parser("association")
    association_actions = association.add_subparsers(dest="action", required=True)
    association_list = association_actions.add_parser("list")
    association_list.add_argument("--object", required=True)
    association_suggest = association_actions.add_parser("suggest")
    association_suggest.add_argument("--object", required=True)
    association_suggest.add_argument("--max-candidates", type=int, default=500)
    association_suggest.add_argument("--semantic", action="store_true")
    association_suggest.add_argument("--semantic-batch-size", type=int, default=32)
    association_set = association_actions.add_parser("set")
    association_set.add_argument("--object", required=True)
    association_set.add_argument("--source", required=True)
    association_set.add_argument(
        "--status", choices=("candidate", "confirmed", "excluded"), required=True
    )
    association_set.add_argument("--subject-relationship")
    association_set.add_argument("--note")
    association_clear = association_actions.add_parser("clear")
    association_clear.add_argument("--object", required=True)
    association_clear.add_argument("--source", required=True)

    evidence = domains.add_parser("evidence")
    evidence_actions = evidence.add_subparsers(dest="action", required=True)
    for action in ("candidates", "select"):
        item = evidence_actions.add_parser(action)
        item.add_argument("--object", required=True)
        item.add_argument("--include-evidence", action="append", default=[])
        item.add_argument("--exclude-evidence", action="append", default=[])
        item.add_argument("--max-candidates", type=int, default=500)
        item.add_argument("--semantic", action="store_true")
        item.add_argument("--semantic-batch-size", type=int, default=32)
        if action == "select":
            item.add_argument("--max-estimated-tokens", type=int, default=12000)
            item.add_argument("--max-bytes", type=int, default=65536)
            item.add_argument("--max-items", type=int, default=64)
    evidence_show = evidence_actions.add_parser("show")
    evidence_show.add_argument("evidence_id")
    evidence_prov = evidence_actions.add_parser("provenance")
    evidence_prov.add_argument("evidence_id")
    evidence_search = evidence_actions.add_parser("search")
    evidence_search.add_argument("query")
    evidence_search.add_argument(
        "--mode", choices=("lexical", "semantic", "hybrid"), default="hybrid"
    )
    evidence_search.add_argument("--limit", type=int, default=10)
    evidence_search.add_argument("--source", action="append", default=[])
    evidence_search.add_argument("--object")
    evidence_search.add_argument("--association-status")
    evidence_search.add_argument("--language")
    evidence_search.add_argument("--include-historical", action="store_true")
    evidence_search.add_argument("--semantic-batch-size", type=int, default=32)
    evidence_search.add_argument("--semantic-runtime", action="store_true")

    registry = domains.add_parser("registry")
    registry_domains = registry.add_subparsers(dest="registry_domain", required=True)
    registry_class = registry_domains.add_parser("class")
    registry_class_actions = registry_class.add_subparsers(dest="action", required=True)
    registry_class_actions.add_parser("list")
    class_show = registry_class_actions.add_parser("show")
    class_show.add_argument("class_ref")
    relation_type = registry_domains.add_parser("relation-type")
    relation_actions = relation_type.add_subparsers(dest="action", required=True)
    relation_actions.add_parser("list")
    relation_show = relation_actions.add_parser("show")
    relation_show.add_argument("relation_ref")
    proposal = registry_domains.add_parser("proposal")
    proposal_actions = proposal.add_subparsers(dest="action", required=True)
    proposal_list = proposal_actions.add_parser("list")
    proposal_list.add_argument("--decision", choices=("pending", "accepted", "rejected"))
    proposal_show = proposal_actions.add_parser("show")
    proposal_show.add_argument("proposal_ref")
    for decision in ("accept", "reject"):
        p = proposal_actions.add_parser(decision)
        p.add_argument("proposal_ref")
        p.add_argument("--note", default="")
    proposal_apply = proposal_actions.add_parser("apply")
    proposal_apply.add_argument("proposal_ref")

    package = domains.add_parser("package")
    package_actions = package.add_subparsers(dest="action", required=True)
    build = package_actions.add_parser("build")
    build.add_argument("--object", required=True)
    build.add_argument(
        "--build-root",
        type=Path,
        default=Path(os.environ.get("SGOKB_PACKAGE_BUILD_ROOT", DEFAULT_BUILD_ROOT)),
    )
    build.add_argument("--include-evidence", action="append", default=[])
    build.add_argument("--exclude-evidence", action="append", default=[])
    build.add_argument("--max-estimated-tokens", type=int, default=12000)
    build.add_argument("--max-bytes", type=int, default=65536)
    build.add_argument("--max-items", type=int, default=64)
    build.add_argument("--max-candidates", type=int, default=500)
    build.add_argument("--knowledge-language", default="ja")
    stage = package_actions.add_parser("stage")
    stage.add_argument("source", type=Path)
    stage.add_argument(
        "--staging-root",
        type=Path,
        default=Path(os.environ.get("SGOKB_EXCHANGE_STAGING", "exchange/staging")),
    )
    preflight = package_actions.add_parser("preflight")
    preflight.add_argument("package", type=Path)
    preflight.add_argument("--destination", type=Path)
    export = package_actions.add_parser("export")
    export.add_argument("package", type=Path)
    export.add_argument("--destination", type=Path, required=True)
    export.add_argument("--acknowledge-review", action="store_true")

    result = domains.add_parser("result")
    result_actions = result.add_subparsers(dest="action", required=True)
    incoming_default = Path(os.environ.get("SGOKB_EXCHANGE_INCOMING", DEFAULT_INCOMING_ROOT))
    detect = result_actions.add_parser("detect")
    detect.add_argument("--incoming-root", type=Path, default=incoming_default)
    receive = result_actions.add_parser("receive")
    receive.add_argument("result", type=Path)
    receive.add_argument("--package-id", required=True)
    receive.add_argument("--incoming-root", type=Path, default=incoming_default)
    result_list = result_actions.add_parser("list")
    result_list.add_argument("--package-id")
    result_actions.add_parser("pending")
    validate = result_actions.add_parser("validate")
    validate.add_argument("receipt_id")
    validate.add_argument("--incoming-root", type=Path, default=incoming_default)
    validate.add_argument("--force", action="store_true")
    review = result_actions.add_parser("review")
    review.add_argument("receipt_id")
    review.add_argument("--incoming-root", type=Path, default=incoming_default)
    review.add_argument("--review-format", choices=("json", "markdown"), default="json")
    result_import = result_actions.add_parser("import")
    result_import.add_argument("receipt_id")
    result_import.add_argument("--incoming-root", type=Path, default=incoming_default)
    result_import.add_argument("--acknowledge-review", action="store_true")

    version = domains.add_parser("version")
    version_actions = version.add_subparsers(dest="action", required=True)
    version_show = version_actions.add_parser("show")
    version_show.add_argument("version_id")
    version_diff = version_actions.add_parser("diff")
    version_diff.add_argument("before_version_id")
    version_diff.add_argument("after_version_id")
    version_diff.add_argument("--diff-format", choices=("json", "markdown"), default="json")

    search = domains.add_parser("search")
    search.add_argument("query")
    _semantic_search_options(search)
    search.add_argument("--require-full-runtime", action="store_true")
    search.add_argument("--limit", type=int, default=10)
    search.add_argument("--candidate-limit", type=int)
    search.add_argument("--primary-class")
    search.add_argument("--additional-class")
    search.add_argument("--ancestor-class")
    search.add_argument("--facet")
    search.add_argument("--version")
    search.add_argument("--temporal-scope")
    search.add_argument("--valid-at")
    search.add_argument("--derivation-kind")
    search.add_argument("--include-archived", action="store_true")

    similar = domains.add_parser("similar")
    _selector(similar)
    similar.add_argument("--facet")
    similar.add_argument("--limit", type=int, default=10)
    similar.add_argument("--cross-class", action="store_true")
    similar.add_argument("--version")
    similar.add_argument("--include-archived", action="store_true")

    render = domains.add_parser("render")
    target = render.add_mutually_exclusive_group(required=True)
    target.add_argument("--version")
    target.add_argument("--object")
    render.add_argument(
        "--output-root",
        type=Path,
        default=Path(os.environ.get("SGOKB_RENDER_ROOT", DEFAULT_RENDER_ROOT)),
    )

    mcp = domains.add_parser("mcp")
    mcp_actions = mcp.add_subparsers(dest="action", required=True)
    serve = mcp_actions.add_parser("serve")
    serve.add_argument("--semantic-runtime", action="store_true")

    system = domains.add_parser("system")
    system_actions = system.add_subparsers(dest="action", required=True)
    system_actions.add_parser("status")
    system_actions.add_parser("integrity")
    index = system_actions.add_parser("index")
    index_actions = index.add_subparsers(dest="subaction", required=True)
    index_actions.add_parser("status")
    index_actions.add_parser("rebuild")
    backup = system_actions.add_parser("backup")
    backup_actions = backup.add_subparsers(dest="subaction", required=True)
    backup_status_parser = backup_actions.add_parser("status")
    backup_status_parser.add_argument("--root", type=Path, default=Path("backups"))
    backup_create = backup_actions.add_parser("create")
    backup_create.add_argument("--output", type=Path)
    backup_create.add_argument("--root", type=Path, default=Path("backups"))
    restore = system_actions.add_parser("restore")
    restore_actions = restore.add_subparsers(dest="subaction", required=True)
    restore_plan_parser = restore_actions.add_parser("plan")
    restore_plan_parser.add_argument("backup", type=Path)
    restore_apply_parser = restore_actions.add_parser("apply")
    restore_apply_parser.add_argument("backup", type=Path)
    restore_apply_parser.add_argument("--acknowledge-overwrite", action="store_true")
    return root


def _command(args) -> str:
    parts = [args.domain]
    for name in ("registry_domain", "action", "subaction"):
        value = getattr(args, name, None)
        if value:
            parts.append(value)
    return ".".join(parts)


def _manifest(path: Path) -> dict:
    return json.loads((path / "manifest.json").read_text(encoding="utf-8"))


def _resolve(admin: ObjectAdminApplication, args) -> str:
    return admin.resolve_object_id(
        object_id=getattr(args, "object_id", None),
        name=getattr(args, "name", None),
    )


def _source_dispatch(repository, args):
    app = Application(
        repository,
        embedder=(embedder_from_env() if getattr(args, "semantic", False) else None),
    )
    if args.action == "status":
        return repository.source_store.status(), False
    if args.action == "snapshots":
        result = [
            {
                "id": s.snapshot_id,
                "source_id": s.source_id,
                "title": s.title,
                "captured_at": s.captured_at,
                "completeness": s.completeness.value,
                "effective": bool(
                    (effective := repository.source_store.effective_snapshot(s.source_id))
                    and effective.snapshot_id == s.snapshot_id
                ),
            }
            for s in repository.source_store.snapshots()
        ]
        return result, False

    if args.action == "import":
        targets = (
            [args.path]
            if args.path.is_file()
            else sorted(args.path.rglob("*.webcapture.zip"))
        )
    else:
        targets = (
            [args.snapshot]
            if args.snapshot
            else [s.snapshot_id for s in repository.source_store.snapshots()]
        )
    if not targets:
        raise ValueError("No input bundles or snapshots found")
    output = []
    failed = False
    for target in targets:
        try:
            if args.action == "import":
                value = app.import_source_path(target)
            else:
                value = app.process_source_snapshot(
                    target, args.size, args.overlap, args.include_auxiliary
                )
            output.append(value)
        except Exception as exc:
            failed = True
            output.append(
                {"input": str(target), "error": type(exc).__name__, "reason": str(exc)}
            )
    return output, failed


def _object_dispatch(repository, args, admin: ObjectAdminApplication):
    read = KnowledgeReadApplication(repository)
    if args.action == "add":
        return admin.add_object(args.name, args.primary_class, args.alias)
    if args.action == "list":
        return admin.list_objects()
    object_id = _resolve(admin, args)
    if args.action == "show":
        registry = admin.show_object(object_id)
        if not args.knowledge:
            return registry
        if registry["current_version_id"] is None and args.version is None:
            return {"registry": registry, "knowledge": None}
        return {
            "registry": registry,
            "knowledge": read.get_object(object_id, version_id=args.version),
        }
    if args.action == "rename":
        return admin.rename_object(object_id, args.to)
    if args.action == "status":
        return admin.set_status(object_id, args.set)
    if args.action == "alias":
        if args.subaction == "list":
            return admin.aliases(object_id)
        return admin.add_alias(
            object_id, args.value, language=args.language, kind=args.kind
        )
    if args.action == "class":
        if args.subaction == "set-primary":
            return admin.set_primary_class(object_id, args.class_ref)
        if args.subaction == "add":
            return admin.add_class(object_id, args.class_ref)
        return admin.remove_class(object_id, args.class_ref)
    if args.action == "events":
        return admin.events(object_id)
    return read.get_object_relations(
        object_id,
        version_id=args.version,
        include_evidence_refs=not args.no_evidence,
    )


def _association_dispatch(repository, args):
    embedder = embedder_from_env() if args.action == "suggest" and args.semantic else None
    app = Application(repository, embedder=embedder)
    if args.action == "list":
        return app.list_source_object_associations(args.object)
    if args.action == "suggest":
        return app.suggest_source_associations(
            args.object,
            max_candidates=args.max_candidates,
            semantic=args.semantic,
            semantic_batch_size=args.semantic_batch_size,
        )
    if args.action == "set":
        return app.set_source_object_association(
            args.object,
            args.source,
            args.status,
            subject_relationship=args.subject_relationship,
            note=args.note,
        )
    return app.clear_source_object_association(args.object, args.source)


def _evidence_dispatch(repository, args):
    if args.action in {"show", "search"}:
        read = build_read_application(
            repository,
            with_semantic=bool(getattr(args, "semantic_runtime", False)),
        )
        if args.action == "show":
            return read.get_evidence(args.evidence_id)
        return read.search_evidence(
            args.query,
            mode=args.mode,
            limit=args.limit,
            source_ids=args.source,
            object_id=args.object,
            association_status=args.association_status,
            language=args.language,
            include_historical=args.include_historical,
            semantic_batch_size=args.semantic_batch_size,
        )
    if args.action == "provenance":
        return asdict(repository.source_store.evidence_provenance(args.evidence_id))

    embedder = embedder_from_env() if args.semantic else None
    app = Application(repository, embedder=embedder)
    common = {
        "max_candidates": args.max_candidates,
        "semantic": args.semantic,
        "semantic_batch_size": args.semantic_batch_size,
        "manual_include": args.include_evidence,
        "manual_exclude": args.exclude_evidence,
    }
    if args.action == "candidates":
        return app.retrieve_object_evidence(args.object, **common)
    return app.select_object_evidence(
        args.object,
        max_estimated_tokens=args.max_estimated_tokens,
        max_bytes=args.max_bytes,
        max_items=args.max_items,
        **common,
    )


def _registry_dispatch(repository, args, admin: ObjectAdminApplication):
    if args.registry_domain == "class":
        return admin.classes() if args.action == "list" else admin.class_show(args.class_ref)
    if args.registry_domain == "relation-type":
        return (
            admin.relation_types()
            if args.action == "list"
            else admin.relation_type_show(args.relation_ref)
        )
    store = repository.registry_proposals
    if args.action == "list":
        return store.list_proposals(decision=args.decision)
    if args.action == "show":
        return store.proposal(args.proposal_ref)
    if args.action in {"accept", "reject"}:
        decision = "accepted" if args.action == "accept" else "rejected"
        return store.decide(args.proposal_ref, decision, note=args.note)
    return store.apply(args.proposal_ref)


def _package_dispatch(repository, args):
    transfer = PackageTransferService()
    if args.action == "preflight":
        return transfer.preflight(args.package, args.destination).to_dict()
    audit = PackageExchangeAuditRepository(repository.db)
    if args.action == "build":
        return (
            ObjectEvidencePackageBuilder(repository)
            .build(
                args.object,
                build_root=args.build_root,
                max_estimated_tokens=args.max_estimated_tokens,
                max_bytes=args.max_bytes,
                max_items=args.max_items,
                max_candidates=args.max_candidates,
                semantic=False,
                manual_include=args.include_evidence,
                manual_exclude=args.exclude_evidence,
                knowledge_language=args.knowledge_language,
            )
            .to_dict()
        )
    if args.action == "stage":
        staged = transfer.stage_from_directory(args.source, args.staging_root)
        manifest = _manifest(Path(staged.path))
        audit.record_staged(manifest, staged.path, staged.preflight.to_dict())
        return staged.to_dict()
    exported = transfer.export(
        args.package,
        args.destination,
        acknowledge_review=args.acknowledge_review,
    )
    manifest = _manifest(Path(args.package).resolve())
    event_id = audit.record_export(
        exported.package_id,
        exported.manifest_sha256,
        exported.destination_root,
        exported.path,
        acknowledged_review=exported.acknowledged_review,
        already_present=exported.already_present,
    )
    result = exported.to_dict()
    result["audit_event_id"] = event_id
    return result


def _result_dispatch(repository, args):
    audit = PackageExchangeAuditRepository(repository.db)
    receipts = ResultReceiptService(audit)
    if args.action == "detect":
        return [item.to_dict() for item in receipts.detect(args.incoming_root)]
    if args.action == "receive":
        return receipts.receive(
            args.result, args.package_id, args.incoming_root
        ).to_dict()
    if args.action == "list":
        return list(audit.result_receipts(args.package_id))
    if args.action == "pending":
        return list(audit.pending_result_receipts())
    if args.action == "validate":
        return ResultValidationService(repository, audit).validate_receipt(
            args.receipt_id,
            incoming_root=args.incoming_root,
            force=args.force,
        ).to_dict()
    if args.action == "review":
        report = DiffReviewService(repository, audit).review_result(
            args.receipt_id,
            incoming_root=args.incoming_root,
        )
        return (
            DiffReviewMarkdownRenderer().render_review(report)
            if args.review_format == "markdown"
            else report.to_dict()
        )
    return (
        ObjectVersionImportService(repository, audit)
        .import_receipt(
            args.receipt_id,
            incoming_root=args.incoming_root,
            acknowledge_review=args.acknowledge_review,
        )
        .to_dict()
    )


def _version_dispatch(repository, args):
    if args.action == "show":
        row = repository.db.execute(
            "SELECT object_id FROM object_versions WHERE id=?", (args.version_id,)
        ).fetchone()
        if not row:
            raise ValueError("Object Version was not found")
        return KnowledgeReadApplication(repository).get_object(
            row["object_id"], version_id=args.version_id
        )
    report = DiffReviewService(
        repository, PackageExchangeAuditRepository(repository.db)
    ).diff_versions(args.before_version_id, args.after_version_id)
    return (
        DiffReviewMarkdownRenderer().render_diff(report)
        if args.diff_format == "markdown"
        else report.to_dict()
    )


def _search_dispatch(repository, args):
    if args.require_full_runtime and not args.semantic_runtime:
        raise RetrievalRuntimeUnavailableError(
            "--require-full-runtime requires --semantic-runtime"
        )
    read = build_read_application(repository, with_semantic=args.semantic_runtime)
    filters = ObjectSearchFilters(
        primary_class=args.primary_class,
        additional_class=args.additional_class,
        ancestor_class=args.ancestor_class,
        facet=args.facet,
        version_id=args.version,
        temporal_scope_id=args.temporal_scope,
        knowledge_valid_at=args.valid_at,
        derivation_kind=args.derivation_kind,
        include_archived=args.include_archived,
    )
    response = read.search_objects(
        args.query,
        filters=filters,
        limit=args.limit,
        mode=args.mode,
        candidate_limit=args.candidate_limit,
    )
    if args.require_full_runtime and response.degraded_channels:
        raise RetrievalRuntimeUnavailableError(
            "Hybrid Search degraded: " + ", ".join(response.degraded_channels)
        )
    return response, response.degraded_channels


def _similar_dispatch(repository, args, admin):
    object_id = _resolve(admin, args)
    read = build_read_application(repository, with_semantic=True)
    return read.find_similar_objects(
        object_id,
        facet=args.facet,
        limit=args.limit,
        cross_class=args.cross_class,
        source_version_id=args.version,
        include_archived=args.include_archived,
    )


def _render_dispatch(repository, args):
    version_id = args.version
    if version_id is None:
        version_id = repository.version_store.current_version_id(args.object)
        if version_id is None:
            raise ValueError("Object has no current accepted Version to render")
    return (
        MarkdownRenderService(repository)
        .render_version(version_id, output_root=args.output_root)
        .to_dict()
    )


def _mcp_dispatch(repository, args):
    from sgokb.mcp import MCPReadAdapter
    from sgokb.mcp.server import run_stdio

    read = build_read_application(repository, with_semantic=args.semantic_runtime)
    run_stdio(MCPReadAdapter(read))
    return {"transport": "stdio", "stopped": True}


def _system_dispatch(repository, db_path: Path, args):
    if args.action == "status":
        return system_status(repository, db_path)
    if args.action == "integrity":
        return integrity(repository)
    if args.action == "index":
        if args.subaction == "status":
            return index_status(repository)
        provider, vector = semantic_runtime()
        metadata = KnowledgeVectorIndexBuilder(repository, vector).rebuild(provider.space)
        return metadata
    if args.action == "backup":
        if args.subaction == "status":
            return backup_status(args.root)
        return create_backup(repository, args.output, args.root)
    raise AssertionError("restore is handled before Repository is opened")


def _error_exit(exc: Exception) -> tuple[str, int]:
    if isinstance(exc, ObjectSelectorError):
        return getattr(exc, "code", "object_selector_error"), EXIT_NOT_FOUND
    if isinstance(exc, RetrievalRuntimeUnavailableError):
        return getattr(exc, "code", "retrieval_runtime_unavailable"), EXIT_RUNTIME
    if isinstance(exc, KnowledgeRequestError):
        message = str(exc).lower()
        code = EXIT_NOT_FOUND if "not found" in message or "unknown" in message else EXIT_INPUT
        return getattr(exc, "code", "invalid_knowledge_request"), code
    if isinstance(exc, PermissionError):
        return "operation_blocked", EXIT_BLOCKED
    if isinstance(exc, FileNotFoundError):
        return "file_not_found", EXIT_IO
    if isinstance(exc, (OSError, httpx.HTTPError)):
        return "io_or_provider_error", EXIT_IO
    if isinstance(exc, sqlite3.IntegrityError):
        return "integrity_error", EXIT_INTEGRITY
    if isinstance(exc, (ValueError, KeyError, json.JSONDecodeError)):
        text = str(exc).lower()
        if any(word in text for word in ("not found", "unknown ", "ambiguous")):
            return "not_found", EXIT_NOT_FOUND
        if any(
            word in text
            for word in ("requires explicit", "blocked", "review acknowledgement")
        ):
            return "precondition_failed", EXIT_BLOCKED
        return "invalid_input", EXIT_INPUT
    return "internal_error", 1


def main(argv=None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = parser().parse_args(argv)
    command = _command(args)
    db_path = Path(args.db)
    repository = None

    try:
        if args.domain == "system" and args.action == "restore":
            if args.subaction == "plan":
                data = restore_plan(args.backup, db_path)
            else:
                data = restore_apply(
                    args.backup,
                    db_path,
                    acknowledge_overwrite=args.acknowledge_overwrite,
                )
            return emit_success(command, data, output_format=args.format)

        repository = Repository(db_path)
        admin = ObjectAdminApplication(repository)
        warnings = ()
        partial = False

        if args.domain == "source":
            data, partial = _source_dispatch(repository, args)
        elif args.domain == "object":
            data = _object_dispatch(repository, args, admin)
        elif args.domain == "association":
            data = _association_dispatch(repository, args)
        elif args.domain == "evidence":
            data = _evidence_dispatch(repository, args)
        elif args.domain == "registry":
            data = _registry_dispatch(repository, args, admin)
        elif args.domain == "package":
            data = _package_dispatch(repository, args)
            if args.action == "preflight" and data.get("disposition") == "blocked":
                return emit_success(
                    command,
                    data,
                    warnings=("Package preflight is blocked",),
                    output_format=args.format,
                    exit_code=EXIT_BLOCKED,
                )
        elif args.domain == "result":
            data = _result_dispatch(repository, args)
            if args.action == "validate" and data.get("validation_state") != "valid":
                return emit_success(
                    command,
                    data,
                    warnings=("Result validation did not reach valid state",),
                    output_format=args.format,
                    exit_code=EXIT_BLOCKED,
                )
        elif args.domain == "version":
            data = _version_dispatch(repository, args)
        elif args.domain == "search":
            data, warnings = _search_dispatch(repository, args)
        elif args.domain == "similar":
            data = _similar_dispatch(repository, args, admin)
        elif args.domain == "render":
            data = _render_dispatch(repository, args)
        elif args.domain == "mcp":
            _mcp_dispatch(repository, args)
            return 0
        else:
            data = _system_dispatch(repository, db_path, args)

        return emit_success(
            command,
            data,
            warnings=warnings,
            output_format=args.format,
            exit_code=EXIT_PARTIAL if partial else 0,
        )
    except Exception as exc:
        code, exit_code = _error_exit(exc)
        return emit_error(
            command,
            code,
            str(exc),
            exit_code=exit_code,
            output_format=args.format,
        )
    finally:
        if repository is not None:
            repository.close()
