"""Versioned support audits in the existing processing ledger; source claims are immutable."""

import json
import re
from pathlib import Path

from jsonschema import Draft202012Validator, ValidationError

from .domain import digest, json_text

VERSION = "support-audit-v1"


def contract_hash(prompt_dir=None):
    directory = Path(prompt_dir) if prompt_dir else Path(__file__).parent / "prompts"
    return digest(
        json_text(
            [
                VERSION,
                (directory / "support_review.md").read_text(encoding="utf-8"),
                (directory / "support_review.schema.json").read_text(encoding="utf-8"),
            ]
        )
    )


def quote_span(text, quote):
    if not quote.strip():
        return None
    start = text.find(quote)
    if start >= 0:
        return [start, start + len(quote)]
    positions = [i for i, char in enumerate(text) if not char.isspace()]
    compact = "".join(text[i] for i in positions)
    sought = re.sub(r"\s+", "", quote)
    start = compact.find(sought)
    if start < 0:
        return None
    return [positions[start], positions[start + len(sought) - 1] + 1]


def audit_claim(repo, claim):
    supports = []
    for fragment_id in claim["fragment_ids"]:
        fragment = repo.one("SELECT * FROM fragments WHERE id=?", (fragment_id,))
        if not fragment:
            raise ValueError("Support fragment missing")
        metadata = json.loads(fragment["metadata"])
        quote = metadata.get("original_text")
        quote = quote if isinstance(quote, str) else ""
        provenance = repo.provenance("fragment", fragment_id)
        evidence = [
            {
                "evidence_id": e["evidence_id"],
                "snapshot_id": e["snapshot_id"],
                "normalized_run": e["run_id"],
                "url": e["url"],
                "content_hash": digest(e["content"]),
                "quote_span": quote_span(e["content"], quote),
                "context": e["content"],
            }
            for e in provenance["evidence"]
        ]
        supports.append(
            {
                "fragment_id": fragment_id,
                "fragment_run": fragment["run_id"],
                "extraction_job": metadata.get("extraction_job"),
                "asserted_by": metadata.get("asserted_by"),
                "epistemic_type": metadata.get("epistemic_type"),
                "quote": quote,
                "quote_hash": digest(quote),
                "quote_present": any(e["quote_span"] is not None for e in evidence),
                "evidence": evidence,
            }
        )
    payload = {"version": VERSION, "claim": claim, "supports": supports}
    return {**payload, "input_hash": digest(json_text(payload))}


def review_index(repo, prompt_dir=None):
    contract = contract_hash(prompt_dir)
    result = {}
    for row in repo.rows(
        "SELECT id,output,model,revision,executed_at,input FROM ai_runs "
        "WHERE task_type='support_review' AND status='success' "
        "ORDER BY rowid DESC"
    ):
        payload = json.loads(row["input"])["payload"]
        if payload.get("contract_hash") == contract:
            result.setdefault(payload["audit_hash"], row)
    return result


def latest_review(repo, audit, prompt_dir=None, reviews=None):
    reviews = review_index(repo, prompt_dir) if reviews is None else reviews
    row = reviews.get(audit["input_hash"])
    if row:
        result = json.loads(row["output"])
        return {
            **result,
            "ai_run": row["id"],
            "channel": ("preflight" if row["model"] == "cpc-support-preflight" else "llm_judge"),
            "model": row["model"],
            "revision": row["revision"],
            "executed_at": row["executed_at"],
        }
    return {"verdict": "unreviewed", "reason": "No current semantic review", "channel": None}


def review_claim(app, claim, max_chars=16000, use_cache=True):
    if max_chars < 1:
        raise ValueError("Invalid support review input budget")
    repo = app.repository
    audit = audit_claim(repo, claim)
    if app.llm is None:
        raise ValueError("Support review requires a real judge provider")
    prompt, prompt_version = app.prompt("support_review")
    schema = json.loads((app.prompt_dir / "support_review.schema.json").read_text(encoding="utf-8"))
    key = digest(
        json_text(
            [
                audit,
                prompt,
                schema,
                max_chars,
                app.llm.model,
                app.llm.revision,
                getattr(app.llm, "configuration", {}),
            ]
        )
    )
    previous = repo.one(
        "SELECT id,output FROM ai_runs WHERE task_type='support_review' AND status='success' "
        "AND json_extract(input,'$.payload.cache_key')=? ORDER BY rowid DESC LIMIT 1",
        (key,),
    )
    if previous and use_cache:
        return {**json.loads(previous["output"]), "ai_run": previous["id"], "cached": True}
    payload = {
        "audit_hash": audit["input_hash"],
        "cache_key": key,
        "contract_hash": contract_hash(app.prompt_dir),
        "input_budget_chars": max_chars,
        "audit": audit,
    }
    if not audit["supports"] or not all(s["quote_present"] for s in audit["supports"]):
        result = {
            "verdict": "unsupported",
            "reason": "A support quote is missing from cited evidence",
        }
    elif len(json_text(payload)) > max_chars:
        result = {
            "verdict": "uncertain",
            "reason": "Support input exceeds review budget; no text was trimmed",
        }
    else:
        ai_id, _, result = app.call_llm("support_review", "support_review", payload)
        try:
            Draft202012Validator(schema).validate(result)
        except ValidationError as error:
            raw = repo.one("SELECT output FROM ai_runs WHERE id=?", (ai_id,))["output"]
            repo.finish_ai(ai_id, output=raw, error="InvalidSupportVerdict")
            raise ValueError("Invalid support review verdict") from error
        return {**result, "ai_run": ai_id, "cached": False}
    ai_id = repo.begin_ai(
        "support_review",
        "cpc-support-preflight",
        VERSION,
        prompt,
        prompt_version,
        {"payload": payload},
    )
    repo.finish_ai(ai_id, json_text(result))
    return {**result, "ai_run": ai_id, "cached": False}


def attribution(claim):
    kind = claim["epistemic_type"]
    label = {
        "fact": "資料の記述（真実性は未認定）",
        "source_interpretation": "資料筆者の評価・解釈",
        "derived_interpretation": "CPCの推論",
        "public_perception": "感想・評判",
        "promotional_claim": "宣伝的主張",
    }.get(kind, "未分類の主張")
    return f"{label}／主張主体: {claim['asserted_by']}"
