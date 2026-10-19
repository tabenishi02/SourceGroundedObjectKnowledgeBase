from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from sgokb.grounding.output import generation_output_schema_hash

FROZEN_CASE_IDS = [
    "n04-roleplay-saber",
    "n04-similar-work-comparison",
    "n04-concept-combination-creative",
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def evaluate(repo_root: Path) -> dict[str, Any]:
    benchmark = repo_root / "benchmark"
    harness_path = benchmark / "n04-v3-formal-harness-v1.json"
    acceptance_path = benchmark / "n04-ai-use-cases-v3.json"
    material_path = benchmark / "n04-v3-material-profiles-v1.json"
    verifier_path = benchmark / "n04-v3-source-fact-verifier-profile-v1.json"

    harness = load_json(harness_path)
    acceptance = load_json(acceptance_path)
    material = load_json(material_path)
    verifier = load_json(verifier_path)

    checks: list[dict[str, Any]] = []

    def check(name: str, ok: bool, detail: Any) -> None:
        checks.append({"name": name, "pass": bool(ok), "detail": detail})

    check("harness_status_frozen", harness.get("status") == "frozen", harness.get("status"))
    check(
        "acceptance_status_frozen",
        acceptance.get("status") == "frozen",
        acceptance.get("status"),
    )
    check("material_status_frozen", material.get("status") == "frozen", material.get("status"))
    check("verifier_status_frozen", verifier.get("status") == "frozen", verifier.get("status"))

    actual_acceptance_sha = sha256_file(acceptance_path)
    actual_material_sha = sha256_file(material_path)
    actual_verifier_sha = sha256_file(verifier_path)
    check(
        "acceptance_file_sha256",
        actual_acceptance_sha == harness["acceptance_spec"]["sha256"],
        {"actual": actual_acceptance_sha, "expected": harness["acceptance_spec"]["sha256"]},
    )
    check(
        "material_file_sha256",
        actual_material_sha == harness["material_profiles"]["file_sha256"],
        {"actual": actual_material_sha, "expected": harness["material_profiles"]["file_sha256"]},
    )
    check(
        "verifier_file_sha256",
        actual_verifier_sha == harness["source_fact_verifier_profile"]["file_sha256"],
        {
            "actual": actual_verifier_sha,
            "expected": harness["source_fact_verifier_profile"]["file_sha256"],
        },
    )

    proof = harness.get("reference_workstation_proof", {})
    proof_path_value = proof.get("path")
    proof_path = repo_root / str(proof_path_value) if proof_path_value else None
    proof_exists = bool(proof_path and proof_path.exists())
    check("reference_workstation_proof_present", proof_exists, proof_path_value)
    if proof_exists and proof_path is not None:
        actual_proof_sha = sha256_file(proof_path)
        check(
            "reference_workstation_proof_sha256",
            actual_proof_sha == proof.get("sha256"),
            {"actual": actual_proof_sha, "expected": proof.get("sha256")},
        )
    else:
        check("reference_workstation_proof_sha256", False, "proof file missing")

    verifier_screening = verifier.get("screening_evidence", {})
    verifier_proof = verifier_screening.get("reference_workstation_result", {})
    check(
        "verifier_reference_workstation_reproduction",
        verifier_screening.get("reference_workstation_reproduction") is True,
        verifier_screening.get("reference_workstation_reproduction"),
    )
    check(
        "verifier_proof_binding_matches_harness",
        verifier_proof.get("path") == proof.get("path")
        and verifier_proof.get("sha256") == proof.get("sha256")
        and verifier_proof.get("run_id") == proof.get("run_id"),
        {"verifier": verifier_proof, "harness": proof},
    )

    unresolved = harness.get("unresolved_before_freeze")
    check("unresolved_before_freeze_empty", unresolved == [], unresolved)

    schema_expected = harness["lm_studio"]["structured_output"]["provider_schema_sha256"]
    schema_actual = generation_output_schema_hash()
    check(
        "generation_output_schema_hash",
        schema_actual == schema_expected,
        {"actual": schema_actual, "expected": schema_expected},
    )

    case_ids = [case.get("case_id") for case in acceptance.get("cases", [])]
    check("frozen_case_ids", case_ids == FROZEN_CASE_IDS, case_ids)
    check(
        "formal_three_case_gate",
        acceptance.get("overall_gate", {}).get("three_case_requirement") == "3/3 formal Case PASS",
        acceptance.get("overall_gate", {}).get("three_case_requirement"),
    )
    check(
        "formal_case_terminal_accepted",
        acceptance.get("common_rules", {}).get("formal_case_pass_terminal") == "ACCEPTED",
        acceptance.get("common_rules", {}).get("formal_case_pass_terminal"),
    )
    check(
        "critical_unsupported_claims_zero",
        acceptance.get("common_rules", {}).get("critical_unsupported_rendered_claims_allowed") == 0,
        acceptance.get("common_rules", {}).get("critical_unsupported_rendered_claims_allowed"),
    )

    failed = [item["name"] for item in checks if not item["pass"]]
    return {
        "task": "N-04G-22",
        "preflight": "PASS" if not failed else "FAIL",
        "failed_checks": failed,
        "checks": checks,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = evaluate(args.repo_root.resolve())
    rendered = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if report["preflight"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
