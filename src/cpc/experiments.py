"""Bounded, opt-in derived experiments; candidates never promote semantic merges."""

from collections import defaultdict

from jsonschema import Draft202012Validator

from .benchmark import require_local
from .claims import build_claims
from .domain import EmbeddingSpace, json_text, validate_vectors
from .search import SQLiteCosineIndex
from .views import build_view


def save_experiment(repo, entity_id, result):
    ai_id = repo.begin_ai("derived_experiment", "cpc-derived-renderer", "1", "", "1", result)
    repo.finish_ai(ai_id, json_text(result))
    result["document_id"] = repo.save_structured(
        entity_id,
        ai_id,
        result,
        [],
        json_text(result),
        {},
        {"algorithm": "derived-experiment-v1", "semantic_quality": "human_gold_missing"},
        algorithm="derived-experiment-v1",
    )
    return result


def hierarchy(claims):
    facets = defaultdict(list)
    for claim in claims:
        facets[(claim["facet"], claim["epistemic_type"])].append(claim["id"])
    return {
        "method": "extractive-claim-hierarchy-v1",
        "overview": {"claim_count": len(claims), "facet_count": len(facets)},
        "facets": [
            {"facet": facet, "epistemic_type": kind, "claim_ids": ids}
            for (facet, kind), ids in sorted(facets.items(), key=lambda x: str(x[0]))
        ],
    }


def compatible_claims(left, right):
    return all(
        left.get(k) == right.get(k)
        for k in (
            "entity",
            "subject",
            "facet",
            "epistemic_type",
            "evidence_strength",
            "asserted_by",
            "temporal_context",
            "conflict_group",
        )
    )


def claim_experiment(app, entity_id, max_claims=200, max_pairs=20, judge=False):
    if not 1 <= max_claims <= 200 or not 1 <= max_pairs <= 50:
        raise ValueError("Experimental candidate limits exceeded")
    require_local(app.embedder)
    if app.embedder is None:
        raise ValueError("Embedding provider required")
    if judge:
        require_local(app.llm)
    source = build_claims(app.repository, entity_id)
    selected = source["claims"][:max_claims]
    vectors = app.embedder.embed([c["text"] for c in selected])
    dimension = validate_vectors(vectors, len(selected))
    space = EmbeddingSpace(
        app.embedder.model, app.embedder.revision, dimension, app.embedder.configuration
    )
    candidates, seen = [], set()
    rows = [
        dict(claim, target_id=claim["id"], vector=vector)
        for claim, vector in zip(selected, vectors)
    ]
    index = SQLiteCosineIndex()
    for left, vector in zip(selected, vectors):
        for right in index.search(vector, rows, min(6, len(rows))):
            pair = tuple(sorted((left["id"], right["id"])))
            if pair[0] == pair[1] or pair in seen:
                continue
            seen.add(pair)
            candidates.append((right["semantic_score"], left, right))
    candidates.sort(key=lambda x: (-x[0], x[1]["id"], x[2]["id"]))
    relations = []
    schema = {
        "type": "object",
        "properties": {
            "relation": {
                "type": "string",
                "enum": ["same_claim", "related", "different_time", "conflict", "unrelated"],
            }
        },
        "required": ["relation"],
        "additionalProperties": False,
    }
    for score, left, right in candidates[:max_pairs]:
        record = {
            "left": left["id"],
            "right": right["id"],
            "similarity": score,
            "relation": "candidate",
            "status": "unreviewed",
        }
        if judge:
            ai_id, _, result = app.call_llm(
                "claim_relation",
                "claim_relation",
                {"left": left, "right": right},
                response_schema=schema,
            )
            if not Draft202012Validator(schema).is_valid(result):
                app.repository.finish_ai(ai_id, error="InvalidClaimRelation")
                raise ValueError("Invalid claim relation")
            relation = result["relation"]
            if relation == "same_claim" and not compatible_claims(left, right):
                relation = "related"
                record["guard"] = "incompatible_claim_attributes"
            if relation == "conflict" and left["temporal_context"] != right["temporal_context"]:
                relation = "different_time"
                record["guard"] = "different_temporal_context"
            record.update(relation=relation, status="proposed", ai_run=ai_id)
        relations.append(record)
    return save_experiment(
        app.repository,
        entity_id,
        {
            "generation_id": source["generation_id"],
            "embedding_space": space.key,
            "hierarchy": hierarchy(source["claims"]),
            "relations": relations,
            "selected_claim_ids": [c["id"] for c in selected],
            "excluded_claim_count": max(0, len(source["claims"]) - max_claims),
            "semantic_quality": "human_gold_missing",
            "promoted_semantic_merges": 0,
        },
    )


def compression_experiment(repo, entity_id, budget, counter=None, query=None):
    """RECOMP-style extractive selection candidate; no token-deletion model or new facts."""
    variants = []
    for ratio in (1, 2, 3, 5):
        try:
            view = build_view(repo, entity_id, max(1, budget // ratio), counter, query)
            variants.append(
                {
                    "ratio": ratio,
                    "status": "completed",
                    "document_id": view["document_id"],
                    "selected_claim_ids": view["structured"]["selected_claim_ids"],
                    "output_tokens": view["output_tokens"],
                    "counter": view["configuration"]["counter"],
                }
            )
        except ValueError as error:
            variants.append({"ratio": ratio, "status": "failed", "error": str(error)})
    return save_experiment(
        repo,
        entity_id,
        {
            "method": "extractive-context-selection-v1",
            "variants": variants,
            "semantic_quality": "human_gold_missing",
        },
    )
