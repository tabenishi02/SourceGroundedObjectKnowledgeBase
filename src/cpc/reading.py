"""Extractive reading copy with shared source references and a separate audit appendix."""

from .claims import build_claims
from .support import attribution, audit_claim, latest_review, review_index
from .views import order_claims


def reading_final(repo, entity_id, prompt_dir=None):
    source = build_claims(repo, entity_id)
    entity = repo.entity(entity_id)
    references, sources, appendix, blocks = {}, {}, {}, []
    reviews = review_index(repo, prompt_dir)
    for claim in order_claims(source["claims"], entity):
        audit = audit_claim(repo, claim)
        refs = []
        for support in audit["supports"]:
            for evidence in support["evidence"]:
                key = (evidence["url"], evidence["snapshot_id"])
                if key not in references:
                    ref = f"S{len(references) + 1}"
                    references[key] = ref
                    sources[ref] = {"url": key[0], "snapshot_id": key[1]}
                ref = references[key]
                if ref not in refs:
                    refs.append(ref)
        number = f"C{len(appendix) + 1}"
        review = latest_review(repo, audit, prompt_dir, reviews)
        appendix[number] = {"claim_id": claim["id"], "audit": audit, "review": review}
        blocks.append(
            f"## {claim['facet']} [{number}]\n{claim['text']}\n\n"
            + attribution(claim)
            + f"／支持判定: {review['verdict']} "
            + " ".join(f"[{ref}](#{ref.lower()})" for ref in refs)
            + "\n\n"
        )
    markdown = (
        f"# {entity['name']} — 閲覧用Final\n\n"
        "> 出典の主張を改変せず掲載。支持判定は真実性の認定ではありません。\n"
        "> 各C番号の実引用・帰属・時点・Fragmentは監査付録を参照。\n\n"
        + "".join(blocks)
        + "## 共有出典\n\n"
        + "".join(
            f"<a id='{ref.lower()}'></a>{ref}: {s['url']} / Snapshot {s['snapshot_id']}\n\n"
            for ref, s in sources.items()
        )
    )
    return {
        "markdown": markdown,
        "audit_manifest": appendix,
        "sources": sources,
        "generation_id": source["generation_id"],
        "claim_count": len(appendix),
    }
