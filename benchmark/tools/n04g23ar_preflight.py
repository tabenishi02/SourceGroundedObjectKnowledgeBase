"""Preflight checks for N-04G-23A-R Judge Candidate Evaluation."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

EXPECTED_GOLD_SHA256 = "347e39f5108ed920847ce717cf98571a5137c48e348aba7af7e5aa50679a4687"
EXPECTED_G23A_PROFILES_SHA256 = "a10b9216d6ead15927c23b015ac3d2863c10dfaa6797f3ede72bef51e58ba89e"
EXPECTED_CANDIDATES = [
    "qwen35-9b-q6k",
    "ministral3-8b-q6k",
    "gemma4-12b-q6k",
    "mistral32-24b-q4km",
]
EXPECTED_RUNTIME = {
    "context_length": 8192,
    "gpu_offload": "max",
    "parallel": 1,
    "temperature": 0,
    "max_tokens": 64,
    "seed": 20261018,
    "stream": False,
    "repeats": 3,
}


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def _profile_by_id(payload: dict[str, Any], profile_id: str) -> dict[str, Any]:
    for profile in payload.get("profiles", []):
        if profile.get("profile_id") == profile_id:
            return profile
    raise RuntimeError(f"Missing profile: {profile_id}")


def run(repo_root: Path) -> dict[str, Any]:
    gold_path = repo_root / "benchmark" / "n04g23a-atomicity-role-gold-v1.json"
    g23a_profiles_path = (
        repo_root / "benchmark" / "n04g23a-atomicity-role-prompt-profiles-v1.json"
    )
    candidates_path = repo_root / "benchmark" / "n04g23ar-judge-candidates-v1.json"
    paraphrase_path = repo_root / "benchmark" / "n04g23ar-split-paraphrase-profile-v1.json"

    gold_sha = _sha256(gold_path)
    g23a_profiles_sha = _sha256(g23a_profiles_path)
    candidates_sha = _sha256(candidates_path)
    paraphrase_sha = _sha256(paraphrase_path)

    _require(gold_sha == EXPECTED_GOLD_SHA256, "Frozen G-23A Gold corpus SHA mismatch")
    _require(
        g23a_profiles_sha == EXPECTED_G23A_PROFILES_SHA256,
        "Frozen G-23A prompt profile SHA mismatch",
    )

    gold = _load(gold_path)
    profiles = _load(g23a_profiles_path)
    manifest = _load(candidates_path)
    paraphrase = _load(paraphrase_path)

    cases = gold.get("cases", [])
    _require(gold.get("status") == "frozen_for_execution", "Gold corpus is not frozen")
    _require(len(cases) == 47, "Gold corpus must contain exactly 47 cases")
    _require(sum(bool(case.get("required")) for case in cases) == 41, "Expected 41 required cases")
    _require(sum(not bool(case.get("required")) for case in cases) == 6, "Expected 6 optional cases")
    _require(
        all(
            "INDETERMINATE" not in case["gold"].values()
            for case in cases
            if case.get("required")
        ),
        "Required Gold contains INDETERMINATE",
    )

    split = _profile_by_id(profiles, "split-v1")
    _require(split.get("mode") == "split", "G-23A split-v1 is no longer split mode")
    _require(split.get("status") == "ready", "G-23A split-v1 is not ready")
    base_runtime = profiles.get("runtime", {})
    for key in ("temperature", "max_tokens", "seed"):
        _require(
            base_runtime.get(key) == EXPECTED_RUNTIME[key],
            f"G-23A runtime mismatch for {key}",
        )

    _require(
        manifest.get("schema_version") == "sgokb.n04g23ar-judge-candidates/1",
        "Unexpected candidate manifest schema",
    )
    _require(
        manifest.get("base_main") == "cfbd7af9663f4cbe5c4acfa9a71d34649b385a48",
        "Candidate manifest base_main changed",
    )
    authority = manifest.get("authority", {})
    _require(
        authority.get("gold_corpus_sha256") == EXPECTED_GOLD_SHA256,
        "Manifest Gold SHA authority mismatch",
    )
    _require(
        authority.get("exact_split_profile_set_sha256") == EXPECTED_G23A_PROFILES_SHA256,
        "Manifest split profile SHA authority mismatch",
    )
    _require(authority.get("exact_split_profile_id") == "split-v1", "Primary profile changed")

    candidate_ids = [candidate.get("candidate_id") for candidate in manifest.get("candidates", [])]
    _require(candidate_ids == EXPECTED_CANDIDATES, "Candidate set or order changed")
    _require(len(candidate_ids) == len(set(candidate_ids)), "Duplicate candidate id")
    _require(
        all("phi-4" not in str(candidate.get("original_model", "")).lower() for candidate in manifest["candidates"]),
        "Phi-4 must not be reintroduced as an alternative candidate",
    )
    runtime_policy = manifest.get("runtime_policy", {})
    for key, value in EXPECTED_RUNTIME.items():
        _require(runtime_policy.get(key) == value, f"Manifest runtime mismatch for {key}")

    primary = manifest.get("primary_gate", {})
    for key in (
        "critical_atomicity_false_pass_cases",
        "critical_role_false_pass_cases",
        "required_atomicity_false_reject_cases",
        "required_role_false_reject_cases",
        "required_repeatability_failure_cases",
    ):
        _require(primary.get(key) == 0, f"Primary Gate relaxed: {key}")

    secondary = manifest.get("secondary_gate", {})
    _require(
        secondary.get("required_exact_vs_paraphrase_atomicity_agreement") == "100% across all required case-repeat pairs",
        "Atomicity paraphrase stability Gate changed",
    )
    _require(
        secondary.get("required_exact_vs_paraphrase_role_agreement") == "100% across all required case-repeat pairs",
        "Role paraphrase stability Gate changed",
    )
    _require(
        secondary.get("required_exact_vs_paraphrase_joint_agreement") == "100% across all required case-repeat pairs",
        "Joint paraphrase stability Gate changed",
    )

    _require(
        paraphrase.get("status") == "frozen_for_execution",
        "Paraphrase profile is not frozen",
    )
    para_profile = _profile_by_id(paraphrase, "split-paraphrase-a")
    _require(para_profile.get("mode") == "split", "Paraphrase profile must use split calls")
    _require(para_profile.get("status") == "ready", "Paraphrase profile is not ready")
    para_runtime = paraphrase.get("runtime", {})
    for key in ("temperature", "max_tokens", "seed", "stream"):
        _require(
            para_runtime.get(key) == EXPECTED_RUNTIME[key],
            f"Paraphrase runtime mismatch for {key}",
        )

    for section, verdict_key, expected_values in (
        ("atomicity", "atomicity_verdict", {"ATOMIC", "NON_ATOMIC", "INDETERMINATE"}),
        ("role", "role_boundary_verdict", {"ROLE_VALID", "ROLE_VIOLATION", "INDETERMINATE"}),
    ):
        schema = para_profile[section]["response_format"]["json_schema"]
        _require(schema.get("strict") is True, f"{section} schema is not strict")
        values = set(schema["schema"]["properties"][verdict_key]["enum"])
        _require(values == expected_values, f"{section} verdict enum changed")

    return {
        "status": "PASS",
        "gold_sha256": gold_sha,
        "g23a_profiles_sha256": g23a_profiles_sha,
        "candidate_manifest_sha256": candidates_sha,
        "paraphrase_profile_sha256": paraphrase_sha,
        "candidate_ids": candidate_ids,
        "case_count": len(cases),
        "required_count": 41,
        "optional_count": 6,
        "primary_profile": "split-v1",
        "secondary_profile": "split-paraphrase-a",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    payload = run(args.repo_root.resolve())
    rendered = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
