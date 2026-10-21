from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

MCP_CONTRACT = "sgokb.mcp-read-tools.v1"
CONTEXT_CONTRACT = "sgokb.context-builder.v1"

REQUIRED_INPUTS = (
    "case-1-roleplay/request.json",
    "case-1-roleplay/context.json",
    "case-2-comparison/similarity-request.json",
    "case-2-comparison/similarity.json",
    "case-2-comparison/context-request.json",
    "case-2-comparison/context.json",
    "case-3-creative/request.json",
    "case-3-creative/context.json",
    "canonical-before.json",
    "canonical-after.json",
    "integrity.json",
    "regression.json",
)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _data(payload: dict[str, Any]) -> dict[str, Any]:
    value = payload.get("data")
    return value if isinstance(value, dict) else payload


def _count_evidence_refs(value: Any) -> int:
    if isinstance(value, dict):
        count = 0
        evidence = value.get("evidence")
        if isinstance(evidence, list):
            count += sum(
                1
                for item in evidence
                if isinstance(item, dict) and item.get("evidence_id")
            )
        for key, item in value.items():
            if key != "evidence":
                count += _count_evidence_refs(item)
        return count
    if isinstance(value, list):
        return sum(_count_evidence_refs(item) for item in value)
    return 0


def _check_context(
    *,
    request: dict[str, Any],
    response: dict[str, Any],
    expected_ids: list[str],
    purpose: str,
    max_characters: int,
    include_attributes: bool,
    include_relations: bool,
    include_evidence_refs: bool,
) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []

    def check(name: str, ok: bool, detail: Any) -> None:
        checks.append({"name": name, "pass": bool(ok), "detail": detail})

    args = request.get("arguments", {})
    payload = _data(response)
    objects = payload.get("objects", [])
    object_ids = [item.get("object_id") for item in objects]
    policy = payload.get("selection_policy", {})
    budget = payload.get("budget", {})

    check(
        "public_tool_build_context",
        request.get("tool") == "build_context",
        request.get("tool"),
    )
    check(
        "request_object_ids",
        args.get("object_ids") == expected_ids,
        args.get("object_ids"),
    )
    check(
        "request_purpose",
        args.get("purpose") == purpose,
        args.get("purpose"),
    )
    check(
        "request_budget",
        args.get("max_characters") == max_characters,
        args.get("max_characters"),
    )
    expected_options = {
        "include_attributes": include_attributes,
        "include_relations": include_relations,
        "include_evidence_refs": include_evidence_refs,
    }
    actual_request_options = {key: args.get(key) for key in expected_options}
    check(
        "request_include_options",
        actual_request_options == expected_options,
        actual_request_options,
    )
    check(
        "mcp_contract",
        response.get("tool_contract_version") == MCP_CONTRACT,
        response.get("tool_contract_version"),
    )
    check(
        "context_contract",
        payload.get("context_contract_version") == CONTEXT_CONTRACT,
        payload.get("context_contract_version"),
    )
    check(
        "response_purpose",
        payload.get("purpose") == purpose,
        payload.get("purpose"),
    )
    check("response_object_ids", object_ids == expected_ids, object_ids)
    check(
        "current_versions",
        bool(objects)
        and all(item.get("is_current") is True for item in objects)
        and all(bool(item.get("resolved_version_id")) for item in objects),
        [
            {
                "object_id": item.get("object_id"),
                "resolved_version_id": item.get("resolved_version_id"),
                "is_current": item.get("is_current"),
            }
            for item in objects
        ],
    )
    actual_policy_options = {key: policy.get(key) for key in expected_options}
    check(
        "selection_policy_include_options",
        actual_policy_options == expected_options,
        actual_policy_options,
    )
    check(
        "selection_policy_deterministic",
        policy.get("budget_metric") == "serialized_json_characters"
        and policy.get("budget_strategy") == "equal_share_per_object"
        and policy.get("partial_statement_truncation") is False,
        {
            "budget_metric": policy.get("budget_metric"),
            "budget_strategy": policy.get("budget_strategy"),
            "partial_statement_truncation": policy.get(
                "partial_statement_truncation"
            ),
        },
    )
    check(
        "budget_limit",
        budget.get("limit_characters") == max_characters,
        budget,
    )
    used = budget.get("used_characters")
    omitted = budget.get("omitted_items")
    check(
        "budget_used",
        isinstance(used, int) and 0 <= used <= max_characters,
        used,
    )
    check(
        "budget_truncation_metadata",
        isinstance(omitted, int)
        and omitted >= 0
        and budget.get("truncated") == (omitted > 0),
        {
            "omitted_items": omitted,
            "truncated": budget.get("truncated"),
        },
    )
    traceable = all(
        bool(item.get("object_id")) and bool(item.get("resolved_version_id"))
        for item in objects
    )
    check("traceable_versions", traceable, object_ids)

    evidence_ref_count = _count_evidence_refs(objects)
    if include_evidence_refs:
        check(
            "evidence_refs_preserved",
            evidence_ref_count > 0,
            evidence_ref_count,
        )
    else:
        check(
            "evidence_refs_omitted",
            evidence_ref_count == 0,
            evidence_ref_count,
        )
    return checks


def _case_result(
    case_id: str,
    checks: list[dict[str, Any]],
) -> dict[str, Any]:
    failed = [item["name"] for item in checks if not item["pass"]]
    return {
        "case_id": case_id,
        "status": "PASS" if not failed else "FAIL",
        "failed_checks": failed,
        "checks": checks,
    }


