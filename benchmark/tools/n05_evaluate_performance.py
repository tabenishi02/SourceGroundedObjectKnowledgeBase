#!/usr/bin/env python3
"""Evaluate N-05 Reference Workstation performance evidence.

This evaluator is intentionally deterministic and uses only the Python standard
library. It does not execute the benchmark workload itself; it evaluates raw
machine evidence against the frozen N-05 performance contract.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


DEFAULT_CONTRACT = Path("benchmark/n05-performance-contract-v1.json")
PLACEHOLDER_VALUES = {"REPLACE", "REPLACE_WITH_RUN_ID"}


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return value


def nearest_rank(values: list[float], quantile: float) -> float:
    """Return the nearest-rank quantile using one-based ceil(q * n)."""
    if not values:
        raise ValueError("nearest_rank requires at least one value")
    if not 0 < quantile <= 1:
        raise ValueError("quantile must be in (0, 1]")
    ordered = sorted(float(value) for value in values)
    rank = max(1, math.ceil(quantile * len(ordered)))
    return ordered[rank - 1]


def _numeric(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _missing_or_placeholder(value: Any) -> bool:
    return value is None or value == "" or (isinstance(value, str) and value in PLACEHOLDER_VALUES)


def _validate_environment(contract: dict[str, Any], evidence: dict[str, Any]) -> list[str]:
    environment = evidence.get("environment")
    if not isinstance(environment, dict):
        return ["environment object is missing"]
    issues = []
    for field in contract["required_environment_fields"]:
        value = environment.get(field)
        if _missing_or_placeholder(value):
            issues.append(f"environment.{field} is missing")
    return issues


def _validate_workload(
    profile_name: str,
    profile_contract: dict[str, Any],
    profile_evidence: dict[str, Any],
) -> list[str]:
    workload = profile_evidence.get("workload")
    if not isinstance(workload, dict):
        return [f"{profile_name}.workload is missing"]
    issues = []
    for field, bounds in profile_contract["workload_envelope"].items():
        value = workload.get(field)
        if not isinstance(value, int) or isinstance(value, bool):
            issues.append(f"{profile_name}.workload.{field} must be an integer")
            continue
        if value < bounds["min"] or value > bounds["max"]:
            issues.append(
                f"{profile_name}.workload.{field}={value} outside "
                f"[{bounds['min']}, {bounds['max']}]"
            )
    return issues


def _validate_sample_shape(
    contract: dict[str, Any],
    profile_name: str,
    condition: str,
    samples: Any,
) -> list[str]:
    if not isinstance(samples, list):
        return [f"{profile_name}.{condition}_samples must be an array"]
    issues = []
    required_sample = contract["required_sample_fields"]
    required_segments = contract["required_segment_fields"]
    seen_ids: set[str] = set()
    for index, sample in enumerate(samples):
        prefix = f"{profile_name}.{condition}_samples[{index}]"
        if not isinstance(sample, dict):
            issues.append(f"{prefix} must be an object")
            continue
        for field in required_sample:
            if field not in sample:
                issues.append(f"{prefix}.{field} is missing")
        sample_id = sample.get("sample_id")
        if not isinstance(sample_id, str) or not sample_id:
            issues.append(f"{prefix}.sample_id must be a non-empty string")
        elif sample_id in seen_ids:
            issues.append(f"{prefix}.sample_id is duplicated: {sample_id}")
        else:
            seen_ids.add(sample_id)
        status = sample.get("status")
        if status not in {"PASS", "FAIL", "ABORTED"}:
            issues.append(f"{prefix}.status must be PASS, FAIL, or ABORTED")
        total = sample.get("total_seconds")
        if not _numeric(total) or float(total) < 0:
            issues.append(f"{prefix}.total_seconds must be a non-negative finite number")
        retry_count = sample.get("retry_count")
        if not isinstance(retry_count, int) or isinstance(retry_count, bool) or retry_count < 0:
            issues.append(f"{prefix}.retry_count must be a non-negative integer")
        segments = sample.get("segments")
        if not isinstance(segments, dict):
            issues.append(f"{prefix}.segments must be an object")
            continue
        for field in required_segments:
            value = segments.get(field)
            if not _numeric(value) or float(value) < 0:
                issues.append(f"{prefix}.segments.{field} must be a non-negative finite number")
    return issues


def _profile_result(
    contract: dict[str, Any],
    profile_name: str,
    profile_contract: dict[str, Any],
    profile_evidence: Any,
) -> dict[str, Any]:
    if not isinstance(profile_evidence, dict):
        return {
            "status": "BLOCKED",
            "issues": [f"profiles.{profile_name} is missing"],
        }

    issues = _validate_workload(profile_name, profile_contract, profile_evidence)
    warm = profile_evidence.get("warm_samples")
    cold = profile_evidence.get("cold_samples")
    issues.extend(_validate_sample_shape(contract, profile_name, "warm", warm))
    issues.extend(_validate_sample_shape(contract, profile_name, "cold", cold))

    min_warm = contract["statistics"]["minimum_warm_samples_per_profile"]
    min_cold = contract["statistics"]["minimum_cold_samples_per_profile"]
    if isinstance(warm, list) and len(warm) < min_warm:
        issues.append(f"{profile_name} requires at least {min_warm} warm samples; got {len(warm)}")
    if isinstance(cold, list) and len(cold) < min_cold:
        issues.append(f"{profile_name} requires at least {min_cold} cold samples; got {len(cold)}")

    if issues:
        return {"status": "BLOCKED", "issues": issues}

    assert isinstance(warm, list)
    assert isinstance(cold, list)
    failed_warm = [
        {"sample_id": sample["sample_id"], "status": sample["status"]}
        for sample in warm
        if sample["status"] != "PASS"
    ]

    successful_warm = [sample for sample in warm if sample["status"] == "PASS"]
    totals = [float(sample["total_seconds"]) for sample in successful_warm]
    target = float(profile_contract["target_p95_seconds"])

    stats: dict[str, Any] = {
        "target_p95_seconds": target,
        "warm_sample_count": len(warm),
        "cold_sample_count": len(cold),
        "warm_failure_count": len(failed_warm),
        "retry_count_total": sum(int(sample["retry_count"]) for sample in warm),
    }
    if totals:
        stats.update(
            {
                "min_seconds": min(totals),
                "p50_seconds": nearest_rank(totals, 0.50),
                "p95_seconds": nearest_rank(totals, 0.95),
                "max_seconds": max(totals),
            }
        )
        segment_p95 = {}
        for segment in contract["required_segment_fields"]:
            segment_p95[segment] = nearest_rank(
                [float(sample["segments"][segment]) for sample in successful_warm], 0.95
            )
        stats["segment_p95_seconds"] = segment_p95

    cold_pass_totals = [
        float(sample["total_seconds"]) for sample in cold if sample["status"] == "PASS"
    ]
    if cold_pass_totals:
        stats["cold_diagnostic"] = {
            "pass_count": len(cold_pass_totals),
            "min_seconds": min(cold_pass_totals),
            "p95_seconds": nearest_rank(cold_pass_totals, 0.95),
            "max_seconds": max(cold_pass_totals),
        }
    else:
        stats["cold_diagnostic"] = {"pass_count": 0}

    if failed_warm:
        return {
            "status": "FAIL",
            "reason": "formal warm sample failure",
            "failed_warm_samples": failed_warm,
            "statistics": stats,
        }

    p95 = stats["p95_seconds"]
    if p95 > target:
        return {
            "status": "FAIL",
            "reason": f"warm p95 {p95:.6f}s exceeds target {target:.6f}s",
            "statistics": stats,
        }

    return {"status": "PASS", "statistics": stats}


def evaluate(contract: dict[str, Any], evidence: dict[str, Any]) -> dict[str, Any]:
    environment_issues = _validate_environment(contract, evidence)
    if evidence.get("schema_version") != "sgokb.n05.performance-evidence.v1":
        environment_issues.append("unsupported or missing evidence schema_version")
    run_id = evidence.get("run_id")
    if not isinstance(run_id, str) or _missing_or_placeholder(run_id):
        environment_issues.append("run_id is missing")

    result: dict[str, Any] = {
        "schema_version": "sgokb.n05.performance-evaluation.v1",
        "run_id": evidence.get("run_id"),
        "contract_schema_version": contract.get("schema_version"),
        "profiles": {},
    }
    if environment_issues:
        result["overall"] = "BLOCKED"
        result["issues"] = environment_issues
        return result

    profiles_evidence = evidence.get("profiles")
    if not isinstance(profiles_evidence, dict):
        result["overall"] = "BLOCKED"
        result["issues"] = ["profiles object is missing"]
        return result

    statuses = []
    for profile_name, profile_contract in contract["profiles"].items():
        profile_result = _profile_result(
            contract,
            profile_name,
            profile_contract,
            profiles_evidence.get(profile_name),
        )
        result["profiles"][profile_name] = profile_result
        statuses.append(profile_result["status"])

    if "FAIL" in statuses:
        result["overall"] = "FAIL"
    elif "BLOCKED" in statuses:
        result["overall"] = "BLOCKED"
    else:
        result["overall"] = "PASS"
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    contract = _load_json(args.contract)
    evidence = _load_json(args.evidence)
    result = evaluate(contract, evidence)
    rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return {"PASS": 0, "FAIL": 1, "BLOCKED": 2}[result["overall"]]


if __name__ == "__main__":
    raise SystemExit(main())
