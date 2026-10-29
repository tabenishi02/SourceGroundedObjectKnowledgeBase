"""Object-centered SGOKB CLI presentation adapter."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from sgokb.application_operator import OperatorSession
from sgokb.exchange.package_builder import DEFAULT_BUILD_ROOT
from sgokb.exchange.result_receipt import DEFAULT_INCOMING_ROOT
from sgokb.operation_contracts import (
    CATEGORY_BLOCKED,
    CATEGORY_INPUT,
    CATEGORY_INTEGRITY,
    CATEGORY_IO,
    CATEGORY_NOT_FOUND,
    CATEGORY_RUNTIME,
    OUTCOME_BLOCKED,
    OUTCOME_PARTIAL,
    OperationFailure,
    OperationRequest,
)
from sgokb.rendering import DEFAULT_RENDER_ROOT
from sgokb.repository import Repository
from sgokb.review import DiffReviewMarkdownRenderer

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
from .runtime import runtime_factory


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
    select_snapshot = source_actions.add_parser("select-snapshot")
    select_snapshot.add_argument("--source", required=True)
    select_snapshot.add_argument("--snapshot", required=True)
    select_snapshot.add_argument("--reason", required=True)
    select_run = source_actions.add_parser("select-run")
    select_run.add_argument("--snapshot", required=True)
    select_run.add_argument("--run", required=True)
    select_run.add_argument("--reason", required=True)

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
    build.add_argument("--package-version", choices=("v1", "v2"), default="v1")
    build.add_argument("--include-evidence", action="append", default=[])
    build.add_argument("--exclude-evidence", action="append", default=[])
    build.add_argument("--max-estimated-tokens", type=int, default=12000)
    build.add_argument("--max-bytes", type=int, default=65536)
    build.add_argument("--max-items", type=int, default=64)
    build.add_argument("--max-candidates", type=int, default=500)
    build.add_argument("--knowledge-language", default="ja")
    build.add_argument("--max-total-raw-bytes", type=int, default=16 * 1024 * 1024)
    build.add_argument("--max-single-raw-bytes", type=int, default=8 * 1024 * 1024)
    build.add_argument("--max-raw-artifacts", type=int, default=64)
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
    derived = system_actions.add_parser("derived")
    derived_actions = derived.add_subparsers(dest="subaction", required=True)
    for action in ("status", "sync"):
        operation = derived_actions.add_parser(action)
        operation.add_argument("--object", dest="object_id")
        operation.add_argument("--semantic-runtime", action="store_true")
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
    composite_backup = backup_actions.add_parser("composite")
    composite_backup_actions = composite_backup.add_subparsers(
        dest="composite_action", required=True
    )
    composite_create = composite_backup_actions.add_parser("create")
    composite_create.add_argument("--incoming-root", type=Path, required=True)
    composite_create.add_argument("--output", type=Path)
    composite_create.add_argument("--root", type=Path, default=Path("backups"))
    composite_verify = composite_backup_actions.add_parser("verify")
    composite_verify.add_argument("backup", type=Path)
    restore = system_actions.add_parser("restore")
    restore_actions = restore.add_subparsers(dest="subaction", required=True)
    restore_plan_parser = restore_actions.add_parser("plan")
    restore_plan_parser.add_argument("backup", type=Path)
    restore_apply_parser = restore_actions.add_parser("apply")
    restore_apply_parser.add_argument("backup", type=Path)
    restore_apply_parser.add_argument("--acknowledge-overwrite", action="store_true")
    composite_restore = restore_actions.add_parser("composite")
    composite_restore_actions = composite_restore.add_subparsers(
        dest="composite_action", required=True
    )
    for action in ("plan", "apply"):
        operation = composite_restore_actions.add_parser(action)
        operation.add_argument("backup", type=Path)
        operation.add_argument("--db-target", type=Path, required=True)
        operation.add_argument("--raw-root", type=Path, required=True)
        operation.add_argument("--incoming-root", type=Path, required=True)
        if action == "apply":
            operation.add_argument("--acknowledge-overwrite", action="store_true")
    return root


def _command(args) -> str:
    parts = [args.domain]
    for name in ("registry_domain", "action", "subaction", "composite_action"):
        value = getattr(args, name, None)
        if value:
            parts.append(value)
    return ".".join(parts)


def _operation_arguments(args) -> dict:
    excluded = {
        "db",
        "format",
        "domain",
        "registry_domain",
        "action",
        "subaction",
        "composite_action",
        "review_format",
        "diff_format",
    }
    return {key: value for key, value in vars(args).items() if key not in excluded}


def _mcp_dispatch(repository, args):
    from sgokb.mcp import MCPReadAdapter
    from sgokb.mcp.server import run_stdio

    read = runtime_factory().build_read_application(
        repository, with_semantic=args.semantic_runtime
    )
    run_stdio(MCPReadAdapter(read))
    return {"transport": "stdio", "stopped": True}


def _failure_exit(category: str) -> int:
    return {
        CATEGORY_INPUT: EXIT_INPUT,
        CATEGORY_NOT_FOUND: EXIT_NOT_FOUND,
        CATEGORY_BLOCKED: EXIT_BLOCKED,
        CATEGORY_RUNTIME: EXIT_RUNTIME,
        CATEGORY_IO: EXIT_IO,
        CATEGORY_INTEGRITY: EXIT_INTEGRITY,
    }.get(category, 1)


def _presentation_data(command: str, args, data):
    renderer = DiffReviewMarkdownRenderer()
    if command == "result.review":
        if args.review_format == "markdown":
            return renderer.render_review(data)
        return data.to_dict()
    if command == "version.diff":
        if args.diff_format == "markdown":
            return renderer.render_diff(data)
        return data.to_dict()
    return data


def main(argv=None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = parser().parse_args(argv)
    command = _command(args)
    db_path = Path(args.db)

    if command == "mcp.serve":
        repository = Repository(db_path)
        try:
            _mcp_dispatch(repository, args)
            return 0
        finally:
            repository.close()

    request = OperationRequest(command, _operation_arguments(args))
    session = OperatorSession(db_path, runtime_factory=runtime_factory())
    try:
        outcome = session.execute(request)
        data = _presentation_data(command, args, outcome.data)
        exit_code = (
            EXIT_PARTIAL
            if outcome.state == OUTCOME_PARTIAL
            else EXIT_BLOCKED
            if outcome.state == OUTCOME_BLOCKED
            else 0
        )
        return emit_success(
            command,
            data,
            warnings=outcome.warnings,
            output_format=args.format,
            exit_code=exit_code,
        )
    except OperationFailure as failure:
        return emit_error(
            command,
            failure.code,
            failure.message,
            details=failure.details,
            exit_code=_failure_exit(failure.category),
            output_format=args.format,
        )
