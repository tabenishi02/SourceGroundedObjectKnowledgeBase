"""Opt-in private real-sample evaluation, resumable independently of a Codex session."""

import argparse
import collections
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cpc.application import Application  # noqa: E402
from cpc.cli import export_markdown  # noqa: E402
from cpc.domain import SearchFilter, digest, now  # noqa: E402
from cpc.providers import embedder_from_env, llm_from_env  # noqa: E402
from cpc.repository import Repository  # noqa: E402


def write_report(path, report):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


def evaluate(args):
    repo = Repository(args.db)
    report_path = Path(args.report)
    report = (
        json.loads(report_path.read_text(encoding="utf-8"))
        if report_path.exists()
        else {"started_at": now(), "samples": [], "ai": [], "documents": []}
    )
    report["status"] = "running"
    write_report(report_path, report)
    app = Application(repo)
    try:
        if args.phase in {"deterministic", "all"}:
            report["samples"] = []
            for path in sorted(Path(args.sample).rglob("*.webcapture.zip")):
                before = digest(path.read_bytes()), path.stat().st_mtime_ns
                result = {"file": str(path), "raw_sha256": before[0]}
                try:
                    imported = app.import_path(path)
                    result.update(imported)
                    snapshot = repo.snapshot(imported["snapshot"])
                    result["site"] = snapshot["site"]
                    result["source_type"] = snapshot["source_type"]
                    if not snapshot["active_run"] or args.reprocess:
                        result.update(app.process(snapshot["id"]))
                    else:
                        result["evidence"] = len(repo.evidence(snapshot["id"]))
                    result["lexical_hits"] = len(
                        app.search(
                            repo.evidence(snapshot["id"])[0]["content"][:10],
                            SearchFilter(snapshot=snapshot["id"]),
                            mode="lexical",
                        )
                    )
                    result["status"] = "success"
                except Exception as error:
                    result.update(status="failed", error=type(error).__name__, reason=str(error))
                result["raw_unchanged"] = before == (
                    digest(path.read_bytes()),
                    path.stat().st_mtime_ns,
                )
                report["samples"].append(result)
                write_report(report_path, report)
        if args.phase in {"ai", "all"}:
            for stage in ("ai", "documents"):
                report.setdefault("previous_attempts", []).extend(
                    dict(row, stage=stage)
                    for row in report[stage]
                    if row.get("status") in {"failed", "empty"}
                )
                report[stage] = [
                    row for row in report[stage] if row.get("status") not in {"failed", "empty"}
                ]
            app.llm, app.embedder = llm_from_env("fragment"), embedder_from_env()
            report["models"] = {
                "llm": app.llm.model,
                "llm_revision": app.llm.revision,
                "embedding": app.embedder.model,
                "embedding_revision": app.embedder.revision,
                "embedding_configuration": app.embedder.configuration,
            }
            character = repo.add_entity("Character", "櫻木真乃")
            work = repo.add_entity(
                "Work",
                "アイドルマスター シャイニーカラーズ",
                ["アイドルマスターシャイニーカラーズ"],
            )
            repo.relate(character, "appears_in", work)
            snapshots = repo.snapshots()

            def priority(s):
                if "櫻木真乃" in s["title"]:
                    return 0
                if "シャイニーカラーズ" in s["title"]:
                    return 1
                return 2

            preferred = [
                "dic.pixiv.net",
                "w.atwiki.jp",
                "dic.nicovideo.jp",
                "ja.wikipedia.org",
                "shinycolors.idolmaster-official.jp",
            ]

            def order(s):
                return (preferred.index(s["site"]) if s["site"] in preferred else 99, s["id"])

            characters = sorted([s for s in snapshots if priority(s) == 0], key=order)
            works = sorted([s for s in snapshots if priority(s) == 1], key=order)
            selected = (
                characters[: args.ai_limit // 2] + works[: args.ai_limit - args.ai_limit // 2]
            )
            completed = {
                (r["snapshot"], r["entity"])
                for r in report["ai"]
                if r.get("status") == "success" and r.get("fragments", 0)
            }
            for snapshot in selected:
                if not snapshot["active_run"]:
                    continue
                if "櫻木真乃" in snapshot["title"]:
                    entity_id = character
                elif "シャイニーカラーズ" in snapshot["title"]:
                    entity_id = work
                else:
                    entity_id = repo.add_entity("Concept", snapshot["title"].split(" - ")[0][:160])
                if (snapshot["id"], entity_id) in completed and not args.reprocess:
                    continue
                result = {"snapshot": snapshot["id"], "entity": entity_id, "site": snapshot["site"]}
                try:
                    result.update(app.fragment(snapshot["id"], entity_id, limit=3, max_chars=3000))
                    result["status"] = "success" if result["fragments"] else "empty"
                except Exception as error:
                    result.update(status="failed", error=type(error).__name__, reason=str(error))
                report["ai"].append(result)
                write_report(report_path, report)
            report["embedding"] = app.embed(batch_size=args.batch_size)
            write_report(report_path, report)
            app.llm = llm_from_env("final")
            for entity_id in (character, work):
                result = {"entity": entity_id}
                try:
                    name = repo.entity(entity_id)["name"]
                    report.setdefault("searches", []).append(
                        {
                            "entity": entity_id,
                            "lexical": len(app.search(name, mode="lexical")),
                            "semantic": len(app.search(name + "の特徴", mode="semantic")),
                            "hybrid_filtered": len(
                                app.search(name, SearchFilter(entity=entity_id))
                            ),
                        }
                    )
                    generated = app.generate(entity_id, limit=5)
                    output = Path(".local/documents") / (generated["document_id"] + ".md")
                    export_markdown(output, generated.pop("markdown"), repo)
                    result.update(generated, path=str(output), status="success")
                    citations = json.loads(repo.document(generated["document_id"])["citations"])
                    result["provenance_verified"] = all(
                        digest(Path(e["raw_path"]).read_bytes()) == e["raw_sha256"]
                        for c in citations.values()
                        for e in c["evidence"]
                    )
                except Exception as error:
                    result.update(status="failed", error=type(error).__name__, reason=str(error))
                report["documents"].append(result)
                write_report(report_path, report)
        report["database"] = repo.status()
        report["sites"] = dict(collections.Counter(r.get("site") for r in report["samples"]))
        report["finished_at"] = now()
        report["status"] = (
            "completed_with_failures"
            if any(
                r.get("status") == "failed"
                for key in ("samples", "ai", "documents")
                for r in report[key]
            )
            else "completed"
        )
    except Exception as error:
        report.update(status="failed", error=type(error).__name__, reason=str(error))
        raise
    finally:
        write_report(report_path, report)
        repo.close()
    print(
        json.dumps(
            {
                "status": report["status"],
                "samples": len(report["samples"]),
                "ai": len(report["ai"]),
                "documents": len(report["documents"]),
                "database": report["database"],
            },
            ensure_ascii=False,
        )
    )
    return 0 if report["status"] == "completed" else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=["deterministic", "ai", "all"], default="all")
    parser.add_argument("--sample", default="sample")
    parser.add_argument("--db", default=".local/evaluation.sqlite")
    parser.add_argument("--report", default=".local/evaluation.json")
    parser.add_argument("--ai-limit", type=int, default=8)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--reprocess", action="store_true")
    raise SystemExit(evaluate(parser.parse_args()))
