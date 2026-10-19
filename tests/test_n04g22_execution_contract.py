from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PREFLIGHT = ROOT / "benchmark" / "tools" / "n04g22_freeze_preflight.py"


def load_preflight_module():
    spec = importlib.util.spec_from_file_location("n04g22_preflight", PREFLIGHT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_g22_frozen_harness_preflight_passes() -> None:
    module = load_preflight_module()
    report = module.evaluate(ROOT)
    assert report["preflight"] == "PASS", report["failed_checks"]


def test_g22_case_order_is_frozen() -> None:
    module = load_preflight_module()
    assert module.FROZEN_CASE_IDS == [
        "n04-roleplay-saber",
        "n04-similar-work-comparison",
        "n04-concept-combination-creative",
    ]


def test_g22_preflight_has_no_runtime_override_cli() -> None:
    source = PREFLIGHT.read_text(encoding="utf-8")
    for forbidden in (
        "--threshold",
        "--model-revision",
        "--source-revision",
        "--case-id",
    ):
        assert forbidden not in source
