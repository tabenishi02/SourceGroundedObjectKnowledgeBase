"""High-recall extraction, bounded inputs and explicit coverage checkpoints."""

import json
import re
from copy import deepcopy

from jsonschema import Draft202012Validator

from .domain import digest, json_text

STRATEGIES = {
    "single_pass": ("all",),
    "high_recall_multi_pass": ("facts_and_promotional_claims", "interpretations_and_perception"),
    "extract_review": ("all", "review_missing_claims"),
}

WINDOW_CHARS = 480
WINDOW_OVERLAP = 64
MIN_WINDOW_CHARS = 120


def extraction_windows(batch, window_chars=WINDOW_CHARS):
    """Partition only inference inputs; preserve Evidence identities and every character."""
    overlap = min(WINDOW_OVERLAP, window_chars // 4)
    if sum(len(e["content"]) for e in batch) <= window_chars:
        yield batch
        return
    for evidence in batch:
        text = evidence["content"]
        start = 0
        while start < len(text):
            end = min(start + window_chars, len(text))
            if end < len(text):
                boundaries = list(re.finditer(r"[。！？.!?\n]", text[start:end]))
                if boundaries and boundaries[-1].end() >= window_chars // 2:
                    end = start + boundaries[-1].end()
            yield [{**evidence, "content": text[start:end]}]
            if end == len(text):
                break
            start = end - overlap


def quote_choices(allowed):
    """The model selects IDs; the Core copies exact source strings."""
    return {
        "q-" + digest(json_text([e["id"], e["content"]])): {
            "evidence_id": e["id"],
            "text": e["content"],
        }
        for e in allowed.values()
    }


def resolve_quotes(result, choices, response_schema):
    errors = list(Draft202012Validator(response_schema).iter_errors(result))
    if errors:
        raise ValueError("Invalid quote-selection schema at " + "/".join(map(str, errors[0].path)))
    resolved = deepcopy(result)
    for fragment in resolved["fragments"]:
        choice = choices[fragment.pop("quote_id")]
        if choice["evidence_id"] not in fragment["evidence_ids"]:
            raise ValueError("Selected quote must belong to a cited Evidence")
        fragment["original_text"] = choice["text"]
    return resolved


def substantive(row):
    kinds = set(json.loads(row["metadata"])["kinds"])
    return bool(kinds & {"paragraph", "table", "quote", "post", "list", "code"})


def validate_capture(result, targets, allowed, schema):
    errors = list(Draft202012Validator(schema).iter_errors(result))
    if errors:
        raise ValueError("Invalid high-recall schema at " + "/".join(map(str, errors[0].path)))
    ids = [a["evidence_id"] for a in result["assessments"]]
    if len(ids) != len(set(ids)) or set(ids) != set(targets):
        raise ValueError("Every input evidence needs exactly one assessment")
    referenced = set()
    for fragment in result["fragments"]:
        refs = fragment["evidence_ids"]
        if any(e not in allowed for e in refs) or not set(refs) & set(targets):
            raise ValueError("Unknown evidence or fragment unrelated to this batch")

        def normalize(t):
            return re.sub(r"\s+", " ", t).strip()

        quote = normalize(fragment["original_text"])
        if not any(quote in normalize(allowed[e]["content"]) for e in refs):
            raise ValueError("original_text must quote supplied evidence verbatim")
        if (
            fragment["epistemic_type"] == "derived_interpretation"
            and fragment["asserted_by"] != "cpc_llm"
        ):
            raise ValueError("Derived interpretations must identify cpc_llm as the claimant")
        referenced.update(refs)
        fragment["content"] = fragment["resolved_statement"]
    for a in result["assessments"]:
        if (a["evidence_id"] in referenced) == bool(a["discard_reason"]):
            raise ValueError(
                "Zero fragments require a reason; referenced evidence cannot be discarded"
            )
    return result


def batches(evidence, batch_size, max_chars):
    batch, used = [], 0
    for row in evidence:
        length = len(json_text(row))
        if length > max_chars:
            raise ValueError("Evidence exceeds input budget; reprocess with smaller chunks")
        if batch and (len(batch) >= batch_size or used + length > max_chars):
            yield batch
            batch, used = [], 0
        batch.append(row)
        used += length
    if batch:
        yield batch


class HighRecallCapture:
    def __init__(self, app):
        self.app, self.repo = app, app.repository

    def extract_window(self, payload, allowed, schema, strategy, max_chars):
        try:
            return self._extract_window(payload, allowed, schema, strategy, max_chars)
        except ValueError as error:
            if str(error) not in {
                "LLM output reached token budget",
                "LLM output truncated; increase CPC_LLM_MAX_TOKENS",
            }:
                raise
            length = sum(len(e["content"]) for e in payload["evidence"])
            if length <= MIN_WINDOW_CHARS:
                raise
            width = max(MIN_WINDOW_CHARS, min(WINDOW_CHARS, length) // 2)
            combined = {"fragments": [], "entity_candidates": [], "assessments": []}
            reasons, ai_id = {}, None
            for window in extraction_windows(payload["evidence"], width):
                neighbors = [{**e, "content": e["content"][:width]} for e in payload["neighbors"]]
                subpayload = {
                    **payload,
                    "evidence": window,
                    "neighbors": neighbors,
                    "target_evidence_ids": [e["id"] for e in window],
                }
                subpayload.pop("validation_error", None)
                result, subreasons, ai_id = self.extract_window(
                    subpayload,
                    {e["id"]: e for e in window + neighbors},
                    schema,
                    strategy,
                    max_chars,
                )
                combined["fragments"].extend(result["fragments"])
                combined["entity_candidates"].extend(result["entity_candidates"])
                reasons.update(subreasons)
            return combined, reasons, ai_id

    def _extract_window(self, payload, allowed, schema, strategy, max_chars):
        ids = payload["target_evidence_ids"]
        choices = quote_choices(allowed)
        payload = {**payload, "quote_choices": choices}
        response_schema = deepcopy(schema)
        assessments = response_schema["properties"]["assessments"]
        assessments.update(minItems=len(ids), maxItems=len(ids))
        assessments["items"]["properties"]["evidence_id"]["enum"] = ids
        fragment_schema = response_schema["properties"]["fragments"]["items"]
        del fragment_schema["properties"]["original_text"]
        fragment_schema["required"].remove("original_text")
        fragment_schema["properties"]["quote_id"] = {"type": "string", "enum": list(choices)}
        fragment_schema["required"].append("quote_id")
        fragment_schema["properties"]["evidence_ids"]["items"]["enum"] = list(allowed)
        combined = {"fragments": [], "entity_candidates": [], "assessments": []}
        reasons = {}
        ai_id = None
        for focus in STRATEGIES[strategy]:
            pass_payload = {**payload, "focus": focus}
            if focus == "review_missing_claims":
                if len(json_text(combined["fragments"])) > max_chars:
                    raise ValueError("Review input exceeds budget; reduce batch size")
                pass_payload["existing_fragments"] = combined["fragments"]
            for attempt in range(2):
                try:
                    ai_id, _, parsed = self.app.call_llm(
                        "high_recall_fragment",
                        "high_recall",
                        pass_payload,
                        response_schema=response_schema,
                    )
                    parsed = resolve_quotes(parsed, choices, response_schema)
                    validated = validate_capture(parsed, ids, allowed, schema)
                    break
                except ValueError as error:
                    ai_id = getattr(self.app, "last_ai_id", None)
                    if ai_id:
                        self.repo.finish_ai(ai_id, error=type(error).__name__)
                    if attempt:
                        raise
                    pass_payload["validation_error"] = str(error)[:300]
            combined["fragments"].extend({**f, "ai_run": ai_id} for f in validated["fragments"])
            combined["entity_candidates"].extend(validated["entity_candidates"])
            reasons.update(
                {a["evidence_id"]: a["discard_reason"] for a in validated["assessments"]}
            )
        return combined, reasons, ai_id

    def run(
        self,
        snapshot_id,
        entity_id,
        batch_size=4,
        max_chars=6000,
        strategy="single_pass",
        resume=None,
    ):
        if strategy not in STRATEGIES or batch_size < 1 or max_chars < 1000:
            raise ValueError("Invalid capture strategy or batch budget")
        snapshot = self.repo.snapshot(snapshot_id)
        if not snapshot or not snapshot["active_run"]:
            raise ValueError("Process snapshot first")
        entity = self.repo.entity(entity_id)
        context = self.repo.page_context(snapshot["active_run"])
        if not context:
            raise ValueError("Legacy normalized generation has no context; process it again")
        evidence = self.repo.evidence(snapshot_id)
        annotated = [{**e, "substantive": substantive(e)} for e in evidence]
        _, prompt_version = self.app.prompt("high_recall")
        schema = json.loads(
            (self.app.prompt_dir / "high_recall.schema.json").read_text(encoding="utf-8")
        )
        configuration = {
            "algorithm": "full-evidence-v4-adaptive-quote-selection",
            "window_chars": WINDOW_CHARS,
            "window_overlap": WINDOW_OVERLAP,
            "minimum_window_chars": MIN_WINDOW_CHARS,
            "validation_retries": 1,
            "strategy": strategy,
            "batch_size": batch_size,
            "max_chars": max_chars,
            "prompt_version": prompt_version,
            "schema_hash": digest(json_text(schema)),
            "model": self.app.llm.model if self.app.llm else None,
            "revision": self.app.llm.revision if self.app.llm else None,
            "provider": getattr(self.app.llm, "configuration", {}),
        }
        if resume:
            job = self.repo.extraction_job(resume)
            if (
                job["snapshot_id"] != snapshot_id
                or job["entity_id"] != entity_id
                or job["normalized_run"] != snapshot["active_run"]
                or job["configuration"] != configuration
                or job["context_id"] != context["id"]
            ):
                raise ValueError("Resume conditions changed; start a new job")
            if job["status"] == "complete":
                return self.repo.coverage(resume)
        else:
            job = self.repo.start_extraction(
                snapshot, entity_id, context["id"], configuration, annotated
            )
        job_id = job["id"]
        done = {
            a["evidence_id"]
            for a in self.repo.assessments(job_id)
            if a["status"] in {"success", "discarded"}
        }
        pending = [e for e in annotated if e["id"] not in done]
        metadata = [e for e in pending if not e["substantive"]]
        if metadata:
            ids = [e["id"] for e in metadata]
            self.repo.record_batch(
                job_id,
                digest(json_text(ids)),
                ids,
                {
                    "assessments": [
                        {"evidence_id": e, "discard_reason": "metadata_only"} for e in ids
                    ],
                    "fragments": [],
                    "entity_candidates": [],
                },
            )
        targets = [
            {"id": e["id"], "content": e["content"], "metadata": json.loads(e["metadata"])}
            for e in pending
            if e["substantive"]
        ]
        ordered = [e["id"] for e in evidence]
        by_id = {e["id"]: e for e in evidence}
        for batch in batches(targets, batch_size, max_chars):
            ids = [e["id"] for e in batch]
            allowed = {e["id"]: e for e in batch}
            neighbors = []
            remaining = max_chars - len(json_text(batch))
            for evidence_id in ids:
                i = ordered.index(evidence_id)
                for j in (i - 1, i + 1):
                    if 0 <= j < len(ordered) and ordered[j] not in allowed:
                        row = by_id[ordered[j]]
                        neighbor = {
                            "id": row["id"],
                            "content": row["content"],
                            "metadata": json.loads(row["metadata"]),
                        }
                        length = len(json_text(neighbor))
                        if length <= remaining:
                            neighbors.append(neighbor)
                            allowed[row["id"]] = neighbor
                            remaining -= length
            # Stable batch identity uses assigned evidence only, not model-generated content.
            key = digest(json_text(ids))
            combined = {"assessments": [], "fragments": [], "entity_candidates": []}
            ai_id = None
            try:
                reasons = {}
                for window in extraction_windows(batch):
                    window_ids = [e["id"] for e in window]
                    window_allowed = {e["id"]: e for e in window}
                    window_neighbors = [e for e in neighbors if e["id"] not in window_allowed]
                    # Context is supplementary; keep target output proportional to a small window.
                    window_neighbors = [
                        {**e, "content": e["content"][:WINDOW_CHARS]} for e in window_neighbors
                    ]
                    window_allowed.update({e["id"]: e for e in window_neighbors})
                    payload = {
                        "entity": entity,
                        "page_context": context["effective"],
                        "captured_at": snapshot["captured_at"],
                        "evidence": window,
                        "target_evidence_ids": window_ids,
                        "neighbors": window_neighbors,
                        "mode": strategy,
                    }
                    result, window_reasons, ai_id = self.extract_window(
                        payload, window_allowed, schema, strategy, max_chars
                    )
                    combined["fragments"].extend(result["fragments"])
                    combined["entity_candidates"].extend(result["entity_candidates"])
                    reasons.update(window_reasons)
                referenced = {e for f in combined["fragments"] for e in f["evidence_ids"]}
                combined["assessments"] = [
                    {"evidence_id": e, "discard_reason": None if e in referenced else reasons[e]}
                    for e in ids
                ]
                self.repo.record_batch(job_id, key, ids, combined, ai_id)
            except Exception as error:
                ai_id = getattr(self.app, "last_ai_id", None) or ai_id
                if ai_id:
                    self.repo.finish_ai(ai_id, error=type(error).__name__)
                self.repo.record_batch(job_id, key, ids, ai_run=ai_id, error=type(error).__name__)
        return self.repo.promote_extraction(job_id)
