from __future__ import annotations

import argparse
import importlib.metadata
import json
import platform
import sys
import time
from pathlib import Path
from typing import Any

MINICHECK_SOURCE_REVISION = "b58b9fa69acbd1015ec970fa65dd752413a053d2"

CANDIDATES = {
    "minicheck-roberta-large": {
        "model_repo": "lytang/MiniCheck-RoBERTa-Large",
        "kind": "minicheck",
        "decision_surface": "support_probability >= 0.50",
    },
    "lettucedect-v2-mmbert-base": {
        "model_repo": "KRLabsOrg/lettucedect-v2-mmbert-base",
        "kind": "mmbert",
        "decision_surface": "one or more unsupported answer-token spans => no PASS",
    },
    "lettucedect-v2-qwen-2b": {
        "model_repo": "KRLabsOrg/lettucedect-v2-qwen-2b",
        "kind": "qwen",
        "decision_surface": "one or more hallucinated_spans => no PASS",
    },
}

QWEN_SYSTEM = """You are an expert annotator who identifies hallucinated spans in a generated answer with respect to a given context (the only trusted evidence). A hallucinated span is a substring of the answer that is not supported by the context. Spans consistent with the context are not hallucinations.

Quote each hallucinated span verbatim from the answer and classify it into exactly one category and one subcategory.

Categories (the kinds of unsupported span):
- contradiction: conflicts with the context (a wrong value, number, date, name, or relationship)
- fabricated_reference: an entity, name, identifier, or section that is absent from the context
- unsupported_addition: a claim, detail, or behavior the context never states

Subcategories:
- entity: a wrong or invented name, entity, or object
- temporal: an incorrect date, time, duration, or ordering
- numerical: an incorrect number, quantity, or amount
- value: a wrong value, setting, or attribute value
- relational: an incorrect relationship or association between things
- identifier: an invented identifier or name not found in the context
- section: a reference to a section, part, or location that does not exist
- attribute: an invented or incorrect attribute or property
- claim: an added factual claim the context does not support
- behavior: an added or changed action or behavior the context never states
- elaboration: extra detail or elaboration beyond what the context supports
- subjective: an unsupported subjective or evaluative statement
- unspecified: unsupported, with no more specific subtype

Reply with ONLY a JSON object (no markdown, no code fences): {"hallucinated_spans": [{"text": "...", "category": "...", "subcategory": "..."}]}. If nothing is unsupported, reply {"hallucinated_spans": []}."""

QWEN_REQUEST = (
    "Restate only information supported by the supplied context. "
    "Do not add details that are absent from the context."
)
QWEN_CATEGORIES = {"contradiction", "fabricated_reference", "unsupported_addition"}
QWEN_SUBCATEGORIES = {
    "entity",
    "temporal",
    "numerical",
    "value",
    "relational",
    "identifier",
    "section",
    "attribute",
    "claim",
    "behavior",
    "elaboration",
    "subjective",
    "unspecified",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", choices=sorted(CANDIDATES), required=True)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--cache-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--qwen-repeats",
        type=int,
        default=3,
        help="Repeat count for deterministic Qwen output stability testing.",
    )
    return parser.parse_args()


