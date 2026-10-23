import json
from pathlib import Path

from scripts.run_n05d04r2_search_quality_acceptance import evaluate_baseline_gates

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "benchmark/n05d04r2-search-quality-acceptance-v1.json"
PHASE_I_GOLD = ROOT / "benchmark/search-quality-gold-v1.json"
R2_SIMILARITY_GOLD = ROOT / "benchmark/n05d04r2-object-similarity-gold-v1.json"
R2_SIMILARITY_TEST_MAP = (
    ROOT / "benchmark/n05d04r2-object-similarity-gold-test-map-v1.json"
)
R2_SIMILARITY_TESTS = ROOT / "tests/test_object_similarity_r2.py"


def _load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_r2_08_acceptance_contract_is_frozen_and_keeps_harrier_baseline():
    contract = _load(CONTRACT)
    assert (
        contract["schema_version"]
        == "sgokb.n05d04r2-search-quality-acceptance/1.0"
    )
    assert contract["status"] == "frozen"
    assert contract["fixed_runtime"] == {
        "embedding_model": "microsoft/harrier-oss-v1-0.6b",
        "embedding_revision": "f9b9dc8d367d443f2479d27aa5d8d2850c0774ee",
        "embedding_dimension": 1024,
        "representation_family": ["object_overview", "facet", "statement"],
        "forbidden_active_representation": "object_overall",
    }
    assert (
        contract["n06_interaction"]["status"]
        == "N-06 Ready; R2 interaction required"
    )


def test_r2_08_reuses_frozen_phase_i_gold_without_rewriting_historical_expectations():
    contract = _load(CONTRACT)
    gold = _load(PHASE_I_GOLD)
    assert gold["schema_version"] == "sgokb.search-gold/1.0"
    assert gold["status"] == "frozen"
    assert contract["inputs"]["phase_i_gold"] == "benchmark/search-quality-gold-v1.json"
    assert len(gold["search_queries"]) == 24
    assert len([case for case in gold["search_queries"] if case.get("statement_refs")]) == 22
    assert len(gold["similarity_cases"]) == 4
    assert len(gold["evidence_cases"]) == 3
    assert len(gold["contract_cases"]) == 5


def test_r2_08_connects_all_six_hierarchical_similarity_gold_cases():
    contract = _load(CONTRACT)
    similarity = _load(R2_SIMILARITY_GOLD)
    ids = [case["id"] for case in similarity["cases"]]
    names = [case["name"] for case in similarity["cases"]]
    assert ids == contract["required_r2_similarity_case_ids"]
    assert names == contract["required_r2_similarity_case_names"]
    assert ids == [
        "R2SIM-G01",
        "R2SIM-G02",
        "R2SIM-G03",
        "R2SIM-G04",
        "R2SIM-G05",
        "R2SIM-G06",
    ]


def test_r2_similarity_gold_has_explicit_regression_test_traceability():
    contract = _load(CONTRACT)
    mapping = _load(R2_SIMILARITY_TEST_MAP)
    source = R2_SIMILARITY_TESTS.read_text(encoding="utf-8")
    assert mapping["status"] == "frozen"
    assert set(mapping["cases"]) == set(contract["required_r2_similarity_case_ids"])
    for test_names in mapping["cases"].values():
        assert test_names
        for test_name in test_names:
            assert f"def {test_name}(" in source


def _passing_result():
    return {
        "search": {
            "exact_lookup_accuracy": 1.0,
            "modes": {
                "semantic": {
                    "quality": {
                        "mrr": 1.0,
                        "recall@1": 0.854,
                        "recall@10": 1.0,
                        "ndcg@10": 0.993,
                    }
                },
                "hybrid": {
                    "quality": {
                        "mrr": 1.0,
                        "recall@1": 0.854,
                        "recall@10": 1.0,
                        "ndcg@10": 1.0,
                    }
                },
            },
            "statement_semantic": {
                "quality": {
                    "mrr": 1.0,
                    "recall@1": 0.864,
                    "recall@10": 1.0,
                    "ndcg@10": 0.993,
                }
            },
        },
        "contracts": {"passed": 5, "total": 5},
        "similarity": {
            "overall_quality": {
                "mrr": 0.833,
                "recall@1": 0.667,
                "recall@10": 1.0,
                "ndcg@10": 0.877,
            },
            "facet_quality": {
                "mrr": 1.0,
                "recall@10": 1.0,
                "ndcg@10": 1.0,
            },
        },
        "evidence_search": {
            "lexical_association": {
                "quality": {"mrr": 1.0, "recall@10": 1.0, "ndcg@10": 1.0}
            },
            "semantic": {
                "quality": {"mrr": 1.0, "recall@10": 1.0, "ndcg@10": 1.0}
            },
        },
    }


def test_r2_08_baseline_evaluator_separates_hard_failures_from_review_deltas():
    contract = _load(CONTRACT)
    result = _passing_result()
    evaluation = evaluate_baseline_gates(result, contract)
    assert evaluation["strict_passed"] is True
    assert evaluation["requires_explanation"] is False

    result["search"]["modes"]["hybrid"]["quality"]["mrr"] = 0.9
    evaluation = evaluate_baseline_gates(result, contract)
    assert evaluation["strict_passed"] is False

    result = _passing_result()
    result["similarity"]["overall_quality"]["mrr"] = 0.8
    evaluation = evaluate_baseline_gates(result, contract)
    assert evaluation["strict_passed"] is True
    assert evaluation["requires_explanation"] is True


def test_r2_08_required_contract_suite_covers_search_similarity_generation_and_evidence():
    contract = _load(CONTRACT)
    files = set(contract["required_r2_contract_tests"])
    assert {
        "tests/test_hybrid_search_r2.py",
        "tests/test_object_similarity_r2.py",
        "tests/test_generation_lifecycle_r2.py",
        "tests/test_generation_lifecycle_qdrant_r2.py",
        "tests/test_object_overview_r2.py",
        "tests/test_search_quality_gold.py",
        "tests/test_j02_evidence_search.py",
    } <= files
