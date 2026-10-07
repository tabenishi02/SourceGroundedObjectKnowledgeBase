"""Budgeted extractive views with a separate complete omission manifest."""

import re
import unicodedata

from .budget import TokenCounter
from .claims import build_claims
from .domain import json_text
from .support import attribution, audit_claim, latest_review, review_index

OVERVIEW_SLOTS = {
    "Character": {"definition", "affiliation", "personality"},
    "Work": {"definition", "genre", "mechanism"},
    "Concept": {"definition", "purpose", "特徴"},
}


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
        "目的",
        "用途",
        "purpose",
        "distinction",
        "features",
        "仕組み",
        "mechanism",
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
        ("purpose", {"目的", "用途", "purpose"}),
        ("mechanism", {"ゲームシステム", "仕組み", "mechanism", "中心的な体験"}),
        ("特徴", {"特徴", "特徴・区別", "distinction", "features"}),
        ("role", {"役割", "role", "立場"}),
    ):
        if facet in aliases:
            return topic
    return facet


def overview_slot(claim, entity):
    topic = overview_topic(claim)
    if entity.get("type") == "Character" and topic in {"unit", "organization", "role"}:
        return "affiliation"
    return topic


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
    supported_only=False,
    prompt_dir=None,
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
    audit_manifest = {}
    reviews = review_index(repo, prompt_dir)
    required = OVERVIEW_SLOTS.get(entity.get("type"), {"definition", "purpose", "特徴"})
    conflicts = {}
    for claim in claims:
        if claim.get("conflict_group"):
            conflicts.setdefault(claim["conflict_group"], []).append(claim["id"])
    if not query:
        first = {}
        for claim in ordered:
            topic = overview_slot(claim, entity)
            if topic in required and overview_priority(claim, entity) < 3:
                first.setdefault(topic, claim)
        priorities = list(first.values())
        priority_ids = {c["id"] for c in priorities}
        ordered = priorities + [c for c in ordered if c["id"] not in priority_ids]

    def footer(selection):
        missing = sorted(required - covered_slots(selection))
        return (
            f"Omitted claims: {len(claims) - len(selection)}. See omission manifest.\n"
            + ("概要の不足項目: " + ", ".join(missing) + "\n" if not query and missing else "")
            + "出典・引用・支持判定の詳細: audit manifest [S番号]。\n"
        )

    def covered_slots(selection):
        return {
            overview_slot(claims_by_id[i], entity)
            for i in selection
            if overview_priority(claims_by_id[i], entity) < 3
        }

    def structure(selection):
        return {
            "trust": "untrusted_source_claims",
            "selected_claim_ids": selection,
            "omitted_count": len(claims) - len(selection),
            "claims": [claims_by_id[claim_id] for claim_id in selection],
        }

    for claim in ordered:
        if counter.count(json_text(structure(selected + [claim["id"]]))) > budget:
            omitted.append({"claim_id": claim["id"], "reason": "output_budget"})
            continue
        audit = audit_claim(repo, claim)
        review = latest_review(repo, audit, prompt_dir, reviews)
        if supported_only and review["verdict"] != "supported":
            omitted.append({"claim_id": claim["id"], "reason": "support_" + review["verdict"]})
            continue
        refs = [f"[S{len(selected) + 1}]"]
        label = {
            "supported": "機械判定で整合",
            "unsupported": "支持不足",
            "uncertain": "要確認",
            "unreviewed": "支持未確認",
        }[review["verdict"]]
        alternatives = [
            i for i in conflicts.get(claim.get("conflict_group"), []) if i != claim["id"]
        ]
        block = (
            f"## {claim['facet']} [{claim['epistemic_type']}]\n"
            f"{claim['text']}\n"
            + f"{attribution(claim)}／{label} {refs[0]}\n"
            + (
                "相違する主張あり。監査付録のalternative_claim_idsを参照。\n"
                if alternatives
                else ""
            )
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
            + "\n\n"
        )
        proposed = prefix + "".join(blocks) + block + footer(selected + [claim["id"]])
        if (
            max(
                counter.count(proposed),
                counter.count(json_text(structure(selected + [claim["id"]]))),
            )
            <= budget
        ):
            selected.append(claim["id"])
            blocks.append(block)
            citations[claim["id"]] = list(
                dict.fromkeys(
                    f"{e['url']} / Snapshot {e['snapshot_id']} / Evidence {e['evidence_id']}"
                    for support in audit["supports"]
                    for e in support["evidence"]
                )
            )
            audit_manifest[refs[0]] = {
                "claim_id": claim["id"],
                "audit": audit,
                "review": review,
                "alternative_claim_ids": alternatives,
            }
        else:
            omitted.append({"claim_id": claim["id"], "reason": "output_budget"})
    text = prefix + "".join(blocks) + footer(selected)
    if (not selected and not supported_only) or counter.count(text) > budget:
        raise ValueError("View budget cannot fit one complete grounded claim")
    representation = structure(selected)
    configuration = {
        "budget": budget,
        "query": query,
        "counter": counter.configuration,
        "selection": "overview-slots-audited-v3",
        "mode": mode,
        "generation_id": source["generation_id"],
        "selected_claim_ids": selected,
        "context_tokens": context_tokens,
        "reserve_tokens": reserve_tokens,
        "omitted": omitted,
        "supported_only": supported_only,
        "missing_overview_slots": sorted(required - covered_slots(selected)),
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
        "audit_manifest": audit_manifest,
        "missing_overview_slots": configuration["missing_overview_slots"],
    }
