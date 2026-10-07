import copy
import json
import sqlite3
from argparse import Namespace
from pathlib import Path

import httpx
import pytest
from test_upgrade import grounded

from cpc.claims import build_claims
from cpc.providers import CompatibleLLM
from cpc.quality import quality_metrics, speed_metrics
from cpc.reading import reading_final
from cpc.support import audit_claim, latest_review, quote_span, review_claim
from cpc.views import build_view


class Judge:
    model, revision, configuration = "test-judge", "1", {}

    def __init__(self, verdict="supported"):
        self.verdict, self.calls = verdict, 0

    def complete(self, prompt, payload, *, schema=None):
        self.calls += 1
        assert schema and "untrusted" in prompt
        return json.dumps({"verdict": self.verdict, "reason": "Controlled semantic verdict"})


def prepared(core):
    app, repo, snapshot, entity = grounded(core)
    app.capture_fragments(snapshot, entity, batch_size=1)
    app.llm = Judge()
    return app, repo, entity, build_claims(repo, entity)["claims"]


def test_quote_coordinates_preserve_unicode_and_whitespace():
    text = "前文\n真乃 は 穏やか。後文"
    span = quote_span(text, "真乃は穏やか。")
    assert text[span[0] : span[1]] == "真乃 は 穏やか。"
    assert quote_span(text, "常にポジティブ") is None
    assert quote_span(text, " ") is None


def test_review_gate_cache_and_input_invalidation_preserve_fragments(core):
    app, repo, entity, claims = prepared(core)
    before = copy.deepcopy(repo.related_fragments(entity))
    initial = build_view(repo, entity, supported_only=True)
    assert not initial["structured"]["claims"]
    result = review_claim(app, claims[0])
    assert result["verdict"] == "supported" and app.llm.calls == 1
    assert review_claim(app, claims[0])["cached"] and app.llm.calls == 1
    verified = build_view(repo, entity, supported_only=True)
    assert verified["structured"]["selected_claim_ids"] == [claims[0]["id"]]
    assert verified["audit_manifest"]["[S1]"]["audit"]["supports"][0]["quote_present"]
    assert any("https://example.test" in ref for ref in verified["citations"][claims[0]["id"]])
    changed = {**claims[0], "text": "An unsupported new assertion"}
    assert latest_review(repo, audit_claim(repo, changed))["verdict"] == "unreviewed"
    app.llm.verdict = "unsupported"
    assert review_claim(app, changed)["verdict"] == "unsupported"
    assert repo.related_fragments(entity) == before


@pytest.mark.parametrize("missing_quote", ["Quote absent from Evidence", None])
def test_missing_quote_and_oversize_review_never_call_provider(core, missing_quote):
    app, repo, _, claims = prepared(core)
    fragment_id = claims[0]["fragment_ids"][0]
    metadata = json.loads(
        repo.one("SELECT metadata FROM fragments WHERE id=?", (fragment_id,))["metadata"]
    )
    metadata["original_text"] = missing_quote
    repo.db.execute(
        "UPDATE fragments SET metadata=? WHERE id=?", (json.dumps(metadata), fragment_id)
    )
    assert review_claim(app, claims[0])["verdict"] == "unsupported"
    assert review_claim(app, claims[1], max_chars=1)["verdict"] in {"unsupported", "uncertain"}
    assert app.llm.calls == 0


def test_reading_copy_keeps_all_claims_and_traceable_shared_sources(core):
    _, repo, entity, claims = prepared(core)
    result = reading_final(repo, entity)
    assert result["claim_count"] == len(claims)
    assert len(result["audit_manifest"]) == len(claims)
    assert len(result["sources"]) < len(claims)
    for claim in claims:
        assert claim["text"] in result["markdown"]
    assert "支持判定: unreviewed" in result["markdown"]
    assert not repo.rows("PRAGMA foreign_key_check")


@pytest.mark.parametrize("status,count", [(503, 3), (429, 3), (400, 1), (502, 1)])
def test_http_retries_are_bounded_and_classified(status, count, monkeypatch):
    monkeypatch.setattr("cpc.providers.time.sleep", lambda _: None)
    attempts = []

    def handle(request):
        attempts.append(request)
        return httpx.Response(status, json={"error": "controlled"})

    llm = CompatibleLLM("http://localhost/v1", "test", transport=httpx.MockTransport(handle))
    with pytest.raises(httpx.HTTPStatusError):
        llm.complete("", {})
    assert len(attempts) == count
    assert len(llm.last_observation["attempts"]) == count


def test_read_timeout_does_not_duplicate_generation():
    attempts = []

    def handle(request):
        attempts.append(request)
        raise httpx.ReadTimeout("controlled", request=request)

    llm = CompatibleLLM("http://localhost/v1", "test", transport=httpx.MockTransport(handle))
    with pytest.raises(httpx.ReadTimeout):
        llm.complete("", {})
    assert len(attempts) == 1


