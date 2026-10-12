"""Dedicated Phase G CLI for local Package staging and explicit external export."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from .exchange.package_transfer import PackageTransferService, _load_manifest
from .repository import Repository
from .storage import PackageExchangeAuditRepository


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description="SGOKB Object Evidence Package transfer")
    root.add_argument("--db", default=os.environ.get("SGOKB_DB", ".local/sgokb.sqlite"))
    actions = root.add_subparsers(dest="action", required=True)

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

    export = actions.add_parser("export", help="Explicitly copy a staged Package to an external root")
    export.add_argument("package", type=Path)
    export.add_argument("--destination", type=Path, required=True)
    export.add_argument(
        "--acknowledge-review",
        action="store_true",
        help="Explicitly approve a review_required Package for this export",
    )
    return root


def main(argv=None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = parser().parse_args(argv)
    service = PackageTransferService()
    repository = None
    try:
        if args.action == "preflight":
            result = service.preflight(args.package, args.destination).to_dict()
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 1 if result["disposition"] == "blocked" else 0

        repository = Repository(args.db)
        audit = PackageExchangeAuditRepository(repository.db)
        if args.action == "stage":
            staged = service.stage_from_directory(args.source, args.staging_root)
            manifest = _load_manifest(Path(staged.path))
            audit.record_staged(manifest, staged.path, staged.preflight.to_dict())
            result = staged.to_dict()
        else:
            exported = service.export(
                args.package,
                args.destination,
                acknowledge_review=args.acknowledge_review,
            )
            manifest = _load_manifest(Path(args.package).resolve())
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
        print(json.dumps(result, ensure_ascii=False, indent=2))
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
