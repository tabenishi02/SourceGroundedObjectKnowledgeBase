from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

MODEL_REPOS = {
    "roberta-large": "lytang/MiniCheck-RoBERTa-Large",
    "deberta-v3-large": "lytang/MiniCheck-DeBERTa-v3-Large",
    "flan-t5-large": "lytang/MiniCheck-Flan-T5-Large",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--model", choices=sorted(MODEL_REPOS), default="roberta-large")
    parser.add_argument("--cache-dir", type=Path, default=Path(".local/n04g20/minicheck"))
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--thresholds",
        default="0.50,0.60,0.70,0.80,0.85,0.90,0.95",
        help="Comma-separated support thresholds to evaluate.",
    )
    return parser.parse_args()


def load_corpus(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload.get("cases"), list) or not payload["cases"]:
        raise ValueError("benchmark corpus must contain non-empty cases")
    return payload


def evaluate_threshold(cases: list[dict[str, Any]], threshold: float) -> dict[str, Any]:
    required_negative = [
        item for item in cases if item["required"] and item["expected"] == "UNSUPPORTED"
    ]
    required_positive = [
        item for item in cases if item["required"] and item["expected"] == "SUPPORTED"
    ]
    false_positive_ids = [
        item["case_id"] for item in required_negative if item["support_probability"] >= threshold
    ]
    true_positive_ids = [
        item["case_id"] for item in required_positive if item["support_probability"] >= threshold
    ]
    all_positive = [item for item in cases if item["expected"] == "SUPPORTED"]
    all_negative = [item for item in cases if item["expected"] == "UNSUPPORTED"]
    return {
        "supported_threshold": threshold,
        "required_negative_false_positive_count": len(false_positive_ids),
        "required_negative_false_positive_ids": false_positive_ids,
        "required_positive_supported_count": len(true_positive_ids),
        "required_positive_count": len(required_positive),
        "positive_recall": (
            sum(item["support_probability"] >= threshold for item in all_positive)
            / len(all_positive)
            if all_positive
            else None
        ),
        "negative_specificity": (
            sum(item["support_probability"] < threshold for item in all_negative)
            / len(all_negative)
            if all_negative
            else None
        ),
        "necessary_g21_gate_pass": len(false_positive_ids) == 0,
    }


def main() -> int:
    args = parse_args()
    corpus = load_corpus(args.corpus)
    thresholds = [float(value.strip()) for value in args.thresholds.split(",") if value.strip()]

    from minicheck.minicheck import MiniCheck

    scorer = MiniCheck(model_name=args.model, cache_dir=str(args.cache_dir))
    docs = [item["document"] for item in corpus["cases"]]
    claims = [item["claim"] for item in corpus["cases"]]
    pred_labels, raw_probs, _, _ = scorer.score(docs=docs, claims=claims)

    scored_cases: list[dict[str, Any]] = []
    for source, pred_label, probability in zip(corpus["cases"], pred_labels, raw_probs):
        scored_cases.append(
            {
                **source,
                "model_pred_label": int(pred_label),
                "support_probability": float(probability),
            }
        )

    threshold_results = [evaluate_threshold(scored_cases, threshold) for threshold in thresholds]
    eligible = [
        item
        for item in threshold_results
        if item["necessary_g21_gate_pass"]
        and item["required_positive_supported_count"] == item["required_positive_count"]
    ]
    recommended = min(eligible, key=lambda item: item["supported_threshold"]) if eligible else None

    report: dict[str, Any] = {
        "benchmark_id": corpus["benchmark_id"],
        "model_name": args.model,
        "model_repo": MODEL_REPOS[args.model],
        "cases": scored_cases,
        "threshold_results": threshold_results,
        "recommended_threshold_candidate": recommended,
        "candidate_has_eligible_threshold": recommended is not None,
        "note": (
            "G-20 benchmark recommendation only. Exact checkpoint revision and threshold profile "
            "remain subject to G-21 freeze."
        ),
    }

    rendered = json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    print(rendered, end="")
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
