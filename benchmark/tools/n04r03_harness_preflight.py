from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from sgokb.mcp.tool_contracts import (
    BUILD_CONTEXT,
    FIND_SIMILAR_OBJECTS,
    MCP_READ_TOOL_CONTRACT_VERSION,
)
from sgokb.retrieval.context_builder import CONTEXT_BUILDER_CONTRACT_VERSION

CASE_IDS = [
    "n04-roleplay-saber",
    "n04-similar-work-comparison",
    "n04-concept-combination-creative",
]
EXPECTED_PURPOSES = ["roleplay", "comparison", "creative"]
EXPECTED_FORMAL_GATE_KEYS = {
    "public_boundary",
    "canonical_scope",
    "retrieval_integration",
    "context_contract",
    "traceability",
    "budget_contract",
}
EXPECTED_GLOBAL_GATE_KEYS = {"canonical_invariance", "integrity", "regression"}
FORBIDDEN_CASE_KEYS = {
    "generation",
    "prompt",
    "model_policy",
    "validation_policy",
    "generator",
    "semantic_validator",
    "atomicity",
    "content_type",
    "verifier",
    "renderer",
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _walk_keys(value: Any) -> set[str]:
    keys: set[str] = set()
    if isinstance(value, dict):
        for key, item in value.items():
            keys.add(str(key).lower())
            keys.update(_walk_keys(item))
    elif isinstance(value, list):
        for item in value:
            keys.update(_walk_keys(item))
    return keys


def evaluate(repo_root: Path) -> dict[str, Any]:
    benchmark = repo_root / "benchmark"
    cases_path = benchmark / "n04-knowledge-access-cases-v1.json"
    harness_path = benchmark / "n04-knowledge-access-formal-harness-v1.json"
    cases = load_json(cases_path)
    harness = load_json(harness_path)

    checks: list[dict[str, Any]] = []

    def check(name: str, ok: bool, detail: Any) -> None:
        checks.append({"name": name, "pass": bool(ok), "detail": detail})

    check(
        "case_spec_status",
        cases.get("status") == "frozen_for_reference_workstation_reacceptance",
        cases.get("status"),
    )
    check(
        "harness_status",
        harness.get("status") == "frozen_for_reference_workstation_reacceptance",
        harness.get("status"),
    )
    check(
        "formal_boundary",
        cases.get("formal_boundary") == "external_consumer_boundary"
        and harness.get("formal_boundary", {}).get("ends_at") == "external consumer boundary"
        and harness.get("formal_boundary", {}).get("consumer_inference_or_generation_is_gating")
        is False,
        harness.get("formal_boundary"),
    )
    check(
        "mcp_contract_version",
        cases.get("contract_versions", {}).get("mcp_read_tools")
        == MCP_READ_TOOL_CONTRACT_VERSION,
        cases.get("contract_versions"),
    )
    check(
        "context_contract_version",
        cases.get("contract_versions", {}).get("context_builder")
        == CONTEXT_BUILDER_CONTRACT_VERSION,
        cases.get("contract_versions"),
    )
    active_tools = {BUILD_CONTEXT.name, FIND_SIMILAR_OBJECTS.name}
    check(
        "required_public_tools_active",
        active_tools == {"build_context", "find_similar_objects"},
        sorted(active_tools),
    )

    case_items = cases.get("cases", [])
    case_ids = [case.get("case_id") for case in case_items]
    check("case_ids", case_ids == CASE_IDS, case_ids)

    purposes: list[str | None] = []
    case_key_violations: dict[str, list[str]] = {}
    for case in case_items:
        context = case.get("build_context") or case.get("build_context_template") or {}
        purposes.append(context.get("purpose"))
        keys = _walk_keys(case)
        violations = sorted(FORBIDDEN_CASE_KEYS.intersection(keys))
        if violations:
            case_key_violations[str(case.get("case_id"))] = violations
    check("case_purposes", purposes == EXPECTED_PURPOSES, purposes)
    check("no_consumer_generation_keys_in_cases", not case_key_violations, case_key_violations)

    comparison = case_items[1] if len(case_items) == 3 else {}
    check(
        "comparison_tool_sequence",
        comparison.get("tool_sequence") == ["find_similar_objects", "build_context"],
        comparison.get("tool_sequence"),
    )
    comparison_context = comparison.get("build_context_template", {})
    check(
        "comparison_candidate_not_hardcoded",
        comparison_context.get("object_ids", [None, None])[1]
        == "<retrieved_current_work_candidate_id>",
        comparison_context.get("object_ids"),
    )

    check(
        "formal_case_gate_set",
        set(harness.get("case_gates", {})) == EXPECTED_FORMAL_GATE_KEYS,
        sorted(harness.get("case_gates", {})),
    )
    check(
        "formal_global_gate_set",
        set(harness.get("global_gates", {})) == EXPECTED_GLOBAL_GATE_KEYS,
        sorted(harness.get("global_gates", {})),
    )
    check(
        "formal_result_states",
        harness.get("result_policy", {}).get("allowed_states") == ["PASS", "FAIL", "BLOCKED"]
        and cases.get("formal_result_states") == ["PASS", "FAIL", "BLOCKED"],
        {
            "harness": harness.get("result_policy", {}).get("allowed_states"),
            "cases": cases.get("formal_result_states"),
        },
    )
    check(
        "consumer_demo_non_gating",
        harness.get("evidence_contract", {}).get(
            "consumer_demonstration_must_not_affect_formal_verdict"
        )
        is True,
        harness.get("evidence_contract", {}).get(
            "consumer_demonstration_must_not_affect_formal_verdict"
        ),
    )
    check(
        "historical_harnesses_non_authoritative",
        harness.get("historical_harnesses_are_current_authority") is False,
        harness.get("historical_harnesses_are_current_authority"),
    )
    forbidden_dependencies = set(cases.get("forbidden_formal_dependencies", []))
    required_forbidden_dependencies = {
        "local_llm_generation",
        "consumer_output_grounding",
        "atomicity_classifier",
        "content_type_classifier",
        "source_fact_verifier",
        "interpretation_verifier",
        "grounded_generation_certification",
        "presentation_generator",
        "frozen_47_confirmation",
    }
    check(
        "old_generation_dependencies_explicitly_forbidden",
        forbidden_dependencies == required_forbidden_dependencies,
        sorted(forbidden_dependencies),
    )

    failed = [item["name"] for item in checks if not item["pass"]]
    return {
        "task": "N-04R-03",
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
