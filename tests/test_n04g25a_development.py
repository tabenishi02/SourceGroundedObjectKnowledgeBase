from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def module():
    spec = importlib.util.spec_from_file_location(
        "g25a_validator", ROOT / "benchmark/tools/n04g25a_validate_development.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def fixture():
    manifest = json.loads((ROOT / "benchmark/n04g25a-development-manifest-v1.json").read_text())
    split = json.loads((ROOT / "benchmark/n04g25a-split-manifest-v1.json").read_text())
    rows = [
        json.loads(s)
        for s in (ROOT / "benchmark/n04g25a-atomicity-development-v1.jsonl")
        .read_text()
        .splitlines()
    ]
    return rows, {f["family_id"]: f for f in manifest["families"]}, split


def test_frozen_corpus_counts_and_group_holdouts():
    report = module().validate(ROOT)
    assert report["status"] == "PASS"
    assert report["tasks"]["atomicity"]["total"] == 450
    assert report["tasks"]["content_type"]["total"] == 550
    assert report["cross_task_lineage_leakage"] == 0
    assert report["confirmation_data_loaded"] is False


@pytest.mark.parametrize(
    "defect",
    ["missing", "duplicate", "label", "ambiguous_training", "family_leak", "normalized_duplicate"],
)
def test_validator_rejects_invalid_or_leaking_corpus(defect):
    rows, families, split = fixture()
    rows, families, split = copy.deepcopy((rows, families, split))
    if defect == "missing":
        del rows[0]["rationale"]
    elif defect == "duplicate":
        rows[1]["case_id"] = rows[0]["case_id"]
    elif defect == "label":
        rows[0]["label"] = "ROLE_VALID"
    elif defect == "ambiguous_training":
        next(r for r in rows if r["label"] == "AMBIGUOUS")["training_target"] = True
    elif defect == "family_leak":
        target = next(r for r in rows if r["split"] == "selection")
        target["lineage_id"] = rows[0]["lineage_id"]
    else:
        target = next(r for r in rows if r["split"] == "selection")
        target["text"] = rows[0]["text"].upper() + "!!!"
    with pytest.raises(ValueError):
        module().check("atomicity", rows, families, split)


def test_role_compatibility_is_evaluation_metadata_not_input():
    mod = module()
    manifest = json.loads((ROOT / "benchmark/n04g25a-development-manifest-v1.json").read_text())
    split = json.loads((ROOT / "benchmark/n04g25a-split-manifest-v1.json").read_text())
    rows = [
        json.loads(s)
        for s in (ROOT / "benchmark/n04g25a-content-type-development-v1.jsonl")
        .read_text()
        .splitlines()
    ]
    rows[0]["compatible_expected_roles"] = ["creative_addition"]
    with pytest.raises(ValueError, match="Compatibility"):
        mod.check("content_type", rows, {f["family_id"]: f for f in manifest["families"]}, split)
