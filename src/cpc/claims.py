"""Rebuildable, conservative knowledge claims; source fragments stay immutable."""

import re

from .domain import digest, json_text


def derive_claims(entity_id, rows):
    groups = {}
    for row in rows:
        metadata = row["metadata"]
        attributes = {
            "entity": entity_id,
            "subject": metadata.get("subject"),
            "facet": row["facet"],
            **{
                k: metadata.get(k)
                for k in (
                    "epistemic_type",
                    "evidence_strength",
                    "asserted_by",
                    "temporal_context",
                    "conflict_group",
                )
            },
        }
        # Only whitespace and sentence-ending punctuation; preserve numbers and negations.
        normalized = re.sub(r"\s+", "", row["content"]).rstrip("。．.!！")
        key = digest(json_text([attributes, normalized]))
        claim = groups.setdefault(
            key,
            {
                "id": key,
                **attributes,
                "text": row["content"],
                "fragment_ids": [],
                "evidence_ids": [],
            },
        )
        claim["fragment_ids"].append(row["id"])
        claim["evidence_ids"].extend(metadata.get("evidence_ids", []))
    for claim in groups.values():
        claim["fragment_ids"] = sorted(set(claim["fragment_ids"]))
        claim["evidence_ids"] = sorted(set(claim["evidence_ids"]))
    return sorted(groups.values(), key=lambda c: c["id"])


def build_claims(repo, entity_id):
    rows = repo.related_fragments(entity_id)
    if not rows:
        raise ValueError("No active fragments")
    claims = derive_claims(entity_id, rows)
    configuration = {"algorithm": "exact-claims-v1"}
    input_hash = digest(json_text(sorted([r["id"], r["content"], r["metadata"]] for r in rows)))
    generation = digest(json_text([entity_id, input_hash, configuration]))
    repo.save_claims(generation, entity_id, configuration, input_hash, claims)
    return {"generation_id": generation, "claims": claims, "fragments": len(rows)}
