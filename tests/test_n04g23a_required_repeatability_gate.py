from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "benchmark" / "tools" / "n04g23a_atomicity_role_benchmark.py"


def _load_runner():
    spec = importlib.util.spec_from_file_location("n04g23a_required_gate_runner", RUNNER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_nonrequired_instability_is_reported_but_does_not_fail_gate() -> None:
    runner = _load_runner()
    results = [
        {
            "case_id": "required-stable",
            "required": True,
            "critical_for_safety": False,
            "gold": {"atomicity": "ATOMIC", "role_boundary": "ROLE_VALID"},
            "repeats": [
                {"atomicity_verdict": "ATOMIC", "role_boundary_verdict": "ROLE_VALID"},
                {"atomicity_verdict": "ATOMIC", "role_boundary_verdict": "ROLE_VALID"},
                {"atomicity_verdict": "ATOMIC", "role_boundary_verdict": "ROLE_VALID"},
            ],
        },
        {
            "case_id": "optional-ambiguous",
            "required": False,
            "critical_for_safety": False,
            "gold": {"atomicity": "INDETERMINATE", "role_boundary": "INDETERMINATE"},
            "repeats": [
                {"atomicity_verdict": "ATOMIC", "role_boundary_verdict": "INDETERMINATE"},
                {"atomicity_verdict": "INDETERMINATE", "role_boundary_verdict": "ROLE_VALID"},
                {"atomicity_verdict": "NON_ATOMIC", "role_boundary_verdict": "INDETERMINATE"},
            ],
        },
    ]

    metrics = runner._score(results)
    assert metrics["repeatability_failure_cases"] == ["optional-ambiguous"]
    assert metrics["required_repeatability_failure_cases"] == []
    assert metrics["gates"]["repeatability_gate"] is True
    assert metrics["gates"]["candidate_viable"] is True
