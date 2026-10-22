import importlib.util
from pathlib import Path
from types import SimpleNamespace

SPEC = importlib.util.spec_from_file_location(
    "n05_resource_preflight",
    Path(__file__).resolve().parents[1] / "benchmark/tools/n05_resource_preflight.py",
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_disk_gate_is_32_gib():
    assert MODULE.MIN_FREE_DISK_GIB == 32
    assert MODULE.MIN_FREE_DISK_BYTES == 32 * 1024**3


def test_volume_blocks_below_threshold(monkeypatch, tmp_path):
    monkeypatch.setattr(
        MODULE.shutil,
        "disk_usage",
        lambda _: SimpleNamespace(total=100 * 1024**3, used=69 * 1024**3, free=31 * 1024**3),
    )
    result = MODULE._volume(tmp_path)
    assert result["pass"] is False
    assert result["required_free_gib"] == 32


def test_volume_accepts_threshold_exactly(monkeypatch, tmp_path):
    monkeypatch.setattr(
        MODULE.shutil,
        "disk_usage",
        lambda _: SimpleNamespace(total=100 * 1024**3, used=68 * 1024**3, free=32 * 1024**3),
    )
    assert MODULE._volume(tmp_path)["pass"] is True


def test_nominal_default_wal_capacity_for_formal_samples():
    assert MODULE.PLANNED_FORMAL_SAMPLES == 46
    assert MODULE.QDRANT_DEFAULT_WAL_CAPACITY_MB == 32
    assert MODULE.PLANNED_FORMAL_SAMPLES * MODULE.QDRANT_DEFAULT_WAL_CAPACITY_MB == 1472
