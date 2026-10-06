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
    root = argparse.ArgumentParser(description="CharacterPageCollector prototype")
    root.add_argument("--db", default=os.environ.get("CPC_DB", ".local/cpc.sqlite"))
    root.add_argument("--prompt-dir", default=os.environ.get("CPC_PROMPT_DIR"))
    commands = root.add_subparsers(dest="command", required=True)
    importer = commands.add_parser(
        "import", help="Read bundles recursively; originals stay unchanged"
    )
    importer.add_argument("path", type=Path)
    process = commands.add_parser(
        "process", aliases=["extract"], help="Normalize and chunk raw snapshots"
    )
    process.add_argument("--snapshot")
    process.add_argument("--size", type=int, default=1000)
    process.add_argument("--overlap", type=int, default=100)
    process.add_argument("--include-auxiliary", action="store_true")
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
    fragment = commands.add_parser("fragment")
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
        "--transport", choices=["canonical", "compact-keys-v1"], default="canonical"
    )
    fragment.add_argument("--dedup-quotes", action="store_true")
    fragment.add_argument("--window-checkpoint", action="store_true")
    fragment.add_argument("--packer", choices=["fixed", "token"], default="fixed")
    fragment.add_argument(
        "--token-counter", choices=["utf8-upper-bound", "lmstudio"], default="utf8-upper-bound"
    )
    fragment.add_argument("--material-tokens", type=int, default=2000)
    fragment.add_argument("--context-tokens", type=int, default=16384)
    fragment.add_argument("--legacy", action="store_true")
    embed = commands.add_parser("embed")
    add_filters(embed)
    embed.add_argument("--batch-size", type=int, default=16)
    embed.add_argument("--incremental", action="store_true")
    search = commands.add_parser("search")
    search.add_argument("query")
    add_filters(search)
    search.add_argument("--limit", type=int, default=10)
    search.add_argument("--mode", choices=["hybrid", "lexical", "semantic"], default="hybrid")
    generate = commands.add_parser("generate")
    generate.add_argument("--entity", required=True)
    generate.add_argument("--query")
    generate.add_argument("--limit", type=int, default=10)
    generate.add_argument("--out", type=Path)
    generate.add_argument("--legacy", action="store_true")
    generate.add_argument("--llm-order", action="store_true")
    generate.add_argument("--batch-size", type=int, default=24)
    generate.add_argument("--max-chars", type=int, default=8000)
    generate.add_argument("--format", choices=["markdown", "json", "context"], default="markdown")
    claims = commands.add_parser("claims")
    claims.add_argument("--entity", required=True)
    experiment = commands.add_parser("claim-experiment")
    experiment.add_argument("--entity", required=True)
    experiment.add_argument("--max-claims", type=int, default=200)
    experiment.add_argument("--max-pairs", type=int, default=20)
    experiment.add_argument("--judge", action="store_true")
    compress = commands.add_parser("compression-experiment")
    compress.add_argument("--entity", required=True)
    compress.add_argument("--budget", type=int, default=12000)
    compress.add_argument("--query")
    view = commands.add_parser("view")
    view.add_argument("--entity", required=True)
    view.add_argument("--query")
    view.add_argument(
        "--mode", choices=["short", "standard", "detailed", "context"], default="short"
    )
    view.add_argument("--budget", type=int)
    view.add_argument(
        "--token-counter", choices=["utf8-upper-bound", "lmstudio"], default="utf8-upper-bound"
    )
    view.add_argument("--model", help="Loaded model for exact token counting")
    view.add_argument("--context-tokens", type=int)
    view.add_argument("--reserve-tokens", type=int, default=2048)
    view.add_argument("--out", type=Path)
    context = commands.add_parser("context")
    context.add_argument("--snapshot", required=True)
    context.add_argument(
        "--override", type=Path, help="JSON patch; creates an immutable context revision"
    )
    coverage = commands.add_parser("coverage")
    coverage.add_argument("job_id")
    benchmark = commands.add_parser("benchmark")
    benchmark.add_argument("manifest", type=Path)
    benchmark.add_argument(
        "--phase", choices=["fragment", "retrieval", "final", "all"], default="all"
    )
    benchmark.add_argument("--strategy", default="single_pass")
    benchmark.add_argument("--resume")
    score = commands.add_parser("benchmark-score", help="Score semantic human/judge labels")
    score.add_argument("labels", type=Path)
    provenance = commands.add_parser("provenance")
    provenance.add_argument("kind", choices=["evidence", "fragment", "claim", "document"])
    provenance.add_argument("id")
    commands.add_parser("status")
    commands.add_parser("snapshots")
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
    repository = None
    try:
        repository = Repository(args.db)
        llm = (
            llm_from_env("final" if args.command == "generate" else "fragment")
            if args.command in {"fragment", "benchmark"}
            or (args.command == "claim-experiment" and args.judge)
            or (args.command == "generate" and (args.legacy or args.llm_order))
            else None
        )
        embedder = (
            embedder_from_env()
            if args.command == "embed"
            or args.command == "claim-experiment"
            or (args.command == "generate" and args.legacy)
            or (args.command == "benchmark" and args.phase in {"retrieval", "all"})
            or (args.command == "search" and args.mode != "lexical")
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
                    [args.snapshot] if args.snapshot else [s["id"] for s in repository.snapshots()]
                )
            if not targets:
                raise ValueError("No input bundles or snapshots found")
            result = []
            for target in targets:
                try:
                    value = (
                        app.import_path(target)
                        if args.command == "import"
                        else app.process(target, args.size, args.overlap, args.include_auxiliary)
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
        elif args.command == "fragment":
            if args.legacy:
                result = app.fragment(args.snapshot, args.entity, args.limit, args.max_chars)
            else:
                result = app.capture_fragments(
                    args.snapshot,
                    args.entity,
                    batch_size=args.batch_size,
                    max_chars=args.max_chars,
                    strategy=args.strategy,
                    resume=args.resume,
                    transport=args.transport,
                    dedup_quotes=args.dedup_quotes,
                    window_checkpoint=args.window_checkpoint,
                    packer=args.packer,
                    token_counter=args.token_counter,
                    material_tokens=args.material_tokens,
                    context_tokens=args.context_tokens,
                )
                failed = result["status"] != "complete"
        elif args.command == "embed":
            result = app.embed(filters(args), args.batch_size, incremental=args.incremental)
        elif args.command == "claims":
            from .claims import build_claims

            result = build_claims(repository, args.entity)
        elif args.command == "claim-experiment":
            from .experiments import claim_experiment

            result = claim_experiment(app, args.entity, args.max_claims, args.max_pairs, args.judge)
        elif args.command == "compression-experiment":
            from .experiments import compression_experiment

            result = compression_experiment(repository, args.entity, args.budget, query=args.query)
        elif args.command == "view":
            from .budget import TokenCounter
            from .views import build_view

            result = build_view(
                repository,
                args.entity,
                args.budget,
                TokenCounter(args.token_counter, args.model),
                args.query,
                args.mode,
                args.context_tokens,
                args.reserve_tokens,
            )
            if args.out:
                export_markdown(args.out, result["markdown"], repository)
                export_markdown(
                    args.out.with_suffix(".omitted.json"),
                    json.dumps(result["omission_manifest"], ensure_ascii=False, indent=2),
                    repository,
                    ".json",
                )
                for field in ("markdown", "structured", "ai_context", "citations"):
                    result.pop(field, None)
                result["path"] = str(args.out)
        elif args.command == "search":
            result = app.search(args.query, filters(args), args.limit, args.mode)
        elif args.command == "generate":
            result = (
                app.generate(args.entity, args.query, args.limit)
                if args.legacy
                else app.build_document(
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
        elif args.command == "benchmark":
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
            result = repository.status()
        elif args.command == "snapshots":
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
