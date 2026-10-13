import json
from pathlib import Path

from sgokb.domain import (
    EmbeddingSpaceSpec,
    VectorIndexPoint,
    VectorMatch,
    VectorRange,
    VectorSearchFilter,
)
from sgokb.retrieval import ExactVectorIndexAdapter, ann_recall_at_k, ranked_retrieval_metrics

ROOT = Path(__file__).resolve().parents[1]
GOLD = ROOT / "benchmark/search-quality-gold-v1.json"


def _space():
    return EmbeddingSpaceSpec(
        provider_key="gold-test",
        provider_version="1",
        model="gold-test-model",
        model_revision="1",
        dimension=3,
        native_dimension=3,
        preprocessing_key="sgokb-search-representation",
        preprocessing_version="2",
        normalize_embeddings=True,
        max_sequence_length=32,
        overflow_policy="reject",
        output_dtype="float32",
        provider_configuration="{}",
    )


def test_i07_gold_fixture_is_frozen_and_covers_required_classes_and_query_types():
    gold = json.loads(GOLD.read_text(encoding="utf-8"))
    assert gold["schema_version"] == "sgokb.search-gold/1.0"
    assert gold["status"] == "frozen"
    object_ids = {item["id"] for item in gold["objects"]}
    classes = {item["primary_class"] for item in gold["objects"]}
    categories = {item["category"] for item in gold["search_queries"]}
    assert set(gold["required_class_coverage"]) <= classes
    assert set(gold["required_query_categories"]) <= categories
    assert {
        "character",
        "work",
        "concept",
        "person",
        "organization",
        "series",
        "place",
        "event",
    } <= classes
    assert {"software", "product", "species", "phenomenon", "language", "ability"} <= classes
    assert {
        "cross_lingual",
        "conditional_exception",
        "fine_statement",
        "facet_specific",
    } <= categories
    for case in gold["search_queries"]:
        assert set(case["relevance"]) <= object_ids
    for case in gold["similarity_cases"]:
        assert case["source_object_id"] in object_ids
        assert set(case["relevance"]) <= object_ids
        assert case["judgement_channel"] == "human_authored_synthetic_gold"


def test_ranked_retrieval_metrics_support_graded_relevance():
    metrics = ranked_retrieval_metrics(["b", "a", "c"], {"a": 3, "b": 1})
    assert metrics["mrr"] == 1.0
    assert metrics["recall@1"] == 0.5
    assert metrics["recall@5"] == 1.0
    assert 0.0 < metrics["ndcg@10"] < 1.0
    assert ann_recall_at_k(["a", "b", "x"], ["a", "b", "c"], 3) == 2 / 3


def test_exact_vector_reference_applies_hard_filters_before_ranking():
    space = _space()
    index = ExactVectorIndexAdapter()
    index.rebuild(
        space,
        [
            VectorIndexPoint(
                "a", (1.0, 0.0, 0.0), {"kind": "statement", "class": "character", "year": 2026}
            ),
            VectorIndexPoint(
                "b", (0.99, 0.01, 0.0), {"kind": "statement", "class": "work", "year": 2026}
            ),
            VectorIndexPoint(
                "c", (0.9, 0.1, 0.0), {"kind": "statement", "class": "character", "year": 2025}
            ),
        ],
    )
    hits = index.search(
        space,
        (1.0, 0.0, 0.0),
        limit=10,
        filters=VectorSearchFilter(
            matches=(VectorMatch("class", ("character",)),),
            excludes=(VectorMatch("kind", ("facet",)),),
            ranges=(VectorRange("year", gte=2026),),
        ),
    )
    assert [hit.point_id for hit in hits] == ["a"]
    assert index.metadata(space).approximate is False
