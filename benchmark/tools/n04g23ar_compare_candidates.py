"""Deterministically select an N-04G-23A-R judge candidate."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = ROOT / "benchmark" / "n04g23ar-judge-candidates-v1.json"
EXPECTED_GOLD_SHA256 = (
    "347e39f5108ed920847ce717cf98571a5137c48e348aba7af7e5aa50679a4687"
)


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _parse_named(items: list[str]) -> dict[str, Path]:
    parsed: dict[str, Path] = {}
    for item in items:
        if "=" not in item:
            raise ValueError("Result arguments must use CANDIDATE_ID=PATH")
        candidate_id, raw_path = item.split("=", 1)
        if not candidate_id or candidate_id in parsed:
            raise ValueError(f"Invalid or duplicate candidate id: {candidate_id!r}")
        parsed[candidate_id] = Path(raw_path)
    return parsed


def _gate_pass(result: dict[str, Any]) -> bool:
    metrics = result["metrics"]
    return all(
        not metrics[key]
        for key in (
            "critical_atomicity_false_pass_cases",
            "critical_role_false_pass_cases",
            "required_atomicity_false_reject_cases",
            "required_role_false_reject_cases",
            "required_repeatability_failure_cases",
        )
    )


def _validate_result(candidate: dict[str, Any], result: dict[str, Any]) -> None:
    candidate_id = candidate["candidate_id"]
    if result.get("corpus_sha256") != EXPECTED_GOLD_SHA256:
        raise RuntimeError(f"Gold SHA mismatch for {candidate_id}")
    if result.get("repeats") != 3:
        raise RuntimeError(f"Repeat count mismatch for {candidate_id}")
    if result.get("model") != candidate["lm_studio_alias"]:
        raise RuntimeError(f"Model alias mismatch for {candidate_id}")
    cases = result.get("cases", [])
    if len(cases) != 47:
        raise RuntimeError(f"Case count mismatch for {candidate_id}")
    if sum(bool(case.get("required")) for case in cases) != 41:
        raise RuntimeError(f"Required count mismatch for {candidate_id}")


def _required_agreement(
    primary: dict[str, Any],
    secondary: dict[str, Any],
) -> dict[str, Any]:
    primary_cases = {
        case["case_id"]: case for case in primary["cases"] if case["required"]
    }
    secondary_cases = {
        case["case_id"]: case for case in secondary["cases"] if case["required"]
    }
    if set(primary_cases) != set(secondary_cases) or len(primary_cases) != 41:
        raise RuntimeError("Required case mismatch between primary and secondary")

    atomicity = 0
    role = 0
    joint = 0
    total = 0
    differences: list[dict[str, Any]] = []
    for case_id in sorted(primary_cases):
        left = primary_cases[case_id]["repeats"]
        right = secondary_cases[case_id]["repeats"]
        if len(left) != 3 or len(right) != 3:
            raise RuntimeError(f"Repeat count mismatch for required case {case_id}")
        for index, (primary_repeat, secondary_repeat) in enumerate(
            zip(left, right),
            start=1,
        ):
            total += 1
            atomic_match = (
                primary_repeat["atomicity_verdict"]
                == secondary_repeat["atomicity_verdict"]
            )
            role_match = (
                primary_repeat["role_boundary_verdict"]
                == secondary_repeat["role_boundary_verdict"]
            )
            atomicity += int(atomic_match)
            role += int(role_match)
            joint += int(atomic_match and role_match)
            if not (atomic_match and role_match):
                differences.append(
                    {
                        "case_id": case_id,
                        "repeat": index,
                        "primary": [
                            primary_repeat["atomicity_verdict"],
                            primary_repeat["role_boundary_verdict"],
                        ],
                        "secondary": [
                            secondary_repeat["atomicity_verdict"],
                            secondary_repeat["role_boundary_verdict"],
                        ],
                    }
                )
    if total != 123:
        raise RuntimeError(f"Expected 123 required case-repeat pairs, got {total}")
    return {
        "total_required_repeat_pairs": total,
        "atomicity_identical": atomicity,
        "role_identical": role,
        "joint_identical": joint,
        "atomicity_agreement": atomicity / total,
        "role_agreement": role / total,
        "joint_agreement": joint / total,
        "differences": differences,
        "pass": atomicity == total and role == total and joint == total,
    }


def _elapsed(result: dict[str, Any]) -> float:
    return float(result["finished_epoch"]) - float(result["started_epoch"])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--primary", action="append", default=[])
    parser.add_argument("--secondary", action="append", default=[])
    parser.add_argument("--runtime-lock", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    manifest = _load(MANIFEST_PATH)
    candidates = manifest["candidates"]
    candidate_by_id = {
        candidate["candidate_id"]: candidate for candidate in candidates
    }
    primary_paths = _parse_named(args.primary)
    secondary_paths = _parse_named(args.secondary)
    runtime_lock = _load(args.runtime_lock)
    runtime_by_id = {
        item["candidate_id"]: item
        for item in runtime_lock.get("candidates", [])
    }
    if set(runtime_by_id) != set(candidate_by_id):
        raise RuntimeError(
            "Runtime lock must cover the complete frozen candidate pool"
        )

    rows: list[dict[str, Any]] = []
    finalists: list[dict[str, Any]] = []
    for candidate in candidates:
        candidate_id = candidate["candidate_id"]
        runtime = runtime_by_id[candidate_id]
        status = runtime.get("status")
        if status == "runtime_incompatible":
            if candidate_id in primary_paths or candidate_id in secondary_paths:
                raise RuntimeError(
                    "Runtime-incompatible candidate has benchmark results: "
                    f"{candidate_id}"
                )
            rows.append(
                {
                    "candidate_id": candidate_id,
                    "runtime_status": status,
                    "primary_pass": False,
                    "secondary_pass": False,
                    "selected": False,
                }
            )
            continue
        if status != "ready":
            raise RuntimeError(
                f"Unexpected runtime status for {candidate_id}: {status!r}"
            )
        if candidate_id not in primary_paths:
            raise RuntimeError(
                f"Missing primary result for ready candidate: {candidate_id}"
            )

        primary = _load(primary_paths[candidate_id])
        _validate_result(candidate, primary)
        primary_pass = _gate_pass(primary)
        row: dict[str, Any] = {
            "candidate_id": candidate_id,
            "runtime_status": status,
            "primary_pass": primary_pass,
            "primary_elapsed_seconds": _elapsed(primary),
            "model_file_size_bytes": runtime.get("model_file_size_bytes"),
            "model_sha256": runtime.get("model_sha256"),
            "primary_metrics": primary["metrics"],
            "secondary_pass": False,
            "selected": False,
        }

        if primary_pass:
            if candidate_id not in secondary_paths:
                raise RuntimeError(
                    "Missing secondary result for primary-pass candidate: "
                    f"{candidate_id}"
                )
            secondary = _load(secondary_paths[candidate_id])
            _validate_result(candidate, secondary)
            stability = _required_agreement(primary, secondary)
            secondary_gate = _gate_pass(secondary)
            row["secondary_metrics"] = secondary["metrics"]
            row["required_prompt_stability"] = stability
            row["secondary_pass"] = secondary_gate and stability["pass"]
            if row["secondary_pass"]:
                finalists.append(row)
        elif candidate_id in secondary_paths:
            raise RuntimeError(
                f"Secondary result exists for primary-fail candidate: {candidate_id}"
            )
        rows.append(row)

    selected_id: str | None = None
    if finalists:
        fastest = min(
            finalists,
            key=lambda row: row["primary_elapsed_seconds"],
        )
        fastest_elapsed = fastest["primary_elapsed_seconds"]
        within_five_percent = [
            row
            for row in finalists
            if row["primary_elapsed_seconds"] <= fastest_elapsed * 1.05
        ]
        if len(within_five_percent) == 1:
            selected = within_five_percent[0]
        else:
            manifest_order = [
                candidate["candidate_id"] for candidate in candidates
            ]
            selected = min(
                within_five_percent,
                key=lambda row: (
                    row["model_file_size_bytes"]
                    if row["model_file_size_bytes"] is not None
                    else float("inf"),
                    manifest_order.index(row["candidate_id"]),
                ),
            )
        selected_id = selected["candidate_id"]
        for row in rows:
            row["selected"] = row["candidate_id"] == selected_id

    payload = {
        "schema_version": "sgokb.n04g23ar-selection/1",
        "candidate_manifest": MANIFEST_PATH.relative_to(ROOT).as_posix(),
        "candidates": rows,
        "selected_candidate_id": selected_id,
        "outcome": "PASS_SELECTED" if selected_id else "VALID_FAIL_NO_SELECTION",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