def test_connect_failure_stops_at_three_attempts(monkeypatch):
    monkeypatch.setattr("cpc.providers.time.sleep", lambda _: None)
    attempts = []

    def handle(request):
        attempts.append(request)
        raise httpx.ConnectError("controlled", request=request)

    llm = CompatibleLLM("http://localhost/v1", "test", transport=httpx.MockTransport(handle))
    with pytest.raises(httpx.ConnectError):
        llm.complete("", {})
    assert len(attempts) == 3
    assert llm.last_observation["attempts"][-1]["failure"] == "ConnectError"


def test_quality_and_speed_do_not_claim_human_gold_or_use_failures():
    quality = quality_metrics(
        [{"expected": "unsupported", "actual": "supported", "label_channel": "curated_fixture"}]
    )
    assert quality["false_supported"] == 1 and not quality["human_gold"]
    speed = speed_metrics(
        [
            {"phase": "warmup", "success": True, "duration_seconds": 90},
            {"phase": "warm", "success": False, "duration_seconds": 100},
            {"phase": "warm", "success": True, "cached": True, "duration_seconds": 0},
            {"phase": "warm", "success": True, "preflight": True, "duration_seconds": 0},
            {"phase": "warm", "success": True, "duration_seconds": 2},
        ]
    )
    assert speed["median_seconds"] == 2 and speed["warm_successes"] == 1


def test_invalid_judge_response_does_not_create_a_supported_record(core):
    app, repo, _, claims = prepared(core)

    class Invalid(Judge):
        def complete(self, prompt, payload, *, schema=None):
            return '{"verdict":"supported","reason":"ok","rewritten_text":"new claim"}'

    app.llm = Invalid()
    with pytest.raises(ValueError, match="Invalid support review"):
        review_claim(app, claims[0])
    assert latest_review(repo, audit_claim(repo, claims[0]))["verdict"] == "unreviewed"
    failed = repo.one("SELECT output FROM ai_runs WHERE error='InvalidSupportVerdict'")
    assert "rewritten_text" in failed["output"]


def test_custom_prompt_change_invalidates_visible_reviews(core, tmp_path):
    app, repo, _, claims = prepared(core)
    review_claim(app, claims[0])
    import shutil

    shutil.copytree(app.prompt_dir, tmp_path / "prompts")
    prompt = tmp_path / "prompts/support_review.md"
    prompt.write_text(prompt.read_text(encoding="utf-8") + "\nChanged policy", encoding="utf-8")
    assert (
        latest_review(repo, audit_claim(repo, claims[0]), prompt.parent)["verdict"] == "unreviewed"
    )


def test_cli_export_includes_audit_appendix_and_keeps_full_final(core, tmp_path, capsys):
    from cpc.cli import main

    app, repo, entity, claims = prepared(core)
    original = app.build_document(entity)
    db = repo.db.execute("PRAGMA database_list").fetchone()[2]
    output = tmp_path / "view.md"
    assert main(["--db", db, "view", "--entity", entity, "--out", str(output)]) == 0
    assert output.with_suffix(".audit.json").exists()
    assert output.with_suffix(".omitted.json").exists()
    reading = tmp_path / "reading.md"
    assert (
        main(
            [
                "--db",
                db,
                "generate",
                "--entity",
                entity,
                "--format",
                "reading",
                "--out",
                str(reading),
            ]
        )
        == 0
    )
    assert len(json.loads(reading.with_suffix(".audit.json").read_text(encoding="utf-8"))) == len(
        claims
    )
    assert repo.document(original["document_id"])["markdown"] == original["markdown"]


def test_evaluation_resume_reuses_successes_and_preserves_source(core, tmp_path, monkeypatch):
    _, repo, _, _ = prepared(core)
    source = tmp_path / "source/captures.sqlite"
    source.parent.mkdir()
    with sqlite3.connect(source) as backup:
        repo.db.backup(backup)
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / "scripts"))
    from run_support_evaluation import run

    monkeypatch.chdir(tmp_path)
    args = Namespace(
        source=source,
        out=tmp_path / "sample/evaluation",
        limit=3,
        labels=None,
        live=False,
        resume=False,
    )
    run(args)
    report = json.loads((args.out / "report.json").read_text(encoding="utf-8"))
    assert report["source_unchanged"] and report["fragment_unchanged"]
    assert report["quality"]["status"] == "gold_missing"
    from cpc.repository import Repository

    with_repo = Repository(args.out / "captures.sqlite")
    before = with_repo.one("SELECT count(*) AS n FROM ai_runs")["n"]
    with_repo.close()
    args.resume = True
    run(args)
    with_repo = Repository(args.out / "captures.sqlite")
    assert with_repo.one("SELECT count(*) AS n FROM ai_runs")["n"] == before
    with_repo.close()
