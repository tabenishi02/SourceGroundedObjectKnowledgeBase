"""Calibrate the judge on synthetic counterexamples, then refresh the small real-data sample."""

import argparse
import json
import os
from pathlib import Path

from jsonschema import Draft202012Validator
from run_efficiency_capture_comparison import read, runtime, write

from cpc.application import Application
from cpc.benchmark import require_local
from cpc.domain import digest, json_text
from cpc.providers import llm_from_env
from cpc.quality import quality_metrics
from cpc.reading import reading_final
from cpc.repository import Repository
from cpc.support import contract_hash, review_claim
from cpc.views import build_view


def run(args):
    out = args.out.resolve()
    if Path("sample").resolve() not in out.parents:
        raise ValueError("Probe output must be private under sample/")
    out.mkdir(parents=True, exist_ok=True)
    state_path = out / "status.json"
    if state_path.exists() and not args.resume:
        raise ValueError("Existing output requires --resume")
    state = read(state_path) if state_path.exists() else {"completed": []}
    llm = llm_from_env("fragment")
    require_local(llm)
    fixtures = read(args.fixtures)
    conditions = {
        "contract": contract_hash(),
        "implementation_hash": digest(
            json_text(
                [
                    Path(__file__).read_text(encoding="utf-8"),
                    *[
                        (Path(__file__).resolve().parents[1] / "src/cpc" / name).read_text(
                            encoding="utf-8"
                        )
                        for name in (
                            "support.py",
                            "views.py",
                            "reading.py",
                            "providers.py",
                            "quality.py",
                        )
                    ],
                ]
            )
        ),
        "fixtures": digest(json_text(fixtures)),
        "provider": llm.configuration,
        "model": llm.model,
        "revision": llm.revision,
        "runtime": runtime() if llm.configuration.get("adapter", "").startswith("strata") else None,
    }
    frozen = out / "conditions.json"
    if frozen.exists() and read(frozen) != conditions:
        raise ValueError("Probe conditions changed")
    write(frozen, conditions)
    state.update(status="running", pid=os.getpid())
    write(state_path, state)
    repo = Repository(args.db)
    app = Application(repo, llm)
    schema = read(app.prompt_dir / "support_review.schema.json")

    def phase(key, operation):
        if key in state["completed"]:
            return read(out / (key + ".json"))
        state["current"] = key
        write(state_path, state)
        result = operation()
        write(out / (key + ".json"), result)
        state["completed"].append(key)
        write(state_path, state)
        return result

    try:
        labels = []
        for fixture in fixtures:
            payload = {
                "audit": {
                    "claim": {
                        "text": fixture["text"],
                        "subject": "対象A",
                        "epistemic_type": fixture["epistemic_type"],
                        "asserted_by": "article_author",
                    },
                    "supports": [
                        {
                            "quote": fixture["quote"],
                            "quote_present": True,
                            "evidence": [
                                {
                                    "context": fixture["quote"],
                                    "url": "https://example.test/target-A",
                                }
                            ],
                        }
                    ],
                }
            }

            def judge():
                ai_id, _, verdict = app.call_llm("support_probe", "support_review", payload)
                try:
                    Draft202012Validator(schema).validate(verdict)
                except Exception:
                    raw = repo.one("SELECT output FROM ai_runs WHERE id=?", (ai_id,))["output"]
                    repo.finish_ai(ai_id, output=raw, error="InvalidSupportVerdict")
                    raise
                return {**verdict, "ai_run": ai_id}

            result = phase(fixture["id"], judge)
            labels.append(
                {
                    "expected": fixture["expected"],
                    "actual": result["verdict"],
                    "label_channel": "curated_fixture",
                }
            )
        quality = quality_metrics(labels)
        real = []
        for path in sorted(args.previous.glob("review-*.json")):
            record = read(path)
            ai = repo.one("SELECT input FROM ai_runs WHERE id=?", (record["ai_run"],))
            claim = json.loads(ai["input"])["payload"]["audit"]["claim"]
            result = phase("real-" + claim["id"], lambda: review_claim(app, claim))
            real.append({"claim_id": claim["id"], **result})
        for n, entity in enumerate(repo.entities()):
            if not repo.related_fragments(entity["id"]):
                continue
            for mode in ("short", "standard", "detailed"):
                result = phase(
                    f"entity-{n}-{mode}",
                    lambda mode=mode: build_view(repo, entity["id"], mode=mode),
                )
                (out / f"entity-{n}-{mode}.md").write_text(result["markdown"], encoding="utf-8")
            phase(f"entity-{n}-reading", lambda: reading_final(repo, entity["id"]))
            phase(
                f"entity-{n}-verified", lambda: build_view(repo, entity["id"], supported_only=True)
            )
        after = digest(json_text(repo.rows("SELECT * FROM fragments ORDER BY id")))
        baseline = read(args.previous / "fragment-baseline.json")["hash"]
        if after != baseline or repo.rows("PRAGMA foreign_key_check"):
            raise ValueError("Fragment preservation check failed")
        report = {
            "quality": quality,
            "real_reviews": real,
            "fragment_unchanged": True,
            "integrity": repo.one("PRAGMA integrity_check")["integrity_check"],
        }
        if report["integrity"] != "ok":
            raise ValueError("Probe database integrity check failed")
        write(out / "report.json", report)
        state.update(status="completed", current=None)
    except Exception as error:
        state.update(status="failed", error=type(error).__name__)
        raise
    finally:
        write(state_path, state)
        repo.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--previous", type=Path, default=Path("sample/pipeline-improvement-evaluation")
    )
    parser.add_argument(
        "--db", type=Path, default=Path("sample/pipeline-improvement-evaluation/captures.sqlite")
    )
    parser.add_argument("--out", type=Path, default=Path("sample/pipeline-support-probes"))
    parser.add_argument("--fixtures", type=Path, default=Path("benchmark/support-probes-v1.json"))
    parser.add_argument("--resume", action="store_true")
    run(parser.parse_args())
