"""Deterministic frozen N-06 gates; incomplete evidence is never PASS."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def recall_at_10(found, exact):
    if len(exact) != 10 or len(set(exact)) != 10:
        raise ValueError("Exact reference must contain ten distinct IDs")
    return len(set(found[:10]) & set(exact)) / 10


def evaluate(evidence, contract, *, require_post_run=True):
    missing = [
        key
        for key in ("ABCDEFGH" if require_post_run else "ABCDEFG")
        if key not in evidence.get("stages", {})
    ]
    blocked = [
        key for key, value in evidence.get("stages", {}).items() if value.get("status") == "BLOCKED"
    ]
    if missing or blocked:
        return {
            "overall": "BLOCKED",
            "missing_stages": missing,
            "blocked_stages": blocked,
            "reason": evidence.get("blocker"),
        }
    checks = {}

    def minimum(name, value, threshold):
        checks[name] = (
            isinstance(value, (int, float)) and math.isfinite(value) and value >= threshold
        )

    def exact(name, value, target):
        checks[name] = value == target

    try:
        stages = evidence["stages"]
        b, c, f = stages["B"], stages["C"], stages["F"]
        for key, target in contract["synthetic_search"]["gates"].items():
            if key in {"unexplained_negative_comparable_deltas", "active_object_overall_leakage"}:
                exact("synthetic." + key, b["gates"][key], target)
            else:
                minimum("synthetic." + key, b["gates"][key], target)
        for key, target in contract["real_data"]["gates"].items():
            exact("real." + key, c["gates"][key], target)
        exact("synthetic.contracts", b["contracts"]["passed"], b["contracts"]["total"])
        exact("synthetic.nonempty_contracts", b["contracts"]["total"], 5)
        exact("synthetic.similarity", b["similarity_passed"], 4)
        exact("synthetic.evidence", b["evidence_passed"], 6)
        exact("ann.indexed_points", f["indexed_points"], contract["ann_100k"]["points"])
        for mode in ("unfiltered", "filtered"):
            cases = f[mode]["cases"]
            values = [recall_at_10(row["ann_ids"], row["exact_ids"]) for row in cases]
            exact("ann." + mode + ".case_count", len(cases), 72)
            minimum("ann." + mode + ".mean", sum(values) / len(values), 0.99)
            minimum("ann." + mode + ".min", min(values), 0.90)
        exact("ann.identity", f["identity_violations"], 0)
        exact("ann.profile", f["profile"], contract["ann_100k"]["qdrant"])
        for name in ("initial_build_seconds", "full_rebuild_seconds", "update_100_seconds"):
            minimum("ann." + name, f[name], 0)
        for model in contract["reranker"]["models"]:
            exact(
                "reranker." + model + ".revision",
                stages["E"][model]["revision"],
                contract["reranker"]["models"][model]["revision"],
            )
            exact("reranker." + model + ".cases", len(stages["E"][model]["cases"]), 22)
        exact("ablation.statement_enabled", stages["D"]["direct_statement_search_enabled"], True)
        if require_post_run:
            required_safety = {
                "canonical_unchanged",
                "preserved_n03_unchanged",
                "reference_qdrant_unchanged",
                "head_unchanged",
                "tracked_unchanged",
                "r1_unchanged",
            }
            exact("safety.complete", set(stages["H"]["safety"]), required_safety)
            exact(
                "regression.complete",
                set(stages["H"]["regression"]),
                {"focused", "full", "ruff", "diff"},
            )
            for name, value in stages["H"]["safety"].items():
                exact("safety." + name, value, True)
            for name, value in stages["H"]["regression"].items():
                exact("regression." + name, value, 0)
        exact("preflight", stages["A"]["status"], "PASS")
    except (KeyError, TypeError, ValueError, ZeroDivisionError) as exc:
        return {
            "overall": "BLOCKED",
            "reason": "Invalid/incomplete evidence: " + str(exc),
            "checks": checks,
        }
    return {
        "overall": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "failed_checks": [k for k, v in checks.items() if not v],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    evidence = json.loads(args.evidence.read_text(encoding="utf-8"))
    contract = json.loads(
        (ROOT / "benchmark/n06-retrieval-vector-quality-contract-v1.json").read_text(
            encoding="utf-8"
        )
    )
    result = evaluate(evidence, contract)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return {"PASS": 0, "FAIL": 1, "BLOCKED": 2}[result["overall"]]


if __name__ == "__main__":
    raise SystemExit(main())
