"""Frozen development Gate and deterministic task-specific selection."""

from __future__ import annotations

from statistics import mean, median

from n04g25a_development_metrics import metrics, repeatability


def evaluate(task, rows, predictions, classes, latencies, peak_vram, artifact_bytes):
    failures = repeatability(rows, predictions)
    repeats = [metrics(task, rows, labels, classes) for labels in predictions]
    critical = max(r["critical_false_pass"] for r in repeats)
    required = max(r["required_valid_false_reject"] for r in repeats)
    return {
        "hard_gate": "PASS" if critical == required == failures == 0 else "FAIL",
        "critical_false_pass": critical,
        "required_valid_false_reject": required,
        "repeatability_failures": failures,
        "repeat_metrics": repeats,
        "ranking_metrics": {
            "nonambiguous_ambiguity_rate": mean(r["nonambiguous_ambiguity_rate"] for r in repeats),
            "macro_f1": mean(r["macro_f1"] for r in repeats),
            "mean_class_recall": mean(r["mean_class_recall"] for r in repeats),
            "median_amortized_latency_seconds": median(latencies),
            "peak_allocated_vram_bytes": peak_vram,
            "artifact_bytes": artifact_bytes,
        },
    }


def select(results, candidate_order):
    """No selection from failed/incomplete candidates and no manual override."""
    selected = {}
    if len(set(candidate_order)) != len(candidate_order):
        raise ValueError("Duplicate manifest candidates")
    expected = {(cid, task) for cid in candidate_order for task in ("atomicity", "content_type")}
    observed = [(r["candidate_id"], r["task"]) for r in results]
    if len(observed) != len(expected) or set(observed) != expected:
        raise ValueError("Complete unique results for every frozen candidate/task required")
    for task in ("atomicity", "content_type"):
        passing = []
        for r in results:
            if r["task"] != task or r["status"] != "completed":
                continue
            if r["hard_gate"] == "PASS":
                if any(
                    r[k] != 0
                    for k in (
                        "critical_false_pass",
                        "required_valid_false_reject",
                        "repeatability_failures",
                    )
                ):
                    raise ValueError("Inconsistent hard Gate")
                passing.append(r)

        def key(r):
            m = r["ranking_metrics"]
            return (
                m["nonambiguous_ambiguity_rate"],
                -m["macro_f1"],
                -m["mean_class_recall"],
                m["median_amortized_latency_seconds"],
                m["peak_allocated_vram_bytes"],
                m["artifact_bytes"],
                candidate_order.index(r["candidate_id"]),
            )

        selected[task] = min(passing, key=key)["candidate_id"] if passing else None
    return {
        "outcome": "DEVELOPMENT_PAIR_PASS" if all(selected.values()) else "VALID_FAIL_NO_SELECTION",
        "selected": selected,
        "partial_task_pass_is_diagnostic_only": not all(selected.values()),
        "confirmation_started": False,
        "G25A_complete": False,
    }
