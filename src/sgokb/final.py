"""Hierarchical, extractive final knowledge. Raw fragments are never merged in storage."""

import re
from collections import defaultdict

from .domain import digest, json_text

CATEGORIES = {
    "fact": "facts",
    "source_interpretation": "source_interpretations",
    "derived_interpretation": "derived_interpretations",
    "public_perception": "public_perception",
    "promotional_claim": "promotional_claims",
}
LABELS = {
    "facts": "事実主張",
    "source_interpretations": "資料の考察",
    "derived_interpretations": "SGOKBによる考察",
    "public_perception": "感想・評判",
    "promotional_claims": "宣伝的主張",
    "unknown": "未分類（旧Schema）",
}


def cluster_fragments(rows):
    groups = {}
    for row in rows:
        m = row["metadata"]
        # Conservative similarity: only whitespace/punctuation variants of the same claim.
        # Different claimant, temporal context, epistemic type or strength stays separate.
        key = json_text(
            [
                row["facet"],
                m.get("epistemic_type", "unknown"),
                m.get("asserted_by", "unknown"),
                m.get("evidence_strength", "unknown"),
                m.get("temporal_context", {}),
                m.get("conflict_group"),
                re.sub(r"[\s。．.!！]+", "", row["content"]),
            ]
        )
        if key not in groups:
            groups[key] = {
                "id": digest(key)[:24],
                "text": row["content"],
                "facet": row["facet"],
                "epistemic_type": m.get("epistemic_type", "unknown"),
                "evidence_strength": m.get("evidence_strength", "unknown"),
                "asserted_by": m.get("asserted_by", "unknown"),
                "temporal_context": m.get("temporal_context", {}),
                "conflict_group": m.get("conflict_group"),
                "fragment_ids": [],
                "evidence_ids": [],
                "context_ids": [],
            }
        cluster = groups[key]
        cluster["fragment_ids"].append(row["id"])
        cluster["evidence_ids"].extend(m.get("evidence_ids", []))
        if m.get("context_id"):
            cluster["context_ids"].append(m["context_id"])
    for cluster in groups.values():
        for field in ("evidence_ids", "context_ids"):
            cluster[field] = list(dict.fromkeys(cluster[field]))
    return list(groups.values())


def ordering_input(cluster):
    return {
        k: v for k, v in cluster.items() if k not in {"fragment_ids", "evidence_ids", "context_ids"}
    }


def conflicts(clusters):
    explicit, numeric = defaultdict(list), defaultdict(list)
    for c in clusters:
        if c["conflict_group"]:
            explicit[c["conflict_group"]].append(c)
        # Candidate only: numeric differences under otherwise identical wording/context.
        if re.search(r"\d+", c["text"]):
            key = json_text(
                [
                    re.sub(r"\d+", "#", c["text"]),
                    c["facet"],
                    c["epistemic_type"],
                    c["temporal_context"],
                ]
            )
            numeric[key].append(c)
    result, seen = [], set()
    for method, groups in (("reported", explicit), ("numeric_candidate", numeric)):
        for key, items in groups.items():
            ids = tuple(sorted(c["id"] for c in items))
            if len({c["text"] for c in items}) > 1 and ids not in seen:
                seen.add(ids)
                result.append(
                    {
                        "id": digest(key)[:24],
                        "method": method,
                        "status": "unresolved",
                        "alternatives": [
                            {
                                "text": c["text"],
                                "cluster_id": c["id"],
                                "fragment_ids": c["fragment_ids"],
                            }
                            for c in items
                        ],
                    }
                )
    return result


def render(rep, citations):
    lines = [
        "# " + rep["entity"]["name"],
        "",
        "> 出典に記載された主張の整理。真偽の確定は行いません。",
        "",
    ]
    numbers = {}
    for key, label in LABELS.items():
        claims = rep.get(key, [])
        if not claims:
            continue
        lines.extend(["## " + label, ""])
        previous = None
        for claim in claims:
            if claim["facet"] != previous:
                previous = claim["facet"]
                lines.extend(["### " + previous.replace("\n", " "), ""])
            labels = []
            for fragment_id in claim["fragment_ids"]:
                numbers.setdefault(fragment_id, len(numbers) + 1)
                labels.append(f"[^c{numbers[fragment_id]}]")
            lines.extend(
                [
                    "- " + claim["text"].replace("\n", " ") + " " + "".join(labels),
                    f"  （主張主体: {claim['asserted_by']} / "
                    f"根拠形式: {claim['evidence_strength']}）",
                    "",
                ]
            )
    if rep["conflicts"]:
        lines.extend(["## 資料間の相違・矛盾候補", ""])
        for group in rep["conflicts"]:
            lines.append(
                "- 未解決（"
                + group["method"]
                + "）: "
                + " / ".join(
                    a["text"] + " " + "".join(f"[^c{numbers[f]}]" for f in a["fragment_ids"])
                    for a in group["alternatives"]
                )
            )
        lines.append("")
    if rep["timeline"]:
        lines.extend(["## 主張の時系列", ""])
        for claim in rep["timeline"]:
            lines.append(
                "- "
                + json_text(claim["temporal_context"])
                + ": "
                + claim["text"]
                + " "
                + "".join(f"[^c{numbers[f]}]" for f in claim["fragment_ids"])
            )
        lines.append("")
    lines.extend(
        [
            "## 資料について",
            "",
            "複数の出典は独立した裏付けとは限りません。取得時刻と主張の時系列は別に保持しています。",
            "",
        ]
    )
    for note in rep["source_notes"]:
        context = note.get("page_context", {})
        lines.append(
            f"- {note['title']} / {context.get('source_type', 'unknown')} / "
            f"{context.get('publisher_type', 'unknown')} / {context.get('page_purpose', 'unknown')}"
        )
    lines.append("")
    for fragment_id, number in numbers.items():
        refs = "; ".join(
            f"{r['url']} (Snapshot `{r['snapshot_id']}`, Evidence `{r['evidence_id']}`, "
            f"{r['metadata']['artifact']}, {', '.join(r['metadata']['positions'])})"
            for r in citations[fragment_id]["evidence"]
        )
        lines.extend([f"[^c{number}]: Fragment `{fragment_id}` → {refs}", ""])
    return "\n".join(lines)


