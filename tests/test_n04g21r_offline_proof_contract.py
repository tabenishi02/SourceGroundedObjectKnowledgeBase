from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "benchmark" / "tools" / "n04g21r_minicheck_offline_proof.py"
PROFILE = ROOT / "benchmark" / "n04-v3-source-fact-verifier-profile-v1.json"


def load_runner():
    spec = importlib.util.spec_from_file_location("n04g21r_offline", RUNNER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_g21r_runner_matches_selected_profile() -> None:
    runner = load_runner()
    profile = json.loads(PROFILE.read_text(encoding="utf-8"))["specialized_verifier"]
    assert runner.EXPECTED_SOURCE_REVISION == profile["source_repository_revision"]
    assert runner.EXPECTED_MODEL_REVISION == profile["model_repository_revision"]
    assert runner.MODEL_REPOSITORY == profile["model_repository"]
    assert runner.THRESHOLD == profile["supported_threshold"] == 0.50


def test_g21r_runner_forces_offline_environment() -> None:
    runner = load_runner()
    source = RUNNER.read_text(encoding="utf-8")
    for variable in (
        "HF_HUB_OFFLINE",
        "TRANSFORMERS_OFFLINE",
        "HF_DATASETS_OFFLINE",
    ):
        assert f'"{variable}": "1"' in source
    assert "install_socket_block" in source
    assert "socket.socket.connect = blocked_connect" in source
    assert "socket.create_connection = blocked_create_connection" in source


def test_g21r_threshold_and_revisions_are_not_cli_overrides() -> None:
    source = RUNNER.read_text(encoding="utf-8")
    assert 'parser.add_argument("--threshold"' not in source
    assert 'parser.add_argument("--expected-source-revision"' not in source
    assert 'parser.add_argument("--expected-model-revision"' not in source
