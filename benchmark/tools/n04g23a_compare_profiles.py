"""Compare N-04G-23A result files for prompt/split stability diagnostics."""

from __future__ import annotations

import argparse
import json
from itertools import combinations
from pathlib import Path
from typing import Any


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _case_map(result: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {case["case_id"]: case for case in result["cases"]}


def _verdict_pairs(case: dict[str, Any]) -> list[tuple[str, str]]:
    return [
        (repeat["atomicity_verdict"], repeat["role_boundary_verdict"]) for repeat in case["repeats"]
    ]


def _pair_compare(
    left_name: str,
    left: dict[str, Any],
    right_name: str,
    right: dict[str, Any],
) -> dict[str, Any]:
    if left["corpus_sha256"] != right["corpus_sha256"]:
        raise ValueError(f"Corpus SHA mismatch: {left_name} vs {right_name}")
    left_cases = _case_map(left)
    right_cases = _case_map(right)
    if set(left_cases) != set(right_cases):
        raise ValueError(f"Case ID mismatch: {left_name} vs {right_name}")

    atomic_equal = 0
    role_equal = 0
    joint_equal = 0
    total = 0
    differences: list[dict[str, Any]] = []

    for case_id in sorted(left_cases):
        left_pairs = _verdict_pairs(left_cases[case_id])
        right_pairs = _verdict_pairs(right_cases[case_id])
        if len(left_pairs) != len(right_pairs):
            raise ValueError(f"Repeat count mismatch for {case_id}: {left_name} vs {right_name}")
        case_diff: list[dict[str, Any]] = []
        for index, (left_pair, right_pair) in enumerate(zip(left_pairs, right_pairs), start=1):
            total += 1
            atomic_match = left_pair[0] == right_pair[0]
            role_match = left_pair[1] == right_pair[1]
            atomic_equal += int(atomic_match)
            role_equal += int(role_match)
            joint_equal += int(atomic_match and role_match)
            if not (atomic_match and role_match):
                case_diff.append(
                    {
                        "repeat": index,
                        "left": {
                            "atomicity": left_pair[0],
                            "role_boundary": left_pair[1],
                        },
                        "right": {
                            "atomicity": right_pair[0],
                            "role_boundary": right_pair[1],
                        },
                    }
                )
        if case_diff:
            differences.append({"case_id": case_id, "differences": case_diff})

    return {
        "left": left_name,
        "right": right_name,
        "total_repeat_pairs": total,
        "atomicity_agreement": atomic_equal / total if total else 0.0,
        "role_agreement": role_equal / total if total else 0.0,
        "joint_agreement": joint_equal / total if total else 0.0,
        "difference_cases": differences,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--result",
        action="append",
        required=True,
        help="Named result in NAME=PATH form. Supply at least two.",
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    named: dict[str, dict[str, Any]] = {}
    for item in args.result:
        if "=" not in item:
            raise ValueError("--result must use NAME=PATH")
        name, raw_path = item.split("=", 1)
        if not name or name in named:
            raise ValueError(f"Invalid or duplicate result name: {name!r}")
        named[name] = _load(Path(raw_path))
    if len(named) < 2:
        raise ValueError("At least two --result entries are required")

    comparisons = [
        _pair_compare(left_name, named[left_name], right_name, named[right_name])
        for left_name, right_name in combinations(named, 2)
    ]
    payload = {
        "schema_version": "sgokb.n04g23a-profile-comparison/1",
        "profiles": {
            name: {
                "profile_id": result["profile_id"],
                "corpus_sha256": result["corpus_sha256"],
                "gates": result["metrics"]["gates"],
                "indeterminate_rate": result["metrics"]["indeterminate_rate"],
            }
            for name, result in named.items()
        },
        "comparisons": comparisons,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
