"""Safety and partition contracts for development-only classifier policy fitting."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "g25a_metrics", ROOT / "benchmark/tools/n04g25a_development_metrics.py"
)
METRICS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(METRICS)
MANIFEST = json.loads((ROOT / "benchmark/n04g25a-candidate-manifest-v1.json").read_text())


def row(label, **extra):
    return {
        "text": "An independent neutral proposition.",
        "label": label,
        "family_id": "fixture",
        "split": "validation",
        "required": True,
        "critical_for_safety": True,
        **extra,
    }


def test_only_claim_text_is_projected_into_model_input():
    first = row("ATOMIC", expected_role="source_fact", support_verdict="SUPPORTED")
    second = dict(first, expected_role="creative_addition", support_verdict="UNSUPPORTED")
    assert METRICS.model_inputs([first]) == METRICS.model_inputs([second]) == [first["text"]]


def test_atomicity_safety_and_valid_rejection_have_distinct_fail_closed_semantics():
    rows = [row("NON_ATOMIC"), row("ATOMIC")]
    result = METRICS.metrics(
        "atomicity", rows, ["ATOMIC", "AMBIGUOUS"], MANIFEST["tasks"]["atomicity"]["output_classes"]
    )
    assert result["critical_false_pass"] == 1
    assert result["required_valid_false_reject"] == 1
    result = METRICS.metrics(
        "atomicity", rows, ["AMBIGUOUS", "ATOMIC"], MANIFEST["tasks"]["atomicity"]["output_classes"]
    )
    assert result["critical_false_pass"] == result["required_valid_false_reject"] == 0


@pytest.mark.parametrize(
    "prediction,critical,rejected",
    [
        ("CREATIVE_CONTENT", 1, 1),
        ("MIXED_CONTENT", 0, 1),
        ("AMBIGUOUS", 0, 1),
        ("SOURCE_FACT_CONTENT", 0, 0),
    ],
)
def test_content_role_compatibility_is_application_owned(prediction, critical, rejected):
    rows = [
        row(
            "SOURCE_FACT_CONTENT",
            compatible_expected_roles=["source_fact"],
            critical_incompatible_expected_roles=[
                "interpretation",
                "creative_addition",
                "context_limit",
            ],
        )
    ]
    result = METRICS.metrics(
        "content_type", rows, [prediction], MANIFEST["tasks"]["content_type"]["output_classes"]
    )
    assert result["critical_false_pass"] == critical
    assert result["required_valid_false_reject"] == rejected


def test_mixed_content_cannot_become_compatible_with_any_role():
    mixed = row(
        "MIXED_CONTENT",
        compatible_expected_roles=[],
        critical_incompatible_expected_roles=list(METRICS.ROLES.values()),
    )
    result = METRICS.metrics(
        "content_type",
        [mixed],
        ["SOURCE_FACT_CONTENT"],
        MANIFEST["tasks"]["content_type"]["output_classes"],
    )
    assert result["critical_false_pass"] == 1
    assert result["required_valid_false_reject"] == 0


def test_policy_fitting_refuses_selection_and_training_rows():
    for partition in ("train", "selection"):
        with pytest.raises(ValueError, match="validation only"):
            METRICS.fit_policy(
                "atomicity",
                [row("ATOMIC", split=partition)],
                [[0.9, 0.1]],
                ["ATOMIC", "NON_ATOMIC"],
                MANIFEST,
            )


def test_validation_threshold_priority_preserves_critical_gate():
    rows = [row("NON_ATOMIC"), row("ATOMIC")]
    result = METRICS.fit_policy(
        "atomicity", rows, [[0.6, 0.4], [0.9, 0.1]], ["ATOMIC", "NON_ATOMIC"], MANIFEST
    )
    assert result["validation_metrics"]["critical_false_pass"] == 0
    assert result["validation_metrics"]["required_valid_false_reject"] == 0
    assert result["fit_partition"] == "validation"
    assert METRICS.predict_labels(
        [[0.6, 0.4], [0.9, 0.1]], ["ATOMIC", "NON_ATOMIC"], result["policy"]
    ) == ["AMBIGUOUS", "ATOMIC"]


def test_repeatability_requires_three_complete_predictions_and_exact_required_labels():
    rows = [row("ATOMIC"), row("AMBIGUOUS", required=False, critical_for_safety=False)]
    assert (
        METRICS.repeatability(
            rows, [["ATOMIC", "ATOMIC"], ["ATOMIC", "AMBIGUOUS"], ["ATOMIC", "NON_ATOMIC"]]
        )
        == 0
    )
    assert (
        METRICS.repeatability(
            rows, [["ATOMIC", "ATOMIC"], ["AMBIGUOUS", "ATOMIC"], ["ATOMIC", "ATOMIC"]]
        )
        == 1
    )
    with pytest.raises(ValueError, match="Three complete"):
        METRICS.repeatability(rows, [["ATOMIC"]] * 3)


@pytest.mark.parametrize("probabilities", [[[float("nan"), 0.1]], [[0.8, 0.8]], [[1.0]]])
def test_malformed_probabilities_are_not_scored_as_a_valid_candidate(probabilities):
    with pytest.raises(ValueError):
        METRICS.predict_labels(
            probabilities, ["ATOMIC", "NON_ATOMIC"], {"min_confidence": 0, "min_margin": 0}
        )
