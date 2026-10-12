"""CLI with small, independently repeatable stages and private defaults."""

import argparse
import json
import os
import sys
from pathlib import Path

import httpx

from .application import Application
from .domain import SearchFilter
from .providers import embedder_from_env, llm_from_env
from .repository import Repository


def add_filters(parser):
    for name in ("entity", "source", "snapshot", "site", "source-type", "facet"):
        parser.add_argument("--" + name)


def filters(args):
    return SearchFilter(**{k: getattr(args, k, None) for k in SearchFilter.__dataclass_fields__})


def parser():
    root = argparse.ArgumentParser(description="Source Grounded Object Knowledge Base")
    root.add_argument("--db", default=os.environ.get("SGOKB_DB", ".local/sgokb.sqlite"))
    root.add_argument("--prompt-dir", default=os.environ.get("SGOKB_PROMPT_DIR"))
    commands = root.add_subparsers(dest="command", required=True)
    importer = commands.add_parser(
        "import", help="Import Web Capture bundles into canonical Source/Snapshot storage"
    )
    importer.add_argument("path", type=Path)
    importer.add_argument("--legacy", action="store_true", help="Use Prototype legacy tables")
    process = commands.add_parser(
        "process", aliases=["extract"], help="Normalize canonical Snapshots into Evidence"
    )
    process.add_argument("--snapshot")
    process.add_argument("--size", type=int, default=1000)
    process.add_argument("--overlap", type=int, default=100)
    process.add_argument("--include-auxiliary", action="store_true")
    process.add_argument("--legacy", action="store_true", help="Use Prototype legacy tables")
    entity = commands.add_parser("entity")
    actions = entity.add_subparsers(dest="action", required=True)
    add = actions.add_parser("add")
    add.add_argument("type")
    add.add_argument("name")
    add.add_argument("--alias", action="append", default=[])
    actions.add_parser("list")
    relate = actions.add_parser("relate")
    relate.add_argument("subject")
    relate.add_argument("predicate")
    relate.add_argument("object")
    link = actions.add_parser("link", help="Explicitly associate an entity with snapshot evidence")
    link.add_argument("entity_id")
    link.add_argument("snapshot_id")
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
    fragment = commands.add_parser(
        "legacy-fragment",
        aliases=["fragment"],
        help="Legacy/research Fragment generation; excluded from the standard pipeline",
    )
    fragment.add_argument("--snapshot", required=True)
    fragment.add_argument("--entity", required=True)
    fragment.add_argument("--limit", type=int, default=6)
    fragment.add_argument("--max-chars", type=int, default=6000)
    fragment.add_argument("--batch-size", type=int, default=4)
    fragment.add_argument(
        "--strategy",
        choices=["single_pass", "high_recall_multi_pass", "extract_review"],
        default="single_pass",
    )
    fragment.add_argument("--resume")
    fragment.add_argument(
        "--classic",
        "--legacy",
        dest="classic",
        action="store_true",
        help="Use the oldest single-pass Fragment extractor",
    )
    embed = commands.add_parser("embed")
    add_filters(embed)
    embed.add_argument("--batch-size", type=int, default=16)
    search = commands.add_parser("search")
    search.add_argument("query")
    add_filters(search)
    search.add_argument("--limit", type=int, default=10)
    search.add_argument("--mode", choices=["hybrid", "lexical", "semantic"], default="hybrid")
    generate = commands.add_parser(
        "legacy-generate",
        aliases=["generate"],
        help="Legacy Fragment-based document generation; excluded from the standard pipeline",
    )
    generate.add_argument("--entity", required=True)
    generate.add_argument("--query")
    generate.add_argument("--limit", type=int, default=10)
    generate.add_argument("--out", type=Path)
    generate.add_argument(
        "--prototype-final",
        "--legacy",
        dest="prototype_final",
        action="store_true",
        help="Use the oldest Fragment search + Final Document implementation",
    )
    generate.add_argument("--llm-order", action="store_true")
    generate.add_argument("--batch-size", type=int, default=24)
    generate.add_argument("--max-chars", type=int, default=8000)
    generate.add_argument("--format", choices=["markdown", "json", "context"], default="markdown")
    context = commands.add_parser("context")
    context.add_argument("--snapshot", required=True)
    context.add_argument(
        "--override", type=Path, help="JSON patch; creates an immutable context revision"
    )
    coverage = commands.add_parser("coverage")
    coverage.add_argument("job_id")
    benchmark = commands.add_parser(
        "legacy-benchmark",
        aliases=["benchmark"],
        help="Legacy Fragment/Final benchmark; research compatibility only",
    )
    benchmark.add_argument("manifest", type=Path)
    benchmark.add_argument(
        "--phase", choices=["fragment", "retrieval", "final", "all"], default="all"
    )
    benchmark.add_argument("--strategy", default="single_pass")
    benchmark.add_argument("--resume")
    score = commands.add_parser("benchmark-score", help="Score semantic human/judge labels")
    score.add_argument("labels", type=Path)
    provenance = commands.add_parser("provenance")
    provenance.add_argument("kind", choices=["evidence", "fragment", "document"])
    provenance.add_argument("id")
    status = commands.add_parser("status")
    status.add_argument("--legacy", action="store_true", help="Show Prototype legacy counts")
    snapshots = commands.add_parser("snapshots")
    snapshots.add_argument("--legacy", action="store_true", help="List Prototype legacy snapshots")
    return root


