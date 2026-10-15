"""CLI with small, independently repeatable stages and private defaults."""

import argparse
import json
import os
import sys
from dataclasses import asdict
from pathlib import Path

import httpx

from .application import Application
from .providers import embedder_from_env
from .repository import Repository


def parser():
    root = argparse.ArgumentParser(description="Source Grounded Object Knowledge Base")
    root.add_argument("--db", default=os.environ.get("SGOKB_DB", ".local/sgokb.sqlite"))
    commands = root.add_subparsers(dest="command", required=True)
    importer = commands.add_parser(
        "import", help="Import Web Capture bundles into canonical Source/Snapshot storage"
    )
    importer.add_argument("path", type=Path)
    process = commands.add_parser(
        "process", aliases=["extract"], help="Normalize canonical Snapshots into Evidence"
    )
    process.add_argument("--snapshot")
    process.add_argument("--size", type=int, default=1000)
    process.add_argument("--overlap", type=int, default=100)
    process.add_argument("--include-auxiliary", action="store_true")
    association = commands.add_parser(
        "association", help="Maintain canonical Source↔Object associations"
    )
    association_actions = association.add_subparsers(dest="action", required=True)
    association_list = association_actions.add_parser("list")
    association_list.add_argument("--object", required=True)
    association_suggest = association_actions.add_parser(
        "suggest", help="Show read-only Source suggestions from canonical Evidence retrieval"
    )
    association_suggest.add_argument("--object", required=True)
    association_suggest.add_argument("--max-candidates", type=int, default=500)
    association_suggest.add_argument("--semantic", action="store_true")
    association_suggest.add_argument("--semantic-batch-size", type=int, default=32)
    association_set = association_actions.add_parser("set")
    association_set.add_argument("--object", required=True)
    association_set.add_argument("--source", required=True)
    association_set.add_argument(
        "--status", choices=["candidate", "confirmed", "excluded"], required=True
    )
    association_set.add_argument("--subject-relationship")
    association_set.add_argument("--note")
    association_clear = association_actions.add_parser(
        "clear", help="Remove an explicit association; does not mean excluded"
    )
    association_clear.add_argument("--object", required=True)
    association_clear.add_argument("--source", required=True)

    evidence_controls = commands.add_parser(
        "evidence", help="Inspect and manually adjust canonical Object Evidence selection"
    )
    evidence_actions = evidence_controls.add_subparsers(dest="action", required=True)
    for action in ("candidates", "select"):
        evidence_action = evidence_actions.add_parser(action)
        evidence_action.add_argument("--object", required=True)
        evidence_action.add_argument("--include-evidence", action="append", default=[])
        evidence_action.add_argument("--exclude-evidence", action="append", default=[])
        evidence_action.add_argument("--max-candidates", type=int, default=500)
        evidence_action.add_argument("--semantic", action="store_true")
        evidence_action.add_argument("--semantic-batch-size", type=int, default=32)
        if action == "select":
            evidence_action.add_argument("--max-estimated-tokens", type=int, default=12000)
            evidence_action.add_argument("--max-bytes", type=int, default=65536)
            evidence_action.add_argument("--max-items", type=int, default=64)
    provenance = commands.add_parser("provenance")
    provenance.add_argument("kind", choices=["evidence"])
    provenance.add_argument("id")
    commands.add_parser("status")
    commands.add_parser("snapshots")
    return root


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = parser().parse_args(argv)
    repository = None
    try:
        repository = Repository(args.db)
        embedder = (
            embedder_from_env()
            if (args.command == "association" and args.action == "suggest" and args.semantic)
            or (args.command == "evidence" and args.semantic)
            else None
        )
        app = Application(repository, embedder=embedder)
        result, failed = None, False
        if args.command in {"import", "process", "extract"}:
            if args.command == "import":
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
            result = []
            for target in targets:
                try:
                    if args.command == "import":
                        value = app.import_source_path(target)
                    else:
                        value = app.process_source_snapshot(
                            target, args.size, args.overlap, args.include_auxiliary
                        )
                    result.append(value)
                except Exception as error:
                    failed = True
                    result.append(
                        {"input": str(target), "error": type(error).__name__, "reason": str(error)}
                    )
        elif args.command == "association":
            if args.action == "list":
                result = app.list_source_object_associations(args.object)
            elif args.action == "suggest":
                result = app.suggest_source_associations(
                    args.object,
                    max_candidates=args.max_candidates,
                    semantic=args.semantic,
                    semantic_batch_size=args.semantic_batch_size,
                )
            elif args.action == "set":
                result = app.set_source_object_association(
                    args.object,
                    args.source,
                    args.status,
                    subject_relationship=args.subject_relationship,
                    note=args.note,
                )
            else:
                result = app.clear_source_object_association(args.object, args.source)
        elif args.command == "evidence":
            common = {
                "max_candidates": args.max_candidates,
                "semantic": args.semantic,
                "semantic_batch_size": args.semantic_batch_size,
                "manual_include": args.include_evidence,
                "manual_exclude": args.exclude_evidence,
            }
            if args.action == "candidates":
                result = app.retrieve_object_evidence(args.object, **common)
            else:
                result = app.select_object_evidence(
                    args.object,
                    max_estimated_tokens=args.max_estimated_tokens,
                    max_bytes=args.max_bytes,
                    max_items=args.max_items,
                    **common,
                )
        elif args.command == "provenance":
            result = asdict(repository.source_store.evidence_provenance(args.id))
        elif args.command == "status":
            result = repository.source_store.status()
        elif args.command == "snapshots":
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
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1 if failed else 0
    except httpx.HTTPError as error:
        print(json.dumps({"error": type(error).__name__, "reason": "Provider HTTP request failed"}))
        return 1
    except (ValueError, OSError, KeyError, json.JSONDecodeError) as error:
        print(json.dumps({"error": type(error).__name__, "reason": str(error)}, ensure_ascii=False))
        return 1
    finally:
        if repository:
            repository.close()
