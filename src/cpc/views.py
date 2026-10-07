"""Budgeted extractive views with a separate complete omission manifest."""

import re
import unicodedata

from .budget import TokenCounter
from .claims import build_claims
from .domain import json_text


def overview_priority(claim, entity):
    """Prefer defining claims about the entity over incidental related material."""

    def normalized(value):
        return re.sub(r"\s+", "", unicodedata.normalize("NFKC", value or "")).casefold()

    facet = normalized(claim["facet"])
    own_subject = normalized(claim["subject"]) == normalized(entity["name"])
    peripheral = any(
        word in facet
        for word in (
            "カード",
            "スキル",
            "イベント",
            "ライブ",
            "楽曲",
            "pixiv",
            "グッズ",
            "ランキング",
            "売上",
            "card",
            "skill",
            "event",
            "song",
            "merchandise",
        )
    )
    defining = facet in {
        "identity",
        "definition",
        "overview",
        "概要",
        "定義",
        "基本情報",
        "作品概要",
        "登場作品",
    }
    foundation = facet in {
        "所属",
        "所属事務所",
        "所属ユニット",
        "ユニット所属",
        "affiliation",
        "所属作品",
        "シリーズ所属",
        "役割",
        "role",
        "ジャンル",
        "ゲームジャンル",
        "ゲームジャンル・特徴",
        "genre",
        "コンセプト",
        "concept",
        "ゲームシステム",
        "開発元",
        "開発会社",
        "developer",
        "制作会社",
        "提供元",
        "媒体",
        "platform",
        "性格",
        "personality",
        "人物像",
        "character_trait",
        "character_traits",
    }
    profile = any(
        word in facet
        for word in (
            "性格",
            "人物像",
            "特徴",
            "年齢",
            "身長",
            "誕生日",
            "趣味",
            "特技",
            "出身",
            "口癖",
            "声優",
            "cv",
            "personality",
            "character_trait",
            "profile",
        )
    )
    tier = 0 if defining else 1 if foundation else 2 if profile else 3
    if not own_subject or peripheral:
        tier = 4
    if claim["epistemic_type"] in {
        "public_perception",
        "promotional_claim",
        "derived_interpretation",
    }:
        tier = max(tier, 3)
    if claim["evidence_strength"] == "weak_inference":
        tier = max(tier, 3)
    return tier


def overview_topic(claim):
    facet = claim["facet"].casefold().strip()
    for topic, aliases in (
        (
            "definition",
            {
                "identity",
                "definition",
                "overview",
                "概要",
                "定義",
                "作品概要",
                "登場作品",
                "所属作品",
            },
        ),
        ("unit", {"所属ユニット", "ユニット所属", "affiliation"}),
        ("organization", {"所属", "所属事務所"}),
        ("personality", {"性格", "personality", "人物像", "character_trait", "character_traits"}),
        ("genre", {"ジャンル", "ゲームジャンル", "ゲームジャンル・特徴", "genre"}),
        ("developer", {"開発元", "開発会社", "developer", "制作会社"}),
    ):
        if facet in aliases:
            return topic
    return facet


def order_claims(claims, entity, query=None):
    terms = (query or "").casefold().split()
    groups = {}
    for claim in claims:
        relevance = sum(term in claim["text"].casefold() for term in terms)
        tier = overview_priority(claim, entity)
        groups.setdefault((-relevance, tier), {}).setdefault(overview_topic(claim), []).append(
            claim
        )
    ordered = []
    remaining = []
    seen_topics = set()
    for key in sorted(groups):
        facets = groups[key]
        for group in facets.values():
            group.sort(
                key=lambda c: (
                    -len(c["evidence_ids"]),
                    -int(entity["name"].replace(" ", "") in c["text"].replace(" ", "")),
                    len(c["text"]),
                    c["id"],
                )
            )
        # Cover defining facets before repeating one facet; no hash-order overview.
        topic_rank = {
            "definition": 0,
            "genre": 1,
            "unit": 1,
            "personality": 2,
            "developer": 2,
            "organization": 3,
        }
        facet_order = sorted(
            facets,
            key=lambda f: (
                topic_rank.get(f, 4),
                -len(facets[f][0]["evidence_ids"]),
                len(facets[f][0]["text"]),
                f,
            ),
        )
        for facet in facet_order:
            if facet not in seen_topics:
                ordered.append(facets[facet].pop(0))
                seen_topics.add(facet)
        remaining.append((facets, facet_order))
    while any(group for facets, _ in remaining for group in facets.values()):
        for facets, facet_order in remaining:
            for facet in facet_order:
                if facets[facet]:
                    ordered.append(facets[facet].pop(0))
    return ordered


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
    claims_by_id = {claim["id"]: claim for claim in claims}
    entity = repo.entity(entity_id)
    ordered = order_claims(claims, entity, query)
    name = entity["name"]
    purpose = {
        "short": "概要：対象の定義と主要な特徴",
        "standard": "基本情報：概要・所属・性格や仕組み・主要属性",
        "detailed": "詳細：基本情報に加えて補足・関連する主張",
        "context": "質問用資料：関連する主張と出典",
    }[mode]
    prefix = f"# {name}\n\n{purpose}\n\n> 出典に記載された主張の抜粋。真偽の確定は行いません。\n\n"
    selected, omitted, blocks, citations = [], [], [], {}

    def structure(selection):
        return {
            "trust": "untrusted_source_claims",
            "selected_claim_ids": selection,
            "omitted_count": len(claims) - len(selection),
            "claims": [claims_by_id[claim_id] for claim_id in selection],
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
        "selection": "entity-overview-priority-v2",
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