class StructuredFinal:
    def __init__(self, app):
        self.app, self.repo = app, app.repository

    def build(self, entity_id, use_llm=False, batch_size=24, max_chars=8000, query=None):
        if batch_size < 1 or max_chars < 1000:
            raise ValueError("Invalid final batch budget")
        entity = self.repo.entity(entity_id)
        rows = self.repo.related_fragments(entity_id)
        if query:
            # Optional query filters the complete entity set through the existing lexical ranker.
            from .domain import SearchFilter

            eligible = self.repo.candidates(SearchFilter(entity=entity_id))
            matches = self.repo.lexical(query, eligible, len(eligible))
            ids = {r["target_id"] for r in matches if r["kind"] == "fragment"}
            rows = [r for r in rows if r["id"] in ids]
        if not rows:
            raise ValueError("No related active fragments")
        clusters = cluster_fragments(rows)
        local_groups = defaultdict(list)
        for cluster in clusters:
            local_groups[(cluster["epistemic_type"], cluster["facet"])].append(cluster)
        rep = {
            "version": "final-knowledge-v1",
            "entity": entity,
            "overview": [],
            **{k: [] for k in LABELS},
            "relationships": [],
            "timeline": [],
            "conflicts": conflicts(clusters),
            "source_notes": [],
        }
        ai_ids = []
        for (kind, facet), group in sorted(local_groups.items()):
            # Hierarchical merge concatenates supported claims; never feeds the complete set to LLM.
            bounded, used = [], 0
            partitions = []
            for c in group:
                length = len(json_text(ordering_input(c)))
                if length > max_chars:
                    raise ValueError("Cluster exceeds final input budget")
                if bounded and (len(bounded) >= batch_size or used + length > max_chars):
                    partitions.append(bounded)
                    bounded, used = [], 0
                bounded.append(c)
                used += length
            if bounded:
                partitions.append(bounded)
            for partition in partitions:
                if use_llm:
                    ai_id, _, output = self.app.call_llm(
                        "final_local_order",
                        "final_order",
                        {
                            "entity": entity,
                            "facet": facet,
                            "epistemic_type": kind,
                            "clusters": [ordering_input(c) for c in partition],
                        },
                    )
                    ai_ids.append(ai_id)
                    order = output.get("ordered_cluster_ids") if isinstance(output, dict) else None
                    allowed = {c["id"]: c for c in partition}
                    if (
                        not isinstance(order, list)
                        or any(not isinstance(i, str) for i in order)
                        or len(order) != len(allowed)
                        or set(order) != set(allowed)
                    ):
                        self.repo.finish_ai(ai_id, error="InvalidClusterPermutation")
                        raise ValueError("Final ordering must retain every cluster exactly once")
                    partition = [allowed[i] for i in order]
                rep[CATEGORIES.get(kind, "unknown")].extend(partition)
        for cluster in clusters:
            if any(v is not None for v in cluster["temporal_context"].values()):
                rep["timeline"].append(cluster)
            if any(w in cluster["facet"].lower() for w in ("関係", "relationship", "所属")):
                rep["relationships"].append(cluster)
        citations = {row["id"]: self.repo.provenance("fragment", row["id"]) for row in rows}
        notes = {}
        for provenance in citations.values():
            for e, context in zip(provenance["evidence"], provenance["page_contexts"]):
                context_id = context["id"] if context else None
                notes[(e["snapshot_id"], e["run_id"], context_id)] = {
                    "context_id": context_id,
                    "snapshot_id": e["snapshot_id"],
                    "normalized_run": e["run_id"],
                    "url": e["url"],
                    "title": e["title"],
                    "captured_at": e["captured_at"],
                    "page_context": context["effective"] if context else {},
                }
        rep["source_notes"] = list(notes.values())
        markdown = render(rep, citations)
        config = {
            "algorithm": "extractive-hierarchy-v1",
            "query": query,
            "batch_size": batch_size,
            "max_chars": max_chars,
            "local_ai_runs": ai_ids,
            "fragment_ids": list(citations),
            "unsupported_additions": "disabled",
        }
        # The final merge itself is a deterministic derived generation with a processing ledger.
        ai_id = self.repo.begin_ai(
            "structured_final",
            "sgokb-extractive-renderer",
            "1",
            "",
            "1",
            {"configuration": config, "cluster_ids": [c["id"] for c in clusters]},
        )
        self.repo.finish_ai(ai_id, json_text(rep))
        document_id = self.repo.save_structured(
            entity_id, ai_id, rep, clusters, markdown, citations, config
        )
        return {
            "document_id": document_id,
            "entity": entity_id,
            "citations": len(citations),
            "clusters": len(clusters),
            "structured": rep,
            "markdown": markdown,
            "ai_context": json_text({"trust": "untrusted_source_claims", "knowledge": rep}),
        }