def _blocked(reason: str, detail: Any) -> dict[str, Any]:
    return {
        "schema_version": "sgokb.n04-knowledge-access-evaluation/1",
        "task": "N-04R-04",
        "formal_boundary": "external_consumer_boundary",
        "overall_status": "BLOCKED",
        "blocked_reason": reason,
        "blocked_detail": detail,
        "failed_cases": [],
        "failed_global_gates": [],
        "cases": [],
        "global_checks": [],
        "consumer_demonstration_considered": False,
    }


def evaluate(run_root: Path) -> dict[str, Any]:
    missing = [
        relative
        for relative in REQUIRED_INPUTS
        if not (run_root / relative).is_file()
    ]
    if missing:
        return _blocked("required_evidence_missing", missing)

    try:
        case1_request = load_json(
            run_root / "case-1-roleplay" / "request.json"
        )
        case1_context = load_json(
            run_root / "case-1-roleplay" / "context.json"
        )
        similarity_request = load_json(
            run_root / "case-2-comparison" / "similarity-request.json"
        )
        similarity_response = load_json(
            run_root / "case-2-comparison" / "similarity.json"
        )
        case2_request = load_json(
            run_root / "case-2-comparison" / "context-request.json"
        )
        case2_context = load_json(
            run_root / "case-2-comparison" / "context.json"
        )
        case3_request = load_json(
            run_root / "case-3-creative" / "request.json"
        )
        case3_context = load_json(
            run_root / "case-3-creative" / "context.json"
        )
        before = load_json(run_root / "canonical-before.json")
        after = load_json(run_root / "canonical-after.json")
        integrity = load_json(run_root / "integrity.json")
        regression = load_json(run_root / "regression.json")
    except (json.JSONDecodeError, OSError, TypeError) as exc:
        return _blocked("formal_evidence_unreadable", str(exc))

    case1_checks = _check_context(
        request=case1_request,
        response=case1_context,
        expected_ids=["326a97cf-47aa-4760-a7f1-07bfe639fcf0"],
        purpose="roleplay",
        max_characters=12000,
        include_attributes=True,
        include_relations=True,
        include_evidence_refs=False,
    )

    similarity = _data(similarity_response)
    results = similarity.get("results", [])
    candidate_id = results[0].get("object_id") if results else None
    candidate_rank = results[0].get("rank") if results else None
    case2_checks = [
        {
            "name": "public_tool_find_similar_objects",
            "pass": similarity_request.get("tool") == "find_similar_objects",
            "detail": similarity_request.get("tool"),
        },
        {
            "name": "similarity_mcp_contract",
            "pass": (
                similarity_response.get("tool_contract_version")
                == MCP_CONTRACT
            ),
            "detail": similarity_response.get("tool_contract_version"),
        },
        {
            "name": "similarity_source_object",
            "pass": (
                similarity.get("source_object_id")
                == "d5824d33-7008-4121-9cfe-1f95a19667fd"
            ),
            "detail": similarity.get("source_object_id"),
        },
        {
            "name": "similarity_candidate_present",
            "pass": bool(candidate_id),
            "detail": candidate_id,
        },
        {
            "name": "similarity_top_candidate_rank",
            "pass": candidate_rank == 1,
            "detail": candidate_rank,
        },
    ]
    if candidate_id:
        case2_checks.extend(
            _check_context(
                request=case2_request,
                response=case2_context,
                expected_ids=[
                    "d5824d33-7008-4121-9cfe-1f95a19667fd",
                    str(candidate_id),
                ],
                purpose="comparison",
                max_characters=24000,
                include_attributes=True,
                include_relations=False,
                include_evidence_refs=True,
            )
        )

    case3_checks = _check_context(
        request=case3_request,
        response=case3_context,
        expected_ids=[
            "8c83f986-f491-41a8-8645-9f71dd5874b9",
            "fee32007-0f92-449a-ba21-4ec2f78d1cd4",
        ],
        purpose="creative",
        max_characters=24000,
        include_attributes=True,
        include_relations=True,
        include_evidence_refs=False,
    )

    cases = [
        _case_result("n04-roleplay-saber", case1_checks),
        _case_result("n04-similar-work-comparison", case2_checks),
        _case_result("n04-concept-combination-creative", case3_checks),
    ]

    integrity_pass = (
        integrity.get("status") == "PASS"
        or integrity.get("pass") is True
    )
    return_codes = regression.get("return_codes", {})
    regression_pass = bool(return_codes) and all(
        value == 0 for value in return_codes.values()
    )
    global_checks = [
        {
            "name": "canonical_invariance",
            "pass": before == after,
            "detail": (
                "exact JSON equality"
                if before == after
                else "before/after differ"
            ),
        },
        {
            "name": "integrity",
            "pass": integrity_pass,
            "detail": integrity,
        },
        {
            "name": "regression",
            "pass": regression_pass,
            "detail": return_codes,
        },
    ]

    failed_global = [
        item["name"] for item in global_checks if not item["pass"]
    ]
    failed_cases = [
        item["case_id"] for item in cases if item["status"] != "PASS"
    ]
    overall = "PASS" if not failed_global and not failed_cases else "FAIL"
    return {
        "schema_version": "sgokb.n04-knowledge-access-evaluation/1",
        "task": "N-04R-04",
        "formal_boundary": "external_consumer_boundary",
        "overall_status": overall,
        "failed_cases": failed_cases,
        "failed_global_gates": failed_global,
        "cases": cases,
        "global_checks": global_checks,
        "consumer_demonstration_considered": False,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = evaluate(args.run_root.resolve())
    rendered = (
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n"
    )
    output = args.output or args.run_root / "overall-evaluation.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    if report["overall_status"] == "PASS":
        return 0
    if report["overall_status"] == "BLOCKED":
        return 2
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
