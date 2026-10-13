"""Dedicated Phase G CLI for Package build, transfer, and Result receipt."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from .exchange.package_builder import DEFAULT_BUILD_ROOT, ObjectEvidencePackageBuilder
from .exchange.package_transfer import PackageTransferService
from .exchange.result_import import ObjectVersionImportService
from .exchange.result_receipt import DEFAULT_INCOMING_ROOT, ResultReceiptService
from .exchange.result_validation import ResultValidationService
from .rendering import DEFAULT_RENDER_ROOT, MarkdownRenderService
from .repository import Repository
from .storage import PackageExchangeAuditRepository


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description="SGOKB Object Evidence Package exchange")
    root.add_argument("--db", default=os.environ.get("SGOKB_DB", ".local/sgokb.sqlite"))
    actions = root.add_subparsers(dest="action", required=True)

    build = actions.add_parser(
        "build", help="Build one Object Evidence Package workspace from canonical storage"
    )
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

    stage = actions.add_parser("stage", help="Finalize a local Package build into staging")
    stage.add_argument("source", type=Path, help="Package build directory containing manifest.json")
    stage.add_argument(
        "--staging-root",
        type=Path,
        default=Path(os.environ.get("SGOKB_EXCHANGE_STAGING", "exchange/staging")),
    )

    preflight = actions.add_parser("preflight", help="Verify a staged Package before export")
    preflight.add_argument("package", type=Path)
    preflight.add_argument("--destination", type=Path)

    export = actions.add_parser(
        "export", help="Explicitly copy a staged Package to an external root"
    )
    export.add_argument("package", type=Path)
    export.add_argument("--destination", type=Path, required=True)
    export.add_argument(
        "--acknowledge-review",
        action="store_true",
        help="Explicitly approve a review_required Package for this export",
    )

    incoming_default = Path(os.environ.get("SGOKB_EXCHANGE_INCOMING", DEFAULT_INCOMING_ROOT))
    detect = actions.add_parser(
        "detect",
        help="List manually returned drop/<package_id>/result.json files without receiving them",
    )
    detect.add_argument("--incoming-root", type=Path, default=incoming_default)

    receive = actions.add_parser(
        "receive",
        help="Copy one result.json into an immutable local receipt and request validation",
    )
    receive.add_argument("result", type=Path)
    receive.add_argument("--package-id", required=True)
    receive.add_argument("--incoming-root", type=Path, default=incoming_default)

    receipts = actions.add_parser("receipts", help="List received Result artifacts")
    receipts.add_argument("--package-id")

    actions.add_parser(
        "pending-validation",
        help="List Result receipts waiting for the Phase H validator",
    )
    validate_result = actions.add_parser(
        "validate-result",
        help="Run the Phase H deterministic validator for one immutable Result receipt",
    )
    validate_result.add_argument("receipt_id")
    validate_result.add_argument("--incoming-root", type=Path, default=incoming_default)
    validate_result.add_argument("--force", action="store_true")

    import_result = actions.add_parser(
        "import-result",
        help="Explicitly import one H-01-valid Result receipt as a new accepted Object Version",
    )
    import_result.add_argument("receipt_id")
    import_result.add_argument("--incoming-root", type=Path, default=incoming_default)
    import_result.add_argument(
        "--acknowledge-review",
        action="store_true",
        help="Explicitly approve review-required Result findings for this import",
    )

    render_markdown = actions.add_parser(
        "render-markdown",
        help="Render one accepted Object Version as derived human-readable Markdown",
    )
    target = render_markdown.add_mutually_exclusive_group(required=True)
    target.add_argument("--version", help="Accepted Object Version ID to render")
    target.add_argument("--object", help="Render the Object's current accepted Version")
    render_markdown.add_argument(
        "--output-root",
        type=Path,
        default=Path(os.environ.get("SGOKB_RENDER_ROOT", DEFAULT_RENDER_ROOT)),
    )
    return root


def _manifest(path: Path) -> dict:
    return json.loads((path / "manifest.json").read_text(encoding="utf-8"))


def main(argv=None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = parser().parse_args(argv)
    transfer = PackageTransferService()
    repository = None
    try:
        if args.action == "preflight":
            result = transfer.preflight(args.package, args.destination).to_dict()
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 1 if result["disposition"] == "blocked" else 0

        repository = Repository(args.db)
        audit = PackageExchangeAuditRepository(repository.db)
        receipt_service = ResultReceiptService(audit)

        if args.action == "build":
            result = (
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
        elif args.action == "stage":
            staged = transfer.stage_from_directory(args.source, args.staging_root)
            manifest = _manifest(Path(staged.path))
            audit.record_staged(manifest, staged.path, staged.preflight.to_dict())
            result = staged.to_dict()
        elif args.action == "export":
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
        elif args.action == "detect":
            result = [item.to_dict() for item in receipt_service.detect(args.incoming_root)]
        elif args.action == "receive":
            result = receipt_service.receive(
                args.result,
                args.package_id,
                args.incoming_root,
            ).to_dict()
        elif args.action == "receipts":
            result = list(audit.result_receipts(args.package_id))
        elif args.action == "validate-result":
            report = ResultValidationService(repository, audit).validate_receipt(
                args.receipt_id,
                incoming_root=args.incoming_root,
                force=args.force,
            )
            result = report.to_dict()
        elif args.action == "import-result":
            result = (
                ObjectVersionImportService(repository, audit)
                .import_receipt(
                    args.receipt_id,
                    incoming_root=args.incoming_root,
                    acknowledge_review=args.acknowledge_review,
                )
                .to_dict()
            )
        elif args.action == "render-markdown":
            version_id = args.version
            if version_id is None:
                version_id = repository.version_store.current_version_id(args.object)
                if version_id is None:
                    raise ValueError("Object has no current accepted Version to render")
            result = (
                MarkdownRenderService(repository)
                .render_version(
                    version_id,
                    output_root=args.output_root,
                )
                .to_dict()
            )
        else:
            result = list(audit.pending_result_receipts())

        print(json.dumps(result, ensure_ascii=False, indent=2))
        if args.action == "validate-result" and result["validation_state"] != "valid":
            return 1
        return 0
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(
            json.dumps(
                {"error": type(error).__name__, "reason": str(error)},
                ensure_ascii=False,
            )
        )
        return 1
    finally:
        if repository is not None:
            repository.close()


if __name__ == "__main__":
    raise SystemExit(main())
