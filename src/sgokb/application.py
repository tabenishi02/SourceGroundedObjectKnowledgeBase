"""Application services shared by CLI and future UIs. No SQL or provider-specific logic."""

import json
from dataclasses import asdict
from pathlib import Path

from .domain import (
    EmbeddingSpace,
    SearchFilter,
    digest,
    json_text,
    validate_fragments,
    validate_vectors,
)
from .ingestion import (
    NORMALIZATION_VERSION,
    ExtractorRegistry,
    WebCaptureImporter,
    analyze,
    chunks,
    classify,
)
from .search import HybridSearch


class Application:
    def __init__(
        self, repository, llm=None, embedder=None, registry=None, prompt_dir=None, reranker=None
    ):
        self.repository, self.llm, self.embedder = repository, llm, embedder
        self.importer = WebCaptureImporter()
        self.reranker = reranker
        self.registry = registry or ExtractorRegistry()
        self.prompt_dir = Path(prompt_dir) if prompt_dir else Path(__file__).with_name("prompts")

    def import_path(self, path):
        bundle = self.importer.read(path)
        return self.repository.import_bundle(bundle, *classify(bundle.manifest["page"]["url"]))

    def process(self, snapshot_id, size=1000, overlap=100, include_auxiliary=False):
        snapshot = self.repository.snapshot(snapshot_id)
        if not snapshot:
            raise ValueError("Unknown snapshot ID")
        bundle = self.importer.read(snapshot["raw_path"])
        if bundle.sha256 != snapshot["raw_sha256"]:
            raise ValueError("Raw changed since import; refusing reprocessing")
        extractor = self.registry.select(snapshot["site"])
        blocks = extractor.extract(bundle, include_auxiliary)
        evidence = chunks(blocks, size, overlap)
        if not evidence:
            raise ValueError("Extraction produced no text")
        configuration = {
            "extractor": extractor.name,
            "extractor_version": extractor.version,
            "normalization": NORMALIZATION_VERSION,
            "chunk_size": size,
            "overlap": overlap,
            "include_auxiliary": include_auxiliary,
            "raw_sha256": bundle.sha256,
        }
        run = self.repository.save_normalized(
            snapshot,
            [asdict(b) for b in blocks],
            evidence,
            configuration,
            analyze(bundle, snapshot, blocks),
        )
        return {
            "snapshot": snapshot_id,
            "run": run,
            "blocks": len(blocks),
            "evidence": len(evidence),
            "extractor": extractor.name,
        }

    def prompt(self, name):
        prompt = (self.prompt_dir / (name + ".md")).read_text(encoding="utf-8")
        first = prompt.splitlines()[0]
        if not first.startswith("version: "):
            raise ValueError("Prompt must declare version on first line")
        return prompt, first[9:] + ":" + digest(prompt)

    def call_llm(self, task, prompt_name, payload, response_schema=None):
        if self.llm is None:
            raise ValueError("Real LLM provider required for this stage")
        prompt, version = self.prompt(prompt_name)
        schema = response_schema or json.loads(
            (self.prompt_dir / (prompt_name + ".schema.json")).read_text(encoding="utf-8")
        )
        # Text-only providers also need the complete contract, not merely its filename.
        prompt += "\nResponse JSON Schema (SGOKB instruction):\n" + json_text(schema)
        version += ":" + digest(prompt)
        version += ":" + digest(json_text(schema))
        ai_id = self.repository.begin_ai(
            task,
            self.llm.model,
            self.llm.revision,
            prompt,
            version,
            {
                "payload": payload,
                "response_schema": schema,
                "provider_configuration": getattr(self.llm, "configuration", {}),
            },
        )
        self.last_ai_id = ai_id
        output = None
        observed = False
        try:
            output = self.llm.complete(prompt, payload, schema=schema)
            self.repository.observe_ai(ai_id, getattr(self.llm, "last_observation", {}))
            observed = True
            raw = output.strip()
            if raw.startswith("<|channel|>final") and "<|message|>" in raw:
                raw = raw.split("<|message|>", 1)[1].strip()
            if raw.startswith("```") and raw.endswith("```"):
                raw = "\n".join(raw.splitlines()[1:-1])
            parsed = json.loads(raw)
            self.repository.finish_ai(ai_id, output)
        except Exception as error:
            output = output if output is not None else getattr(self.llm, "last_output", None)
            if not observed:
                self.repository.observe_ai(ai_id, getattr(self.llm, "last_observation", {}))
            self.repository.finish_ai(ai_id, output, type(error).__name__)
            raise
        return ai_id, version, parsed

    def capture_fragments(self, snapshot_id, entity_id, **options):
        from .capture import HighRecallCapture

        return HighRecallCapture(self).run(snapshot_id, entity_id, **options)

    def build_document(self, entity_id, **options):
        from .final import StructuredFinal

        return StructuredFinal(self).build(entity_id, **options)

    def fragment(self, snapshot_id, entity_id, limit=6, max_chars=5000):
        snapshot = self.repository.snapshot(snapshot_id)
        if not snapshot or not snapshot["active_run"]:
            raise ValueError("Process snapshot before extracting fragments")
        entity = self.repository.entity(entity_id)
        evidence = self.repository.evidence(snapshot_id)
        names = [entity["name"], *entity["aliases"]]

        def relevance(row):
            metadata = json.loads(row["metadata"])
            section = " / ".join(metadata["section"])
            substantive = bool(set(metadata["kinds"]) & {"paragraph", "table", "quote", "post"})
            noise = any(
                term in section
                for term in ("関連イラスト", "関連小説", "関連記事", "関連動画", "目次")
            )
            return (
                min(3, sum(row["content"].count(n) for n in names if n))
                + (8 if any(n in section for n in names if n) else 0)
                + (4 if substantive and len(row["content"]) >= 40 else -8)
                - (40 if noise else 0)
            )

        evidence.sort(key=lambda e: -relevance(e))
        chosen, used = [], 0
        for row in evidence[:limit]:
            if used + len(row["content"]) > max_chars:
                break
            chosen.append(
                {
                    "id": row["id"],
                    "content": row["content"],
                    "metadata": json.loads(row["metadata"]),
                }
            )
            used += len(row["content"])
        if not chosen:
            raise ValueError("No evidence within fragment input budget")
        payload = {"entity": entity, "evidence": chosen}
        ai_id, version, parsed = self.call_llm("fragment", "fragment_extraction", payload)
        try:
            items = validate_fragments(parsed, {e["id"] for e in chosen})
            # An empty valid result is recorded but never replaces an existing useful generation.
            if not items:
                return {
                    "snapshot": snapshot_id,
                    "entity": entity_id,
                    "fragments": 0,
                    "ai_run": ai_id,
                }
            ids = self.repository.save_fragments(
                snapshot,
                entity_id,
                items,
                ai_id,
                {
                    "prompt_version": version,
                    "limit": limit,
                    "max_chars": max_chars,
                    "selection": "entity-section-structure-v1",
                },
            )
        except Exception as error:
            self.repository.finish_ai(ai_id, error=type(error).__name__)
            raise
        return {
            "snapshot": snapshot_id,
            "entity": entity_id,
            "fragments": len(ids),
            "fragment_ids": ids,
            "ai_run": ai_id,
        }

    def embed(self, filters=SearchFilter(), batch_size=16):
        if self.embedder is None:
            raise ValueError("Real embedding provider required for this stage")
        if batch_size < 1:
            raise ValueError("Batch size must be positive")
        rows = self.repository.candidates(filters)
        if not rows:
            return {"embedded": 0}
        # Build the requested generation before a single atomic promotion.
        vectors = []
        dimension = None
        for start in range(0, len(rows), batch_size):
            batch = rows[start : start + batch_size]
            output = self.embedder.embed([r["content"] for r in batch])
            size = validate_vectors(output, len(batch))
            if dimension is not None and dimension != size:
                raise ValueError("Embedding dimension changed between batches")
            dimension = size
            vectors.extend(output)
        space = EmbeddingSpace(
            self.embedder.model, self.embedder.revision, dimension, self.embedder.configuration
        )
        self.repository.save_embeddings(space, rows, vectors)
        return {"embedded": len(rows), "space": space.key, "dimension": dimension}

    def search(self, query, filters=SearchFilter(), limit=10, mode="hybrid"):
        return HybridSearch(self.repository, self.embedder, reranker=self.reranker).search(
            query, filters, limit, mode
        )

    def generate(self, entity_id, query=None, limit=10):
        entity = self.repository.entity(entity_id)
        query = query or entity["name"]
        results = self.search(query, SearchFilter(entity=entity_id), min(1000, limit * 5))
        selected = [r for r in results if r["kind"] == "fragment"][:limit]
        if not selected:
            raise ValueError("No related fragments found; run fragment and embed first")
        payload = {
            "entity": entity,
            "query": query,
            "fragments": [
                {
                    "id": r["target_id"],
                    "facet": r["facet"],
                    "content": r["content"],
                    "evidence_ids": [
                        e["evidence_id"]
                        for e in self.repository.provenance("fragment", r["target_id"])["evidence"]
                    ],
                }
                for r in selected
            ],
        }
        evidence_pool = {}
        for row in selected:
            for evidence in self.repository.provenance("fragment", row["target_id"])["evidence"]:
                evidence_pool[evidence["evidence_id"]] = {
                    "id": evidence["evidence_id"],
                    "content": evidence["content"],
                    "section": evidence["metadata"]["section"],
                    "snapshot_id": evidence["snapshot_id"],
                }
        payload["evidence"] = list(evidence_pool.values())
        ai_id, version, parsed = self.call_llm("final_document", "final_document", payload)
        try:
            markdown, citations = self.render_document(entity["name"], parsed, selected)
            configuration = {
                "prompt_version": version,
                "query": query,
                "selected": [
                    {
                        "id": r["target_id"],
                        "kind": r["kind"],
                        "score": r["rerank_score"],
                        "channels": r["channels"],
                    }
                    for r in selected
                ],
                "reranker": "rrf60-literal-v1",
            }
            document_id = self.repository.save_document(
                entity_id, ai_id, markdown, citations, configuration
            )
        except Exception as error:
            self.repository.finish_ai(ai_id, error=type(error).__name__)
            raise
        return {
            "document_id": document_id,
            "entity": entity_id,
            "citations": len(citations),
            "markdown": markdown,
        }

    def render_document(self, name, parsed, selected):
        if not isinstance(parsed, dict) or not isinstance(parsed.get("sections"), list):
            raise ValueError("Expected final sections array")
        allowed = {r["target_id"] for r in selected}
        citations, numbers = {}, {}
        lines = [
            "# " + name,
            "",
            "> AIによる試作文書。引用先の原資料で内容を確認してください。",
            "",
        ]
        claims_count = 0
        for section in parsed["sections"]:
            if not isinstance(section, dict) or not isinstance(section.get("heading"), str):
                raise ValueError("Invalid section heading")
            lines += ["## " + section["heading"].replace("\n", " "), ""]
            claims = section.get("claims")
            if not isinstance(claims, list):
                raise ValueError("Expected claims array")
            for claim in claims:
                if (
                    not isinstance(claim, dict)
                    or not isinstance(claim.get("text"), str)
                    or not claim["text"].strip()
                ):
                    raise ValueError("Claim text required")
                refs = claim.get("fragment_ids")
                if not isinstance(refs, list) or not refs or any(r not in allowed for r in refs):
                    raise ValueError("Claim references unknown fragment")
                labels = []
                for fragment_id in dict.fromkeys(refs):
                    if fragment_id not in numbers:
                        numbers[fragment_id] = len(numbers) + 1
                        citations[fragment_id] = self.repository.provenance("fragment", fragment_id)
                    labels.append(f"[^c{numbers[fragment_id]}]")
                lines += [claim["text"].strip() + " " + "".join(labels), ""]
                claims_count += 1
        if not claims_count:
            raise ValueError("Final document has no grounded claims")
        for fragment_id, number in numbers.items():
            evidence = citations[fragment_id]["evidence"]
            refs = "; ".join(
                f"{r['url']} (Snapshot `{r['snapshot_id']}`, Evidence "
                f"`{r['evidence_id']}`, {r['metadata']['artifact']}, "
                f"{', '.join(r['metadata']['positions'])})"
                for r in evidence
            )
            lines += [f"[^c{number}]: Fragment `{fragment_id}` → {refs}", ""]
        return "\n".join(lines), citations
