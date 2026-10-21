from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVALUATOR = ROOT / "benchmark" / "tools" / "n04r04_evaluate_evidence.py"


def _load_evaluator():
    spec = importlib.util.spec_from_file_location("n04r04_evaluator", EVALUATOR)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")


def _context(ids: list[str], purpose: str, limit: int) -> dict:
    return {
        "tool_contract_version": "sgokb.mcp-read-tools.v1",
        "data": {
            "context_contract_version": "sgokb.context-builder.v1",
            "purpose": purpose,
            "selection_policy": {"partial_statement_truncation": False},
            "objects": [
                {
                    "object_id": object_id,
                    "requested_version_id": None,
                    "resolved_version_id": f"version:{index}",
                    "is_current": True,
                    "knowledge": {},
                }
                for index, object_id in enumerate(ids)
            ],
            "budget": {
                "limit_characters": limit,
                "used_characters": min(100, limit),
                "omitted_items": 0,
                "truncated": False,
            },
            "warnings": [],
        },
    }


def test_n04r04_evaluator_passes_valid_boundary_evidence(tmp_path: Path) -> None:
    module = _load_evaluator()
    saber = "326a97cf-47aa-4760-a7f1-07bfe639fcf0"
    fate = "d5824d33-7008-4121-9cfe-1f95a19667fd"
    bleach = "57db855c-574a-4b38-b474-421c165894f1"
    tsundere = "8c83f986-f491-41a8-8645-9f71dd5874b9"
    journey = "fee32007-0f92-449a-ba21-4ec2f78d1cd4"

    _write(
        tmp_path / "case-1-roleplay" / "request.json",
        {
            "tool": "build_context",
            "arguments": {
                "object_ids": [saber],
                "purpose": "roleplay",
                "max_characters": 12000,
            },
        },
    )
    _write(tmp_path / "case-1-roleplay" / "context.json", _context([saber], "roleplay", 12000))

    _write(
        tmp_path / "case-2-comparison" / "similarity-request.json",
        {"tool": "find_similar_objects", "arguments": {"object_id": fate, "limit": 5}},
    )
    _write(
        tmp_path / "case-2-comparison" / "similarity.json",
        {
            "tool_contract_version": "sgokb.mcp-read-tools.v1",
            "data": {
                "source_object_id": fate,
                "source_version_id": "version:fate",
                "results": [{"object_id": bleach, "rank": 1}],
            },
        },
    )
    _write(
        tmp_path / "case-2-comparison" / "context-request.json",
        {
            "tool": "build_context",
            "arguments": {
                "object_ids": [fate, bleach],
                "purpose": "comparison",
                "max_characters": 24000,
            },
        },
    )
    _write(
        tmp_path / "case-2-comparison" / "context.json",
        _context([fate, bleach], "comparison", 24000),
    )

    _write(
        tmp_path / "case-3-creative" / "request.json",
        {
            "tool": "build_context",
            "arguments": {
                "object_ids": [tsundere, journey],
                "purpose": "creative",
                "max_characters": 24000,
            },
        },
    )
    _write(
        tmp_path / "case-3-creative" / "context.json",
        _context([tsundere, journey], "creative", 24000),
    )

    snapshot = {"objects": [saber, fate, bleach, tsundere, journey], "version": 1}
    _write(tmp_path / "canonical-before.json", snapshot)
    _write(tmp_path / "canonical-after.json", snapshot)
    _write(tmp_path / "integrity.json", {"status": "PASS"})
    _write(
        tmp_path / "regression.json",
        {
            "return_codes": {
                "focused_pytest": 0,
                "full_pytest": 0,
                "ruff": 0,
                "diff_check": 0,
            }
        },
    )

    report = module.evaluate(tmp_path)
    assert report["overall_status"] == "PASS"
    assert report["consumer_demonstration_considered"] is False
    assert all(item["status"] == "PASS" for item in report["cases"])


def test_n04r04_evaluator_fails_only_on_sgokb_boundary_evidence(tmp_path: Path) -> None:
    module = _load_evaluator()
    assert "reference-consumer" not in EVALUATOR.read_text(encoding="utf-8")
    assert "sgokb.grounding" not in EVALUATOR.read_text(encoding="utf-8")
    assert module.MCP_CONTRACT == "sgokb.mcp-read-tools.v1"
    assert module.CONTEXT_CONTRACT == "sgokb.context-builder.v1"
