from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

DEPENDENCY_COMPLEXITY = {
    "lettucedect-v2-mmbert-base": 1,
    "minicheck-roberta-large": 2,
    "lettucedect-v2-qwen-2b": 3,
}
HISTORICAL_EVIDENCE_PREFERENCE = {
    "minicheck-roberta-large": 0,
    "lettucedect-v2-mmbert-base": 1,
    "lettucedect-v2-qwen-2b": 2,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", type=Path, nargs="+", required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def load_report(path: Path) -> dict[str, Any]:
    report = json.loads(path.read_text(encoding="utf-8"))
    if "candidate_id" not in report or "metrics" not in report:
        raise ValueError(f"not a G-21V result file: {path}")
    report["_source_path"] = str(path)
    return report


def tie_break_key(report: dict[str, Any]) -> tuple[Any, ...]:
    candidate_id = report["candidate_id"]
    metrics = report["metrics"]
    runtime = report["runtime"]
    positive_recall = metrics.get("positive_recall")
    if positive_recall is None:
        positive_recall = -1.0
    elapsed_seconds = runtime.get("elapsed_seconds")
    if elapsed_seconds is None:
        elapsed_seconds = float("inf")
    peak_vram_mib = runtime.get("peak_vram_mib")
    if peak_vram_mib is None:
        peak_vram_mib = float("inf")

    return (
        -float(positive_recall),
        int(metrics.get("indeterminate_count", 0)),
        DEPENDENCY_COMPLEXITY[candidate_id],
        float(elapsed_seconds),
        float(peak_vram_mib),
        HISTORICAL_EVIDENCE_PREFERENCE[candidate_id],
    )


def main() -> int:
    args = parse_args()
    reports = [load_report(path) for path in args.results]
    benchmark_ids = {report["benchmark_id"] for report in reports}
    if len(benchmark_ids) != 1:
        raise ValueError(f"result files use different benchmark IDs: {sorted(benchmark_ids)}")

    candidate_ids = [report["candidate_id"] for report in reports]
    if len(candidate_ids) != len(set(candidate_ids)):
        raise ValueError("duplicate candidate result supplied")

    eligible = [report for report in reports if report["metrics"]["candidate_gate_pass"]]
    ordered_eligible = sorted(eligible, key=tie_break_key)

    if not ordered_eligible:
        disposition = "BLOCKED_NO_ELIGIBLE_CANDIDATE"
        selected_candidate = None
        rationale = (
            "No candidate passed the pre-frozen critical false-positive, required-positive, "
            "indeterminate, and candidate-specific gates. Do not relax thresholds or rubric; "
            "reopen G-21V for failure analysis / additional candidates."
        )
    else:
        selected_candidate = ordered_eligible[0]["candidate_id"]
        disposition = "SELECT_FOR_G21R"
        rationale = (
            "One or more candidates passed the frozen safety Gate. Selection follows the "
            "pre-frozen tie-break order: positive recall, indeterminate/runtime failures, "
            "dependency complexity, measured latency, measured VRAM, then historical-evidence "
            "preference. Selection remains subject to G-21R isolated offline Reference "
            "Workstation proof."
        )

    candidates: list[dict[str, Any]] = []
    for report in sorted(reports, key=lambda item: item["candidate_id"]):
        metrics = report["metrics"]
        runtime = report["runtime"]
        candidates.append(
            {
                "candidate_id": report["candidate_id"],
                "source_path": report["_source_path"],
                "model_repo": report["model_repo"],
                "candidate_metadata": report["candidate_metadata"],
                "candidate_gate_pass": metrics["candidate_gate_pass"],
                "required_negative_false_positive_count": metrics[
                    "required_negative_false_positive_count"
                ],
                "required_negative_false_positive_ids": metrics[
                    "required_negative_false_positive_ids"
                ],
                "required_positive_supported_count": metrics[
                    "required_positive_supported_count"
                ],
                "required_positive_count": metrics["required_positive_count"],
                "positive_recall": metrics["positive_recall"],
                "negative_specificity": metrics["negative_specificity"],
                "indeterminate_count": metrics["indeterminate_count"],
                "elapsed_seconds": runtime.get("elapsed_seconds"),
                "peak_vram_mib": runtime.get("peak_vram_mib"),
                "dependency_complexity_rank": DEPENDENCY_COMPLEXITY[report["candidate_id"]],
            }
        )

    result = {
        "benchmark_id": next(iter(benchmark_ids)),
        "disposition": disposition,
        "selected_candidate_for_g21r": selected_candidate,
        "selection_rationale": rationale,
        "eligible_candidates_in_tie_break_order": [
            report["candidate_id"] for report in ordered_eligible
        ],
        "candidates": candidates,
        "safety_invariant": (
            "Any required unsupported claim accepted as supported disqualifies that candidate. "
            "Do not post-hoc change candidate decision surfaces or corpus labels."
        ),
    }

    rendered = json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