def export_markdown(path, markdown, repository, suffix=".md"):
    path = path.resolve()
    sample = Path("sample").resolve()
    raw_paths = {Path(s["raw_path"]).resolve() for s in repository.snapshots()}
    if path in raw_paths or sample in path.parents or path.name.endswith(".webcapture.zip"):
        raise ValueError("Refusing to overwrite Raw Capture or sample directory")
    if path.suffix.lower() != suffix:
        raise ValueError("Document export requires a " + suffix + " path")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(markdown, encoding="utf-8")
    temporary.replace(path)


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = parser().parse_args(argv)
    args.command = {
        "fragment": "legacy-fragment",
        "generate": "legacy-generate",
        "benchmark": "legacy-benchmark",
    }.get(args.command, args.command)
    repository = None
    try:
        repository = Repository(args.db)
        llm = (
            llm_from_env("final" if args.command == "legacy-generate" else "fragment")
            if args.command in {"legacy-fragment", "legacy-benchmark"}
            or (args.command == "legacy-generate" and (args.prototype_final or args.llm_order))
            else None
        )
        embedder = (
            embedder_from_env()
            if args.command == "embed"
            or (args.command == "legacy-generate" and args.prototype_final)
            or (args.command == "legacy-benchmark" and args.phase in {"retrieval", "all"})
            or (args.command == "search" and args.mode != "lexical")
            or (args.command == "association" and args.action == "suggest" and args.semantic)
            or (args.command == "evidence" and args.semantic)
            else None
        )
        app = Application(repository, llm, embedder, prompt_dir=args.prompt_dir)
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
                    else (
                        [s["id"] for s in repository.snapshots()]
                        if args.legacy
                        else [s.snapshot_id for s in repository.source_store.snapshots()]
                    )
                )
            if not targets:
                raise ValueError("No input bundles or snapshots found")
            result = []
            for target in targets:
                try:
                    if args.command == "import":
                        value = (
                            app.import_path(target)
                            if args.legacy
                            else app.import_source_path(target)
                        )
                    else:
                        value = (
                            app.process(target, args.size, args.overlap, args.include_auxiliary)
                            if args.legacy
                            else app.process_source_snapshot(
                                target, args.size, args.overlap, args.include_auxiliary
                            )
                        )
                    result.append(value)
                except Exception as error:
                    failed = True
                    result.append(
                        {"input": str(target), "error": type(error).__name__, "reason": str(error)}
                    )
        elif args.command == "entity":
            if args.action == "add":
                result = {"entity": repository.add_entity(args.type, args.name, args.alias)}
            elif args.action == "list":
                result = repository.entities()
            elif args.action == "relate":
                repository.relate(args.subject, args.predicate, args.object)
                result = {"related": True}
            else:
                repository.entity(args.entity_id)
                evidence = repository.evidence(args.snapshot_id)
                if not evidence:
                    raise ValueError("No processed evidence for this snapshot")
                repository.link_evidence(args.entity_id, [e["id"] for e in evidence])
                result = {"linked": len(evidence)}
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
        elif args.command == "legacy-fragment":
            if args.classic:
                result = app.legacy_fragment(args.snapshot, args.entity, args.limit, args.max_chars)
            else:
                result = app.legacy_capture_fragments(
                    args.snapshot,
                    args.entity,
                    batch_size=args.batch_size,
                    max_chars=args.max_chars,
                    strategy=args.strategy,
                    resume=args.resume,
                )
                failed = result["status"] != "complete"
        elif args.command == "embed":
            result = app.embed(filters(args), args.batch_size)
        elif args.command == "search":
            result = app.search(args.query, filters(args), args.limit, args.mode)
        elif args.command == "legacy-generate":
            result = (
                app.legacy_generate(args.entity, args.query, args.limit)
                if args.prototype_final
                else app.legacy_build_document(
                    args.entity,
                    use_llm=args.llm_order,
                    batch_size=args.batch_size,
                    max_chars=args.max_chars,
                    query=args.query,
                )
            )
            if args.out:
                key = {"markdown": "markdown", "json": "structured", "context": "ai_context"}[
                    args.format
                ]
                value = result[key]
                export_markdown(
                    args.out,
                    json.dumps(value, ensure_ascii=False, indent=2)
                    if isinstance(value, dict)
                    else value,
                    repository,
                    {"markdown": ".md", "json": ".json", "context": ".txt"}[args.format],
                )
                for field in ("markdown", "structured", "ai_context"):
                    result.pop(field, None)
                result["path"] = str(args.out)
        elif args.command == "context":
            snapshot = repository.snapshot(args.snapshot)
            if not snapshot or not snapshot["active_run"]:
                raise ValueError("Process snapshot first")
            result = (
                repository.revise_context(
                    snapshot["active_run"],
                    overrides=json.loads(args.override.read_text(encoding="utf-8")),
                )
                if args.override
                else repository.page_context(snapshot["active_run"])
            )
        elif args.command == "coverage":
            result = repository.coverage(args.job_id)
        elif args.command == "legacy-benchmark":
            from .benchmark import run_benchmark

            result = run_benchmark(app, args.manifest, args.phase, args.strategy, args.resume)
            failed = result["status"] != "complete"
        elif args.command == "benchmark-score":
            from .benchmark import judgement_metrics

            result = judgement_metrics(json.loads(args.labels.read_text(encoding="utf-8")))
        elif args.command == "provenance":
            if args.kind == "document":
                document = repository.document(args.id)
                if not document:
                    raise ValueError("Unknown document ID")
                result = json.loads(document["citations"])
            else:
                result = repository.provenance(args.kind, args.id)
        elif args.command == "status":
            result = repository.status() if args.legacy else repository.source_store.status()
        elif args.command == "snapshots":
            if args.legacy:
                result = [
                    {
                        k: s[k]
                        for k in (
                            "id",
                            "source_id",
                            "site",
                            "source_type",
                            "title",
                            "captured_at",
                            "active_run",
                        )
                    }
                    for s in repository.snapshots()
                ]
            else:
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
