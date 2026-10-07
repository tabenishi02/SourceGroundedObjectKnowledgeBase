"""Explicit reference-label metrics; LLM judgements never become human gold implicitly."""

import statistics


def quality_metrics(cases):
    if not cases:
        raise ValueError("No quality cases")
    channels = {case["label_channel"] for case in cases}
    if not channels <= {"human", "curated_fixture", "llm_judge"}:
        raise ValueError("Unknown label channel")
    for case in cases:
        if case["expected"] not in {"supported", "unsupported", "uncertain"}:
            raise ValueError("Invalid reference verdict")
    correct = sum(case["actual"] == case["expected"] for case in cases)
    unsafe = sum(
        case["actual"] == "supported" and case["expected"] != "supported" for case in cases
    )
    required = sum(len(set(case.get("required_claim_ids", []))) for case in cases)
    retrieved = sum(
        len(set(case.get("required_claim_ids", [])) & set(case.get("selected_claim_ids", [])))
        for case in cases
    )
    return {
        "cases": len(cases),
        "label_channels": sorted(channels),
        "human_gold": channels == {"human"},
        "verdict_accuracy": correct / len(cases),
        "false_supported": unsafe,
        "required_claim_recall": retrieved / required if required else None,
    }


def speed_metrics(measurements):
    """Separate warm-up, cached reuse, failures and complete warm measurements."""
    warm = [
        row
        for row in measurements
        if row.get("phase") == "warm"
        and row.get("success")
        and not row.get("cached")
        and not row.get("preflight")
    ]
    durations = sorted(row["duration_seconds"] for row in warm)
    return {
        "warm_successes": len(warm),
        "warmup_count": sum(row.get("phase") == "warmup" for row in measurements),
        "failures": sum(not row.get("success") for row in measurements),
        "cached_count": sum(bool(row.get("cached")) for row in measurements),
        "preflight_count": sum(bool(row.get("preflight")) for row in measurements),
        "median_seconds": statistics.median(durations) if durations else None,
        "min_seconds": min(durations) if durations else None,
        "max_seconds": max(durations) if durations else None,
        "quality_inferred_from_speed": False,
    }
