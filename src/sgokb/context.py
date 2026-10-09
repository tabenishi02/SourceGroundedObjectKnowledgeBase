"""Deterministic page-level context; observations are not authority judgments."""

import json
import re

from bs4 import BeautifulSoup

VERSION = "page-context-v1"
FIELDS = {
    "source_type",
    "publisher_type",
    "page_purpose",
    "page_summary",
    "subject_candidates",
    "source_published_at",
    "source_updated_at",
    "source_independence",
}
# Small replaceable registry, deliberately conservative. Unknown hosts remain unknown.
OFFICIAL_HOSTS = {"idolmaster-official.jp", "bandainamcoent.co.jp", "shinycolors.idolmaster.jp"}


def structured_nodes(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from structured_nodes(child)
    elif isinstance(value, list):
        for child in value:
            yield from structured_nodes(child)


def analyze(bundle, snapshot, blocks):
    soup = BeautifulSoup(bundle.artifacts["dom/main.html"].decode("utf-8"), "html.parser")
    meta = {}
    for tag in soup.select("meta[content]"):
        meta[tag.get("property", tag.get("name", "")).lower()] = tag["content"]
    nodes = []
    for tag in soup.select('script[type="application/ld+json"]'):
        try:
            nodes.extend(structured_nodes(json.loads(tag.get_text())))
        except (ValueError, TypeError):
            pass
    types = {
        str(t)
        for n in nodes
        for t in (n.get("@type", []) if isinstance(n.get("@type"), list) else [n.get("@type", "")])
    }
    title = snapshot["title"]
    headings = [b.content for b in blocks if b.kind == "heading"]
    lead = " ".join(b.content for b in blocks if b.kind == "paragraph")[:400]
    signals = " ".join([title, *headings[:8], lead])
    source = snapshot["source_type"].replace("generic_web", "generic")
    host = snapshot["site"].lower()
    official = any(host == h or host.endswith("." + h) for h in OFFICIAL_HOSTS)
    if official:
        source, publisher = "official", "official"
    elif "Product" in types:
        source, publisher = "commerce", "commercial"
    else:
        publisher = {
            "encyclopedia": "community",
            "wiki": "community",
            "bbs": "anonymous",
            "social": "individual",
            "blog": "individual",
            "news": "editorial",
            "commerce": "commercial",
        }.get(source, "unknown")
    purpose = "unknown"
    for pattern, value in [
        (r"レビュー|review|感想", "product_review" if source == "commerce" else "opinion"),
        (r"考察|分析|analysis", "analysis"),
        (r"攻略|使い方|guide", "guide"),
        (r"キャラクター|プロフィール|character", "character_profile"),
        (r"作品概要|ゲーム概要|作品紹介", "work_introduction"),
    ]:
        if re.search(pattern, signals, re.I):
            purpose = value
            break
    if purpose == "unknown":
        purpose = {
            "news": "news_report",
            "bbs": "discussion",
            "social": "daily_post",
            "commerce": "product_description",
            "encyclopedia": "concept_explanation",
        }.get(source, "unknown")
    # The summary is an extract, never a model-authored factual conclusion.
    summary = meta.get("description", meta.get("og:description", lead))[:600]
    names = [title, *headings[:5]] + [
        n.get("name") for n in nodes if isinstance(n.get("name"), str)
    ]
    return {
        "source_type": source,
        "publisher_type": publisher,
        "page_purpose": purpose,
        "page_summary": summary,
        "subject_candidates": list(dict.fromkeys(n for n in names if n))[:12],
        "source_published_at": meta.get("article:published_time")
        or next(
            (n["datePublished"] for n in nodes if isinstance(n.get("datePublished"), str)), None
        ),
        "source_updated_at": meta.get("article:modified_time")
        or next((n["dateModified"] for n in nodes if isinstance(n.get("dateModified"), str)), None),
        "source_independence": {"relationship": "unknown", "depends_on_sources": []},
        "signals": {
            "title": title,
            "headings": headings[:12],
            "json_ld_types": sorted(types),
            "summary_origin": "meta" if "description" in meta else "extracted_lead",
        },
    }


def effective_context(deterministic, inferred=None, overrides=None):
    inferred, overrides = inferred or {}, overrides or {}
    for patch in (inferred, overrides):
        if set(patch) - FIELDS:
            raise ValueError("Unknown page context fields")
        for key, value in patch.items():
            if key == "subject_candidates":
                if not isinstance(value, list) or any(not isinstance(n, str) for n in value):
                    raise ValueError("Subject candidates must be strings")
            elif key == "source_independence":
                if not isinstance(value, dict):
                    raise ValueError("Source independence must be an object")
            elif value is not None and not isinstance(value, str):
                raise ValueError("Context fields must be strings or null")
    return {**deterministic, **inferred, **overrides}
