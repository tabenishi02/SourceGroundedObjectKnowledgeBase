"""Frozen N-07 contract evaluator; capability gaps are FAIL, not missing evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

CONTRACT = Path(__file__).resolve().parents[1] / "n07-failure-recovery-contract-v1.json"


def evaluate(evidence: dict, contract: dict | None = None) -> dict:
    contract = contract or json.loads(CONTRACT.read_text(encoding="utf-8"))
    failures, blocked = [], []
    for stage, names in contract["stages"].items():
        for name in names:
            case = evidence.get("cases", {}).get(name, {})
            status = case.get("status", "BLOCKED")
            if name == "controlled_process_termination_supporting_case" and status == "BLOCKED":
                continue
            if status == "FAIL":
                failures.append(name)
            elif status != "PASS":
                blocked.append(name)
    for name, expected in contract["hard_gates"].items():
        actual = evidence.get("gates", {}).get(name)
        if actual is None:
            blocked.append("gate:" + name)
        elif name in {"rpo_hours_max", "rto_hours_max"}:
            if not isinstance(actual, (int, float)) or actual > expected or actual < 0:
                failures.append("gate:" + name)
        elif type(actual) is not type(expected) or actual != expected:
            failures.append("gate:" + name)
    for name in ["preflight", "post_regression", "safety"]:
        status = evidence.get(name, {}).get("status")
        if status == "FAIL":
            failures.append(name)
        elif status != "PASS":
            blocked.append(name)
    # A valid requirement failure is decisive even if other work is incomplete.
    return {
        "overall": "FAIL" if failures else "BLOCKED" if blocked else "PASS",
        "failures": sorted(set(failures)),
        "blocked": sorted(set(blocked)),
        "contract_schema": contract["schema_version"],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = evaluate(json.loads(args.evidence.read_text(encoding="utf-8")))
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
