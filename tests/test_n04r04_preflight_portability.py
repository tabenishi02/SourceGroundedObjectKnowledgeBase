"""Regression coverage for R-03 preflight implementation portability repairs."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "r04_preflight_repairs", ROOT / "benchmark/tools/n04r03_harness_preflight.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_frozen_worktree_bytes_match_the_frozen_git_blobs():
    assert MODULE.git_blob_sha(ROOT / "benchmark/n04-knowledge-access-cases-v1.json") == (
        "ab3374508467575955f0f9da911f551178a93b6e"
    )
    assert MODULE.git_blob_sha(ROOT / "benchmark/tools/n04r04_evaluate_evidence.py") == (
        "060037e5316dd819472018f54c1d5600786e3e74"
    )


def test_evaluator_dependency_check_accepts_only_static_standard_library_dependencies():
    assert (
        MODULE.evaluator_dependency_violations(
            "from __future__ import annotations\nimport argparse, json\nfrom pathlib import Path\n"
        )
        == []
    )


@pytest.mark.parametrize(
    "source",
    [
        "import sgokb.grounding",
        "from transformers import pipeline",
        "from minicheck import MiniCheck",
        "import requests",
        "from .consumer import generate",
        "__import__('consumer')",
        "import importlib\nimportlib.import_module('consumer')",
        "eval('consumer()')",
        "exec('import consumer')",
        "invalid syntax !",
    ],
)
def test_evaluator_dependency_check_rejects_external_and_dynamic_execution(source):
    assert MODULE.evaluator_dependency_violations(source)