def package_version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def load_corpus(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    cases = payload.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("benchmark corpus must contain non-empty cases")
    return payload


def resolved_hf_revision(repo_id: str) -> str:
    from huggingface_hub import model_info

    info = model_info(repo_id)
    if not info.sha:
        raise RuntimeError(f"could not resolve Hugging Face revision for {repo_id}")
    return str(info.sha)


def cuda_runtime_snapshot() -> dict[str, Any]:
    import torch

    snapshot: dict[str, Any] = {
        "cuda_available": torch.cuda.is_available(),
        "torch_version": torch.__version__,
        "torch_cuda_build": torch.version.cuda,
    }
    if torch.cuda.is_available():
        snapshot.update(
            {
                "device_name": torch.cuda.get_device_name(0),
                "device_capability": list(torch.cuda.get_device_capability(0)),
            }
        )
    return snapshot


def summarize_cases(
    cases: list[dict[str, Any]], *, extra_gate_pass: bool = True
) -> dict[str, Any]:
    required_negative = [
        item for item in cases if item["required"] and item["expected"] == "UNSUPPORTED"
    ]
    required_positive = [
        item for item in cases if item["required"] and item["expected"] == "SUPPORTED"
    ]
    all_positive = [item for item in cases if item["expected"] == "SUPPORTED"]
    all_negative = [item for item in cases if item["expected"] == "UNSUPPORTED"]

    false_positive_ids = [
        item["case_id"] for item in required_negative if item["verdict"] == "SUPPORTED"
    ]
    required_positive_supported_ids = [
        item["case_id"] for item in required_positive if item["verdict"] == "SUPPORTED"
    ]
    indeterminate_ids = [
        item["case_id"] for item in cases if item["verdict"] == "INDETERMINATE"
    ]

    positive_recall = (
        sum(item["verdict"] == "SUPPORTED" for item in all_positive) / len(all_positive)
        if all_positive
        else None
    )
    negative_specificity = (
        sum(item["verdict"] == "UNSUPPORTED" for item in all_negative) / len(all_negative)
        if all_negative
        else None
    )

    candidate_gate_pass = (
        not false_positive_ids
        and len(required_positive_supported_ids) == len(required_positive)
        and not indeterminate_ids
        and extra_gate_pass
    )
    return {
        "required_negative_false_positive_count": len(false_positive_ids),
        "required_negative_false_positive_ids": false_positive_ids,
        "required_positive_supported_count": len(required_positive_supported_ids),
        "required_positive_count": len(required_positive),
        "required_positive_supported_ids": required_positive_supported_ids,
        "positive_recall": positive_recall,
        "negative_specificity": negative_specificity,
        "indeterminate_count": len(indeterminate_ids),
        "indeterminate_ids": indeterminate_ids,
        "candidate_gate_pass": candidate_gate_pass,
    }


def run_minicheck(
    corpus: dict[str, Any], cache_dir: Path
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    repo = CANDIDATES["minicheck-roberta-large"]["model_repo"]
    before_revision = resolved_hf_revision(repo)

    from minicheck.minicheck import MiniCheck

    scorer = MiniCheck(model_name="roberta-large", cache_dir=str(cache_dir))
    docs = [item["document"] for item in corpus["cases"]]
    claims = [item["claim"] for item in corpus["cases"]]
    pred_labels, raw_probs, used_chunks, support_prob_per_chunk = scorer.score(
        docs=docs, claims=claims
    )

    after_revision = resolved_hf_revision(repo)
    if before_revision != after_revision:
        raise RuntimeError(
            "MiniCheck model main revision changed during benchmark: "
            f"{before_revision} -> {after_revision}"
        )

    scored: list[dict[str, Any]] = []
    for source, pred_label, probability, chunks, chunk_probs in zip(
        corpus["cases"],
        pred_labels,
        raw_probs,
        used_chunks,
        support_prob_per_chunk,
    ):
        probability_value = float(probability)
        scored.append(
            {
                **source,
                "verdict": "SUPPORTED" if probability_value >= 0.50 else "UNSUPPORTED",
                "model_pred_label": int(pred_label),
                "support_probability": probability_value,
                "used_chunks": list(chunks),
                "support_prob_per_chunk": [float(value) for value in chunk_probs],
            }
        )

    metadata = {
        "resolved_model_revision_before": before_revision,
        "resolved_model_revision_after": after_revision,
        "source_revision": MINICHECK_SOURCE_REVISION,
        "threshold": 0.50,
    }
    return scored, metadata


def merge_token_spans(
    answer: str,
    sequence_ids: list[int | None],
    offsets: list[list[int]],
    labels: list[int],
    unsupported_probs: list[float],
) -> list[dict[str, Any]]:
    spans: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    for sid, (start, end), label, probability in zip(
        sequence_ids, offsets, labels, unsupported_probs
    ):
        if sid != 1 or start == end:
            continue
        if label == 1:
            if current is None:
                current = {
                    "start": start,
                    "end": end,
                    "max_unsupported_probability": probability,
                }
            else:
                current["end"] = end
                current["max_unsupported_probability"] = max(
                    float(current["max_unsupported_probability"]), probability
                )
        elif current is not None:
            start_pos = int(current["start"])
            end_pos = int(current["end"])
            current["text"] = answer[start_pos:end_pos]
            spans.append(current)
            current = None

    if current is not None:
        start_pos = int(current["start"])
        end_pos = int(current["end"])
        current["text"] = answer[start_pos:end_pos]
        spans.append(current)
    return spans


def run_mmbert(
    corpus: dict[str, Any], cache_dir: Path
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    import torch
    from transformers import AutoModelForTokenClassification, AutoTokenizer

    repo = CANDIDATES["lettucedect-v2-mmbert-base"]["model_repo"]
    revision = resolved_hf_revision(repo)
    tokenizer = AutoTokenizer.from_pretrained(
        repo, revision=revision, cache_dir=cache_dir, use_fast=True
    )
    model = AutoModelForTokenClassification.from_pretrained(
        repo, revision=revision, cache_dir=cache_dir
    )
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    model.to(device).eval()

    scored: list[dict[str, Any]] = []
    for source in corpus["cases"]:
        encoded = tokenizer(
            source["document"],
            source["claim"],
            truncation="only_first",
            max_length=4096,
            return_offsets_mapping=True,
            return_tensors="pt",
        )
        sequence_ids = list(encoded.sequence_ids(0))
        offsets = encoded["offset_mapping"][0].tolist()
        model_inputs = {
            key: value.to(device)
            for key, value in encoded.items()
            if key != "offset_mapping"
        }
        with torch.no_grad():
            logits = model(**model_inputs).logits[0]
        probabilities = torch.softmax(logits, dim=-1)
        labels = logits.argmax(dim=-1).detach().cpu().tolist()
        unsupported_probs = probabilities[:, 1].detach().cpu().tolist()
        spans = merge_token_spans(
            source["claim"],
            sequence_ids,
            offsets,
            labels,
            [float(value) for value in unsupported_probs],
        )
        scored.append(
            {
                **source,
                "verdict": "UNSUPPORTED" if spans else "SUPPORTED",
                "unsupported_spans": spans,
            }
        )

    return scored, {"resolved_model_revision": revision}


def parse_qwen_output(raw: str, answer: str) -> list[dict[str, Any]]:
    object_start = raw.find("{")
    if object_start < 0:
        raise ValueError("Qwen output did not contain a JSON object")
    payload, _ = json.JSONDecoder().raw_decode(raw[object_start:])
    if not isinstance(payload, dict) or set(payload) != {"hallucinated_spans"}:
        raise ValueError("Qwen output schema mismatch at top level")
    spans = payload["hallucinated_spans"]
    if not isinstance(spans, list):
        raise ValueError("hallucinated_spans must be an array")

    normalized: list[dict[str, Any]] = []
    for item in spans:
        if not isinstance(item, dict):
            raise ValueError("hallucinated span must be an object")
        if set(item) != {"text", "category", "subcategory"}:
            raise ValueError("hallucinated span schema mismatch")
        text = item["text"]
        category = item["category"]
        subcategory = item["subcategory"]
        if not isinstance(text, str) or not text:
            raise ValueError("hallucinated span text must be a non-empty string")
        if text not in answer:
            raise ValueError("hallucinated span text is not verbatim from the answer")
        if category not in QWEN_CATEGORIES:
            raise ValueError(f"invalid hallucination category: {category!r}")
        if subcategory not in QWEN_SUBCATEGORIES:
            raise ValueError(f"invalid hallucination subcategory: {subcategory!r}")
        start = answer.find(text)
        normalized.append(
            {
                "text": text,
                "category": category,
                "subcategory": subcategory,
                "start": start,
                "end": start + len(text),
            }
        )
    return normalized


def run_qwen(
    corpus: dict[str, Any], cache_dir: Path, repeats: int
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if repeats < 2:
        raise ValueError("Qwen repeatability requires --qwen-repeats >= 2")

    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    repo = CANDIDATES["lettucedect-v2-qwen-2b"]["model_repo"]
    revision = resolved_hf_revision(repo)
    tokenizer = AutoTokenizer.from_pretrained(repo, revision=revision, cache_dir=cache_dir)
    model = AutoModelForCausalLM.from_pretrained(
        repo,
        revision=revision,
        cache_dir=cache_dir,
        torch_dtype="auto",
    )
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    model.to(device).eval()

    scored: list[dict[str, Any]] = []
    repeatability_failures: list[str] = []
    for source in corpus["cases"]:
        user = (
            f"User request: {QWEN_REQUEST}\n\n"
            f"{source['document']}\n\n"
            f"Answer to verify:\n{source['claim']}"
        )
        messages = [
            {"role": "system", "content": QWEN_SYSTEM},
            {"role": "user", "content": user},
        ]

        canonical_outputs: list[str] = []
        raw_outputs: list[str] = []
        parsed_runs: list[list[dict[str, Any]]] = []
        error: str | None = None

        for _ in range(repeats):
            inputs = tokenizer.apply_chat_template(
                messages,
                add_generation_prompt=True,
                enable_thinking=False,
                return_tensors="pt",
                return_dict=True,
            ).to(device)
            with torch.no_grad():
                generated = model.generate(
                    **inputs,
                    max_new_tokens=512,
                    do_sample=False,
                )
            reply = tokenizer.decode(
                generated[0, inputs["input_ids"].shape[1] :],
                skip_special_tokens=True,
            )
            raw_outputs.append(reply)
            try:
                spans = parse_qwen_output(reply, source["claim"])
            except ValueError as exc:
                error = str(exc)
                break
            parsed_runs.append(spans)
            canonical_outputs.append(
                json.dumps(
                    spans,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                )
            )

        if error is not None:
            scored.append(
                {
                    **source,
                    "verdict": "INDETERMINATE",
                    "parse_error": error,
                    "raw_outputs": raw_outputs,
                }
            )
            repeatability_failures.append(source["case_id"])
            continue

        stable = len(set(canonical_outputs)) == 1
        if not stable:
            repeatability_failures.append(source["case_id"])
        spans = parsed_runs[0]
        scored.append(
            {
                **source,
                "verdict": "UNSUPPORTED" if spans else "SUPPORTED",
                "hallucinated_spans": spans,
                "repeatability_pass": stable,
                "raw_outputs": raw_outputs,
            }
        )

    metadata = {
        "resolved_model_revision": revision,
        "qwen_repeats": repeats,
        "repeatability_pass": not repeatability_failures,
        "repeatability_failure_ids": repeatability_failures,
    }
    return scored, metadata


def main() -> int:
    args = parse_args()
    corpus = load_corpus(args.corpus)
    candidate = CANDIDATES[args.candidate]
    args.cache_dir.mkdir(parents=True, exist_ok=True)

    import torch

    started = time.perf_counter()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.reset_peak_memory_stats()

    if candidate["kind"] == "minicheck":
        cases, candidate_metadata = run_minicheck(corpus, args.cache_dir)
        extra_gate_pass = True
    elif candidate["kind"] == "mmbert":
        cases, candidate_metadata = run_mmbert(corpus, args.cache_dir)
        extra_gate_pass = True
    elif candidate["kind"] == "qwen":
        cases, candidate_metadata = run_qwen(corpus, args.cache_dir, args.qwen_repeats)
        extra_gate_pass = bool(candidate_metadata["repeatability_pass"])
    else:
        raise AssertionError(f"unknown candidate kind: {candidate['kind']}")

    elapsed_seconds = time.perf_counter() - started
    peak_vram_mib = (
        torch.cuda.max_memory_allocated(0) / (1024 * 1024)
        if torch.cuda.is_available()
        else None
    )

    metrics = summarize_cases(cases, extra_gate_pass=extra_gate_pass)
    report = {
        "benchmark_id": corpus["benchmark_id"],
        "candidate_id": args.candidate,
        "model_repo": candidate["model_repo"],
        "decision_surface": candidate["decision_surface"],
        "candidate_metadata": candidate_metadata,
        "metrics": metrics,
        "cases": cases,
        "runtime": {
            "python": sys.version,
            "platform": platform.platform(),
            "packages": {
                "minicheck": package_version("minicheck"),
                "nltk": package_version("nltk"),
                "torch": package_version("torch"),
                "transformers": package_version("transformers"),
                "huggingface_hub": package_version("huggingface_hub"),
                "tokenizers": package_version("tokenizers"),
                "accelerate": package_version("accelerate"),
            },
            "cuda": cuda_runtime_snapshot(),
            "elapsed_seconds": elapsed_seconds,
            "peak_vram_mib": peak_vram_mib,
        },
        "note": (
            "N-04G-21V candidate-selection evidence only. "
            "Final G-21 freeze still requires isolated offline Reference Workstation proof."
        ),
    }

    rendered = json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
