"""Closure evaluator tests retain historical failures and fail closed on contradictions."""

import json
import subprocess

import pytest

from benchmark.tools import phase_n_closure_audit as audit

HISTORICAL_CLOSURE_REF = "fb9b0d6a6f670d1b0f053148769ce8cd448ea217"


def _git_show(relative: str) -> bytes:
    return subprocess.check_output(
        ["git", "show", f"{HISTORICAL_CLOSURE_REF}:{relative}"],
        cwd=audit.ROOT,
    )


@pytest.fixture
def subject(tmp_path, monkeypatch):
    contract = json.loads(_git_show(audit.CONTRACT_PATH).decode("utf-8"))
    paths = {audit.CONTRACT_PATH, audit.PREP, audit.TASKS, audit.N05_RESULT, audit.N05_DOC}
    for authority in contract["authorities"]:
        paths.add(authority["path"])
        if authority.get("aggregate"):
            paths.add(authority["aggregate"])
    paths.update(contract["gates"]["C04_documentation_state"]["reconcile_paths"])
    for relative in paths:
        destination = tmp_path / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(_git_show(relative))

    original_git = audit.git

    def historical_git(*parts):
        mapped = tuple(
            f"{HISTORICAL_CLOSURE_REF}:src" if part == "HEAD:src" else part
            for part in parts
        )
        return original_git(*mapped)

    monkeypatch.setattr(audit, "git", historical_git)
    return tmp_path


def test_reconciled_authorities_accept_historical_failure(subject):
    result = audit.static_audit(subject)
    assert all(gate["status"] == "PASS" for gate in result["gates"].values())
    assert result["gates"]["C02"]["checks"]["original FAIL preserved"]
    assert audit.verdict(result)["overall"] == "BLOCKED"


def test_line_endings_do_not_change_git_content_identity(subject):
    for path in subject.rglob("*"):
        if path.is_file():
            path.write_bytes(path.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))
    assert all(v["status"] == "PASS" for v in audit.static_audit(subject)["gates"].values())


def test_missing_authority_is_blocked(subject):
    (subject / audit.N06).unlink()
    assert audit.static_audit(subject)["gates"]["C02"]["status"] == "BLOCKED"


def test_corrupt_aggregate_is_failure(subject):
    (subject / audit.N06).write_text("invalid JSON", encoding="utf-8")
    assert audit.static_audit(subject)["gates"]["C02"]["status"] == "FAIL"


def test_stale_current_state_is_failure(subject):
    path = subject / audit.PREP
    path.write_text(
        path.read_text(encoding="utf-8").replace("N-07 = Complete / PASS", "N-07 = Pending"),
        encoding="utf-8",
    )
    assert audit.static_audit(subject)["gates"]["C04"]["status"] == "FAIL"


def test_changed_historical_result_is_failure(subject):
    path = subject / audit.OLD
    data = json.loads(path.read_text(encoding="utf-8"))
    data["overall"] = "PASS"
    path.write_text(json.dumps(data), encoding="utf-8")
    assert audit.static_audit(subject)["gates"]["C02"]["status"] == "FAIL"


def test_incompatible_model_is_failure(subject):
    path = subject / audit.N06
    data = json.loads(path.read_text(encoding="utf-8"))
    data["embedding"]["revision"] = "other"
    path.write_text(json.dumps(data), encoding="utf-8")
    assert audit.static_audit(subject)["gates"]["C03"]["status"] == "FAIL"


def test_phase_o_cannot_start(subject):
    path = subject / audit.TASKS
    path.write_text(
        path.read_text(encoding="utf-8").replace("- [ ] **O-01 ", "- [x] **O-01 "), encoding="utf-8"
    )
    assert audit.static_audit(subject)["gates"]["C07"]["status"] == "FAIL"


def test_all_seven_gates_required_and_failure_wins():
    evidence = {"gates": {f"C{i:02}": {"status": "PASS"} for i in range(1, 8)}}
    assert audit.verdict(evidence)["overall"] == "PASS"
    evidence["gates"]["C06"]["status"] = "BLOCKED"
    assert audit.verdict(evidence)["overall"] == "BLOCKED"
    evidence["gates"]["C05"]["status"] = "FAIL"
    assert audit.verdict(evidence)["overall"] == "FAIL"


def test_runtime_evaluator_requires_real_success_and_safety():
    evidence = {"gates": {f"C{i:02}": {"status": "PASS"} for i in range(1, 8)}}
    assert audit.evaluate_runtime(evidence)["overall"] == "BLOCKED"
    evidence["regression"] = {
        key: {"return_code": 0}
        for key in ["pytest", "ruff", "compile", "diff", "format"]
    }
    evidence["regression"]["pytest"].update(passed=1, failed=0)
    evidence["safety"] = {
        key: True
        for key in [
            "r1_unchanged",
            "originals_unchanged",
            "reference_qdrant_unchanged",
            "head_unchanged",
            "tracked_state_unchanged",
            "main_unchanged",
            "no_run_owned_child_processes",
            "required_assets_available",
        ]
    }
    assert audit.evaluate_runtime(evidence)["overall"] == "PASS"
    evidence["safety"]["r1_unchanged"] = False
    assert audit.evaluate_runtime(evidence)["overall"] == "FAIL"


def test_format_exception_cannot_hide_a_new_regression():
    evidence = {
        "regression": {key: {"return_code": 0} for key in ["pytest", "ruff", "compile", "diff"]}
    }
    evidence["regression"]["pytest"].update(passed=1, failed=0)
    evidence["regression"]["format"] = {
        "return_code": 1,
        "baseline_exception": {
            "offenders": ["existing.py"],
            "all_unchanged_since_accepted_result": False,
            "scoped_return_code": 0,
            "policy": "handoff Step E accepted baseline exception",
        },
    }
    audit.evaluate_runtime(evidence)
    assert evidence["gates"]["C05"]["status"] == "FAIL"
    evidence["regression"]["format"]["baseline_exception"][
        "all_unchanged_since_accepted_result"
    ] = True
    audit.evaluate_runtime(evidence)
    assert evidence["gates"]["C05"]["status"] == "PASS"
