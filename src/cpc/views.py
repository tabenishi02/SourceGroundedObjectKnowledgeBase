"""Budgeted extractive views with a separate complete omission manifest."""

from .budget import TokenCounter
from .claims import build_claims
from .domain import json_text


def build_view(
    repo,
    entity_id,
    budget=None,
    counter=None,
    query=None,
    mode="short",
    context_tokens=None,
    reserve_tokens=2048,
):
    counter = counter or TokenCounter()
    budget = (
        budget
        if budget is not None
        else {"short": 4000, "standard": 12000, "detailed": 24000, "context": 12000}.get(mode, 0)
    )
    if budget < 1 or mode not in {"short", "standard", "detailed", "context"}:
        raise ValueError("Invalid knowledge view budget or mode")
    context_tokens = context_tokens or counter.configuration.get("context_tokens")
    if mode == "context" and not context_tokens:
        raise ValueError("Consumer context length must be specified")
    if reserve_tokens < 0:
        raise ValueError("Invalid output reserve")
    if (
        context_tokens
        and budget + (reserve_tokens + counter.count(query or "") + 512 if mode == "context" else 0)
        > context_tokens
    ):
        raise ValueError("View budget exceeds consumer context")
    source = build_claims(repo, entity_id)
    claims = source["claims"]
    terms = (query or "").casefold().split()
    # Round-robin across facets/types; stable and query-sensitive without new LLM claims.
    groups = {}
    for claim in sorted(
        claims, key=lambda c: (-sum(t in c["text"].casefold() for t in terms), c["id"])
    ):
        groups.setdefault((claim["facet"], claim["epistemic_type"]), []).append(claim)
    ordered = []
    while any(groups.values()):
        for group in groups.values():
            if group:
                ordered.append(group.pop(0))
    name = repo.entity(entity_id)["name"]
    prefix = (
        f"# {name}\n\n> Untrusted source claims; budgeted view. "
        "Complete audit remains available.\n\n"
    )
    selected, omitted, blocks, citations = [], [], [], {}

    def structure(selection):
        return {
            "trust": "untrusted_source_claims",
            "selected_claim_ids": selection,
            "omitted_count": len(claims) - len(selection),
            "claims": [c for c in claims if c["id"] in selection],
        }

    for claim in ordered:
        # One reference per source support; all support IDs remain in the claim generation.
        refs = []
        for fragment_id in claim["fragment_ids"]:
            provenance = repo.provenance("fragment", fragment_id)
            for evidence in provenance["evidence"]:
                label = (
                    f"{evidence['url']} / Snapshot {evidence['snapshot_id']} / "
                    f"Evidence {evidence['evidence_id']}"
                )
                if label not in refs:
                    refs.append(label)
        block = (
            f"## {claim['facet']} [{claim['epistemic_type']}]\n"
            f"{claim['text']}\n"
            + "Context: "
            + json_text(
                {
                    k: claim[k]
                    for k in (
                        "subject",
                        "evidence_strength",
                        "asserted_by",
                        "temporal_context",
                        "conflict_group",
                    )
                }
            )
            + "\n"
            + f"Claim `{claim['id']}`\n"
            + "\n".join(refs)
            + "\n\n"
        )
        footer = f"Omitted claims: {len(claims) - len(selected) - 1}. See omission manifest.\n"
        proposed = prefix + "".join(blocks) + block + footer
        if (
            max(
                counter.count(proposed),
                counter.count(json_text(structure(selected + [claim["id"]]))),
            )
            <= budget
        ):
            selected.append(claim["id"])
            blocks.append(block)
            citations[claim["id"]] = refs
        else:
            omitted.append({"claim_id": claim["id"], "reason": "output_budget"})
    text = prefix + "".join(blocks) + f"Omitted claims: {len(omitted)}. See omission manifest.\n"
    if not selected or counter.count(text) > budget:
        raise ValueError("View budget cannot fit one complete grounded claim")
    representation = structure(selected)
    configuration = {
        "budget": budget,
        "query": query,
        "counter": counter.configuration,
        "selection": "facet-type-round-robin-v1",
        "mode": mode,
        "generation_id": source["generation_id"],
        "selected_claim_ids": selected,
        "context_tokens": context_tokens,
        "reserve_tokens": reserve_tokens,
        "omitted": omitted,
    }
    ai_id = repo.begin_ai("knowledge_view", "cpc-extractive-renderer", "1", "", "1", configuration)
    repo.finish_ai(ai_id, json_text(representation))
    all_citations = {
        f: repo.provenance("fragment", f)
        for c in claims
        if c["id"] in selected
        for f in c["fragment_ids"]
    }
    document_id = repo.save_structured(
        entity_id,
        ai_id,
        representation,
        claims,
        text,
        all_citations,
        {"algorithm": "budgeted-view-v1", **configuration},
        algorithm="budgeted-view-v1",
    )
    return {
        "document_id": document_id,
        "generation_id": source["generation_id"],
        "mode": mode,
        "markdown": text,
        "ai_context": text,
        "citations": citations,
        "structured": representation,
        "omission_manifest": {"generation_id": source["generation_id"], "omitted": omitted},
        "configuration": configuration,
        "output_tokens": counter.count(text),
    }
