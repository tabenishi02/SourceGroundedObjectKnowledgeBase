"""Model-specific counting and deterministic inference packing; never trims source text."""

import json
import re

import httpx

from .domain import json_text


class TokenCounter:
    def __init__(self, kind="utf8-upper-bound", model=None):
        self.configuration = {"kind": kind, "model": model, "exact": kind == "lmstudio"}
        self.model = None
        if kind == "lmstudio":
            try:
                import lmstudio
            except ImportError as exc:
                raise ValueError("Install the optional token-counting dependency lmstudio") from exc
            response = httpx.get("http://127.0.0.1:1234/api/v1/models", timeout=10)
            response.raise_for_status()
            loaded = [
                instance
                for item in response.json().get("models", [])
                for instance in item.get("loaded_instances", [])
                if model is None or item.get("key") == model or instance.get("id") == model
            ]
            if len(loaded) != 1:
                raise ValueError(
                    "Exact counter requires one matching already loaded LM Studio model"
                )
            self.model = lmstudio.llm(loaded[0]["id"])
            self.configuration["loaded_instance"] = loaded[0]["id"]
            self.configuration["context_tokens"] = self.model.get_context_length()
        elif kind != "utf8-upper-bound":
            raise ValueError("Unknown token counter")

    def count(self, text):
        return len(self.model.tokenize(text)) if self.model else len(text.encode("utf-8"))

    def request_tokens(self, prompt, payload):
        if self.model:
            import lmstudio

            chat = lmstudio.Chat.from_history(
                {
                    "messages": [
                        {"role": "system", "content": prompt},
                        {"role": "user", "content": json_text(payload)},
                    ]
                }
            )
            return self.count(self.model.apply_prompt_template(chat))
        # Explicit estimate, not a claim of exact template/context counting.
        return self.count(prompt + json_text(payload)) + 512


def calibrate_packer(repo, counter, provider, transport, target, output_budget, model, revision):
    """Freeze a conservative output/material ratio from compatible successful calls."""
    samples, ratios = [], []
    if counter.configuration["exact"]:
        rows = repo.rows(
            "SELECT a.id,a.input,o.observations FROM ai_runs a JOIN ai_observations o "
            "ON o.ai_run=a.id WHERE a.task_type='high_recall_fragment' AND a.status='success' "
            "AND a.model=? AND a.revision=? ORDER BY a.rowid DESC LIMIT 32",
            (model, revision),
        )
        for row in rows:
            recorded = json.loads(row["input"])
            if recorded.get("provider_configuration") != provider:
                continue
            compact = "f" in recorded.get("response_schema", {}).get("properties", {})
            if compact != (transport == "compact-keys-v1"):
                continue
            text = "".join(e["content"] for e in recorded["payload"].get("evidence", []))
            tokens = counter.count(text)
            output = json.loads(row["observations"]).get("usage", {}).get("completion_tokens")
            if tokens and output:
                samples.append(row["id"])
                ratios.append(output / tokens)
    ratio = max(ratios, default=0)
    effective = min(target, max(1, int(output_budget / (ratio * 1.25)))) if ratio else target
    return {
        "method": "observed-max-output-ratio-v1",
        "sample_ai_runs": samples,
        "output_material_ratio": ratio,
        "margin": 1.25,
        "material_target": effective,
    }


def packed_windows(evidence, counter, target):
    """Choose Unicode character spans under material budget, preserving every position."""
    pending, used = [], 0
    for row in evidence:
        text, start = row["content"], 0
        dense = set(row.get("metadata", {}).get("kinds", [])) & {"table", "list", "post"}
        cap = max(1, target // 2) if dense else target
        while start < len(text):
            low, high = start + 1, len(text)
            if counter.count(text[start:low]) > cap:
                raise ValueError("Material budget cannot fit one character")
            while low < high:
                middle = (low + high + 1) // 2
                if counter.count(text[start:middle]) <= cap:
                    low = middle
                else:
                    high = middle - 1
            end = low
            boundaries = list(re.finditer(r"[。！？.!?\n]", text[start:end]))
            if end < len(text) and boundaries and boundaries[-1].end() >= (end - start) // 2:
                end = start + boundaries[-1].end()
            size = counter.count(text[start:end])
            if pending and used + size > target:
                yield pending
                pending, used = [], 0
            origin = row.get("span_start", 0)
            pending.append(
                {
                    **row,
                    "content": text[start:end],
                    "span_start": origin + start,
                    "span_end": origin + end,
                }
            )
            used += size
            if end == len(text):
                break
            overlap = min(64, max(0, (end - start) // 4))
            # Same-Evidence spans must not share an ID in one request's assessment map.
            yield pending
            pending, used = [], 0
            start = end - overlap
    if pending:
        yield pending
