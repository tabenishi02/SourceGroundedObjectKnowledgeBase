"""Deterministic Phase N authority/state/compatibility audit; no product-data writes."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = "benchmark/phase-n-closure-audit-contract-v1.json"
PREP = "docs/planning/phases/N/PHASE_N_PREPARATION.md"
TASKS = "docs/planning/project/KNOWLEDGE_BASE_REDESIGN_TASKS.md"
N05_RESULT = "benchmark/results/n05d04r2-r2-09-performance-acceptance.json"
N05_DOC = "docs/evaluation/N05D04R2_R2_09_PERFORMANCE_ACCEPTANCE_RESULT.md"
N06 = "benchmark/results/n06-retrieval-vector-quality.json"
R01 = "benchmark/results/n07-r01-composite-backup-restore.json"
OLD = "benchmark/results/n07-failure-recovery.json"
START, END = "<!-- phase-n-current:start -->", "<!-- phase-n-current:end -->"


def git(*parts):
    return subprocess.check_output(["git", *parts], cwd=ROOT, encoding="utf-8").strip()


def current_block(text):
    if text.count(START) != 1 or text.count(END) != 1:
        raise ValueError("One explicit current-authority block is required")
    return text.split(START, 1)[1].split(END, 1)[0]


def static_audit(root=ROOT):
    contract = json.loads((root / CONTRACT_PATH).read_text(encoding="utf-8"))
    gates = {f"C{i:02}": {"checks": {}, "missing": [], "errors": []} for i in range(1, 5)}
    gates["C07"] = {"checks": {}, "missing": [], "errors": []}
    inventory = {}

    def check(gate, name, actual):
        gates[gate]["checks"][name] = bool(actual)

    def read(relative, gate):
        path = root / relative
        if not path.is_file():
            gates[gate]["missing"].append(relative)
            return None
        data = path.read_bytes()
        inventory[relative] = {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
        try:
            return data.decode("utf-8").replace("\r\n", "\n")
        except UnicodeDecodeError:
            gates[gate]["errors"].append("Invalid UTF-8: " + relative)
            return None

    def load(relative, gate):
        value = read(relative, gate)
        if value is None:
            return None
        try:
            result = json.loads(value)
            if not isinstance(result, dict):
                raise ValueError("Object required")
            return result
        except (ValueError, TypeError):
            gates[gate]["errors"].append("Invalid JSON object: " + relative)
            return None

    texts, aggregates = {}, {}
    for authority in contract["authorities"]:
        name = authority["task"]
        value = read(authority["path"], "C02")
        if value is not None:
            texts[name] = value
        if authority.get("aggregate"):
            aggregates[name] = load(authority["aggregate"], "C02")
    for name in ["N-01", "N-02", "N-03", "N-04R-05"]:
        text = texts.get(name, "")
        check("C01", name, bool(re.search(r"Status:.*Complete", text[:1600])))
    check("C01", "N-04", "Complete / PASS" in texts.get("N-04", "")[:1600])
    check("C01", "N-05", bool(re.search(r"N-05\s*=\s*Complete / PASS", texts.get("N-05", ""))))
    check("C01", "N-06", "N-06 = **Complete / PASS**" in texts.get("N-06", ""))
    check(
        "C01",
        "N07-R01 review",
        "ChatGPT independently compared" in texts.get("N07-R01", "")
        and "N07-R01 = Complete / PASS" in texts.get("N07-R01", ""),
    )
    expected = {f"N-0{i}": "Complete" if i <= 3 else "Complete / PASS" for i in range(1, 8)}
    expected["N07-R01"] = "Complete / PASS"
    for relative in contract["gates"]["C04_documentation_state"]["reconcile_paths"]:
        text = read(relative, "C04")
        if text is None:
            continue
        try:
            block = current_block(text)
        except ValueError as exc:
            gates["C04"]["errors"].append(relative + ": " + str(exc))
            continue
        statuses = dict(re.findall(r"^([A-Za-z0-9 -]+) = (.+)$", block, re.M))
        if relative in {PREP, TASKS}:
            for name, state in expected.items():
                check("C04", relative + ":" + name, statuses.get(name) == state)
            check("C04", relative + ":Phase N", statuses.get("Phase N") == "Active / Not Complete")
        else:
            for name in ("N-07", "N07-R01"):
                check(
                    "C04",
                    relative + ":" + name,
                    statuses.get(name, "").startswith("Complete / PASS")
                    and not any(
                        x in statuses.get(name, "") for x in ["FAIL", "Pending", "Not Started"]
                    ),
                )
        check(
            "C04",
            relative + ":no unresolved required task",
            not any(
                re.match(r"N(?:-0[1-7]|07-R01) = .*?(?:FAIL|BLOCKED|Pending|Not Started)", line)
                for line in block.splitlines()
            ),
        )
    prep = (root / PREP).read_text(encoding="utf-8") if (root / PREP).exists() else ""
    task_text = (root / TASKS).read_text(encoding="utf-8") if (root / TASKS).exists() else ""
    for i in range(1, 8):
        rows = re.findall(r"^\| N-0" + str(i) + r" \|(.+)$", prep, re.M)
        check(
            "C04",
            f"current task table N-0{i}",
            bool(rows)
            and all(
                "Complete" in row
                and not any(value in row for value in ["Pending", "Ready", "Active", "BLOCKED"])
                for row in rows
            ),
        )
        check(
            "C04",
            f"project checklist N-0{i}",
            bool(re.search(r"^- \[x\] \*\*N-0" + str(i) + r" ", task_text, re.M)),
        )
    check("C01", "N-07 after remediation", "N-07 = Complete / PASS" in prep)
    base = contract["base_candidate"]
    check(
        "C02",
        "accepted result ancestor",
        subprocess.run(
            ["git", "merge-base", "--is-ancestor", base, "HEAD"], cwd=ROOT, capture_output=True
        ).returncode
        == 0,
    )
    for relative in [N06, R01, OLD]:
        text = read(relative, "C02")
        if text is not None:
            original = subprocess.check_output(["git", "show", f"{base}:{relative}"], cwd=ROOT)
            check(
                "C02",
                "unchanged accepted/historical aggregate:" + relative,
                original.decode("utf-8").replace("\r\n", "\n") == text,
            )
    old_doc = next(a["path"] for a in contract["authorities"] if a["task"] == "N-07-historical")
    if old_doc in inventory:
        check(
            "C02",
            "historical FAIL narrative unchanged",
            subprocess.check_output(
                ["git", "show", f"{base}:{old_doc}"], cwd=ROOT, encoding="utf-8"
            )
            == (root / old_doc).read_text(encoding="utf-8"),
        )
    n05, n06, r01, old = (
        load(N05_RESULT, "C02"),
        aggregates.get("N-06"),
        aggregates.get("N07-R01"),
        aggregates.get("N-07-historical"),
    )
    n05_doc = read(N05_DOC, "C02") or ""
    if all(isinstance(x, dict) for x in [n05, n06, r01, old]):
        check("C02", "N06 PASS", n06.get("overall") == "PASS")
        check(
            "C02",
            "R01 PASS",
            r01.get("overall") == "PASS"
            and r01.get("evaluation") == {"overall": "PASS", "failures": [], "blocked": []},
        )
        check(
            "C02",
            "original FAIL preserved",
            old.get("overall") == "FAIL" and old.get("case_counts") == {"PASS": 47, "FAIL": 3},
        )
        check(
            "C02", "N03 completed fixture", aggregates.get("N-03", {}).get("status") == "complete"
        )
        for label, run, source, text in [
            ("N05", n05.get("run_id"), n05.get("measured_head"), texts.get("N-05", "")),
            ("N06", n06.get("run_id"), n06.get("execution_head"), texts.get("N-06", "")),
            ("R01", r01.get("run_id"), r01.get("measured_commit"), texts.get("N07-R01", "")),
        ]:
            check(
                "C02",
                label + " run/source in authority",
                bool(run and source and run in text and source in text),
            )
            valid = bool(isinstance(source, str) and re.fullmatch(r"[0-9a-f]{40}", source))
            check(
                "C02",
                label + " measured ancestor",
                valid
                and subprocess.run(
                    ["git", "merge-base", "--is-ancestor", source, base],
                    cwd=ROOT,
                    capture_output=True,
                ).returncode
                == 0,
            )
        n04 = texts.get("N-04", "")
        source4 = re.search(r"formal input HEAD: `([0-9a-f]{40})`", n04)
        check(
            "C02",
            "N04 run/source parse",
            bool(source4 and re.search(r"Run ID.*`\d{8}T\d{6}\+0900`", n04)),
        )
        check(
            "C02",
            "N04 measured ancestor",
            bool(source4)
            and subprocess.run(
                ["git", "merge-base", "--is-ancestor", source4[1] if source4 else "invalid", base],
                cwd=ROOT,
                capture_output=True,
            ).returncode
            == 0,
        )
        compatibility = contract["accepted_compatibility"]
        check(
            "C03",
            "N05 R2 contract",
            compatibility["retrieval_contract"] in texts.get("N-05", "")
            and compatibility["retrieval_contract"] in n05_doc
            and n05.get("overall") == "PASS",
        )
        check("C03", "N05 frozen revision", compatibility["embedding_revision"] in n05_doc)
        emb = n06.get("embedding", {})
        rebuild = r01.get("derived_rebuild", {})
        for field, value in [
            ("model", compatibility["embedding_model"]),
            ("revision", compatibility["embedding_revision"]),
        ]:
            check("C03", field, emb.get(field) == value and rebuild.get(field) == value)
        family = set(compatibility["representation_families"])
        generation = n06.get("synthetic", {}).get("generation", {})
        check(
            "C03",
            "N06 family",
            set(generation.get("kinds", [])) == family and generation.get("leakage") == 0,
        )
        check(
            "C03",
            "restored R2 rebuild",
            rebuild.get("status") == "PASS"
            and set(rebuild.get("family", [])) <= family
            and "object_overview" in rebuild.get("family", [])
            and rebuild.get("object_overall_leakage") == 0
            and rebuild.get("canonical_unchanged") is True,
        )
        check(
            "C03",
            "derived outside RTO",
            "outside canonical RTO" in " ".join(r01.get("limitations", [])),
        )
        check(
            "C03",
            "production semantics unchanged since accepted remediation",
            git("rev-parse", "HEAD:src") == git("rev-parse", base + ":src"),
        )
    for task in contract["gates"]["C07_phase_o_handoff"]["tasks"]:
        check(
            "C07",
            task + " downstream unchecked",
            bool(re.search(r"^- \[ \] \*\*" + task + r" ", task_text, re.M))
            and not re.search(r"^- \[x\] \*\*" + task + r" ", task_text, re.M),
        )
    prior_project = git("show", base + ":" + TASKS)

    def phase_o(text):
        start = text.index("# Phase O")
        tail = text[start:]
        match = re.search(r"\n# (?!Phase O)", tail)
        return tail[: match.start()] if match else tail

    check("C07", "Phase O task definitions unchanged", phase_o(task_text) == phase_o(prior_project))
    for value in gates.values():
        value["status"] = (
            "FAIL"
            if value["errors"] or not all(value["checks"].values())
            else "BLOCKED"
            if value["missing"]
            else "PASS"
        )
    # Required paths absent make affected authority closure unjudgeable, not an invented PASS.
    if gates["C02"]["missing"]:
        for key in ["C01", "C02", "C03"]:
            if not gates[key]["errors"]:
                gates[key]["status"] = "BLOCKED"
    return {
        "gates": gates,
        "authority_inventory": inventory,
        "base_accepted_result": base,
        "deferred_phase_o": contract["gates"]["C07_phase_o_handoff"]["tasks"],
    }


def verdict(evidence):
    statuses = {
        name: evidence.get("gates", {}).get(name, {}).get("status", "BLOCKED")
        for name in [f"C{i:02}" for i in range(1, 8)]
    }
    return {
        "overall": "FAIL"
        if "FAIL" in statuses.values()
        else "PASS"
        if all(value == "PASS" for value in statuses.values())
        else "BLOCKED",
        "gates": statuses,
    }


def evaluate_runtime(evidence):
    """Derive runtime gates from measured commands and explicit safety comparisons."""
    regression = evidence.get("regression", {})
    safety = evidence.get("safety", {})
    required_commands = ["pytest", "ruff", "compile", "diff"]
    missing = [key for key in required_commands if key not in regression]
    checks = {key: regression.get(key, {}).get("return_code") == 0 for key in required_commands}
    tests = regression.get("pytest", {})
    checks["tests executed"] = tests.get("passed", 0) > 0
    checks["zero failed"] = tests.get("failed") == 0
    format_result = regression.get("format", {})
    format_ok = format_result.get("return_code") == 0
    if not format_ok:
        baseline = format_result.get("baseline_exception", {})
        format_ok = (
            bool(baseline.get("offenders"))
            and baseline.get("all_unchanged_since_accepted_result") is True
            and baseline.get("scoped_return_code") == 0
            and baseline.get("policy") == "handoff Step E accepted baseline exception"
        )
    checks["format"] = format_ok
    if "format" not in regression:
        missing.append("format")
    required_safety = [
        "r1_unchanged",
        "originals_unchanged",
        "reference_qdrant_unchanged",
        "head_unchanged",
        "tracked_state_unchanged",
        "main_unchanged",
        "no_run_owned_child_processes",
        "required_assets_available",
    ]
    safety_missing = [key for key in required_safety if key not in safety]
    safety_checks = {key: safety.get(key) is True for key in required_safety}
    for gate, values, absent in [("C05", checks, missing), ("C06", safety_checks, safety_missing)]:
        evidence.setdefault("gates", {})[gate] = {
            "checks": values,
            "missing": absent,
            "status": "BLOCKED" if absent else "PASS" if all(values.values()) else "FAIL",
        }
    return verdict(evidence)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--runtime-evidence", type=Path)
    args = parser.parse_args()
    evidence = static_audit()
    if args.runtime_evidence:
        runtime = json.loads(args.runtime_evidence.read_text(encoding="utf-8"))
        evidence.update({key: runtime[key] for key in ("regression", "safety")})
        evidence["evaluation"] = evaluate_runtime(evidence)
    args.output.write_text(
        json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({key: value["status"] for key, value in evidence["gates"].items()}))


if __name__ == "__main__":
    main()
