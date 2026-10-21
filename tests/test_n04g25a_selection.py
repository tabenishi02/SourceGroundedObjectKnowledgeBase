"""Selection cannot bypass frozen policies, complete repeats, or zero-error Gates."""

from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "benchmark/tools"


def module(name):
    # Explicit local module path; ML dependencies remain lazy and isolated.
    previous = sys.path[:]
    try:
        sys.path.insert(0, str(TOOLS))
        spec = importlib.util.spec_from_file_location(name, TOOLS / f"{name}.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    finally:
        sys.path[:] = previous


SELECTOR = module("n04g25a_select_development")
RUNNER = module("n04g25a_run_selection")


def read(name):
    return json.loads((ROOT / "benchmark" / name).read_text(encoding="utf-8"))


def test_all_candidate_task_policies_are_committed_before_selection():
    frozen = read("n04g25a-development-policy-lock-v1.json")
    manifest = read("n04g25a-candidate-manifest-v1.json")
    assert RUNNER.verify_freeze(frozen, manifest, artifacts=False)
    assert len(frozen["locks"]) == 8
    assert frozen["confirmation_started"] is False
    assert all(
        c["status"] == "runtime_compatible_training_validation_pass" for c in manifest["candidates"]
    )


@pytest.mark.parametrize(
    "defect",
    [
        "missing",
        "duplicate",
        "classes",
        "partition",
        "threshold",
        "artifacts",
        "confirmation",
        "selection",
    ],
)
def test_selection_refuses_missing_or_changed_preselection_policy(defect):
    frozen = copy.deepcopy(read("n04g25a-development-policy-lock-v1.json"))
    manifest = read("n04g25a-candidate-manifest-v1.json")
    if defect == "missing":
        frozen["locks"].pop()
    elif defect == "duplicate":
        frozen["locks"][-1] = frozen["locks"][0]
    elif defect == "classes":
        frozen["locks"][0]["classes"].reverse()
    elif defect == "partition":
        frozen["locks"][0]["fit_partition"] = "selection"
    elif defect == "threshold":
        frozen["locks"][0]["policy"]["min_confidence"] = 0.1234
    elif defect == "artifacts":
        frozen["locks"][0]["artifacts"] = {}
    elif defect == "confirmation":
        frozen["confirmation_started"] = True
    else:
        frozen["selection_started"] = True
    with pytest.raises(ValueError):
        RUNNER.verify_freeze(frozen, manifest, artifacts=False)


def candidate(cid, task, passed=True, **ranking):
    return {
        "candidate_id": cid,
        "task": task,
        "status": "completed",
        "hard_gate": "PASS" if passed else "FAIL",
        "critical_false_pass": 0 if passed else 1,
        "required_valid_false_reject": 0,
        "repeatability_failures": 0,
        "ranking_metrics": {
            "nonambiguous_ambiguity_rate": 0.0,
            "macro_f1": 1.0,
            "mean_class_recall": 1.0,
            "median_amortized_latency_seconds": 0.01,
            "peak_allocated_vram_bytes": 100,
            "artifact_bytes": 200,
            **ranking,
        },
    }


def test_failed_candidate_is_never_selected_despite_better_ranking_metrics():
    results = [
        candidate(
            cid,
            task,
            passed=cid == "slow",
            median_amortized_latency_seconds=100 if cid == "slow" else 0,
        )
        for cid in ["fast", "slow"]
        for task in ["atomicity", "content_type"]
    ]
    result = SELECTOR.select(results, ["fast", "slow"])
    assert result["selected"] == {"atomicity": "slow", "content_type": "slow"}
    assert result["outcome"] == "DEVELOPMENT_PAIR_PASS"
    assert result["G25A_complete"] is False
    assert result["confirmation_started"] is False


def test_task_specific_winners_and_manifest_order_tiebreak_are_deterministic():
    results = [
        candidate(cid, task) for cid in ["one", "two"] for task in ["atomicity", "content_type"]
    ]
    results[1]["ranking_metrics"]["nonambiguous_ambiguity_rate"] = 0.1
    result = SELECTOR.select(results, ["one", "two"])
    assert result["selected"] == {"atomicity": "one", "content_type": "two"}


def test_partial_and_all_failure_cannot_become_pair_pass():
    results = [candidate("one", "atomicity"), candidate("one", "content_type", passed=False)]
    assert SELECTOR.select(results, ["one"])["outcome"] == "VALID_FAIL_NO_SELECTION"
    results[0] = candidate("one", "atomicity", passed=False)
    assert SELECTOR.select(results, ["one"])["selected"] == {
        "atomicity": None,
        "content_type": None,
    }
    with pytest.raises(ValueError, match="Complete unique"):
        SELECTOR.select(results[:1], ["one"])


def test_all_three_repeats_must_pass_every_hard_gate():
    rows = [
        {
            "label": "NON_ATOMIC",
            "family_id": "fixture",
            "required": True,
            "critical_for_safety": True,
        }
    ]
    result = SELECTOR.evaluate(
        "atomicity",
        rows,
        [["NON_ATOMIC"], ["NON_ATOMIC"], ["ATOMIC"]],
        ["ATOMIC", "NON_ATOMIC", "AMBIGUOUS"],
        [0.1, 0.1, 0.1],
        100,
        200,
    )
    assert result["hard_gate"] == "FAIL"
    assert result["critical_false_pass"] == 1
    assert result["repeatability_failures"] == 1
