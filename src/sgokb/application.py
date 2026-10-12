"""Application services shared by CLI and future UIs. No SQL or provider-specific logic."""

import json
from dataclasses import asdict
from pathlib import Path

from .domain import (
    EmbeddingSpace,
    EvidenceExtractionMode,
    MetadataOrigin,
    NormalizationStatus,
    SearchFilter,
    SnapshotCompleteness,
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
from .retrieval import EvidenceBudget, EvidencePackageSelector, ObjectEvidenceRetriever
from .search import HybridSearch


def _capture_locators(bundle):
    page_url = bundle.manifest["page"]["url"]
    values = [("url", page_url)]
    canonical_url = bundle.metadata.get("document", {}).get("canonical_url")
    if isinstance(canonical_url, str) and canonical_url.strip():
        values.append(("canonical_url", canonical_url.strip()))
    return tuple(values)


def _artifact_set_digest(bundle):
    payload = {
        path: {"sha256": digest(raw), "bytes": len(raw)}
        for path, raw in sorted(bundle.artifacts.items())
    }
    return digest(json.dumps(payload, sort_keys=True, separators=(",", ":")))


def _artifact_kind(logical_path):
    if logical_path == "manifest.json":
        return "capture_manifest"
    if logical_path == "checksums.json":
        return "checksums"
    if logical_path == "dom/main.html":
        return "rendered_dom"
    if logical_path.startswith("dom/frames/"):
        return "frame_dom"
    if logical_path == "archive/page.mhtml":
        return "mhtml"
    if logical_path.startswith("metadata/"):
        return "metadata"
    return "capture_artifact"


def _artifact_media_type(logical_path, document_content_type=None):
    if logical_path == "dom/main.html":
        return document_content_type or "text/html"
    if logical_path.startswith("dom/frames/"):
        return "text/html"
    if logical_path.endswith(".json"):
        return "application/json"
    if logical_path.endswith(".mhtml"):
        return "multipart/related"
    return None


def _normalization_input_paths(bundle, include_auxiliary):
    paths = ["dom/main.html"]
    if include_auxiliary:
        paths.extend(("metadata/frames.json", "metadata/shadow-dom.json"))
        paths.extend(
            frame["file"]
            for frame in bundle.metadata["frames"]
            if frame.get("capture_status") == "success" and frame.get("file")
        )
    return tuple(dict.fromkeys(paths))


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

    def import_source_path(self, path, *, source_id=None, label=None):
        """Import one validated Web Capture Bundle into the canonical Source chain.

        This is intentionally separate from ``import_path``. The latter remains the
        Prototype compatibility path until Phase L.
        """
        bundle = self.importer.read(path)
        store = self.repository.source_store
        manifest = bundle.manifest
        snapshot_id = manifest["capture_id"]
        existing = store.find_snapshot_by_id(snapshot_id)
        if existing is not None:
            stored_digest = store.snapshot_metadata(snapshot_id).get("artifact_set_sha256")
            if stored_digest != _artifact_set_digest(bundle):
                raise ValueError("Existing capture_id has different raw bytes")
            if source_id is not None and existing.source_id != source_id:
                raise ValueError("Existing capture_id belongs to another Source")
            effective = store.effective_snapshot(existing.source_id)
            return {
                "source": existing.source_id,
                "snapshot": snapshot_id,
                "duplicate": True,
                "effective": bool(effective and effective.snapshot_id == snapshot_id),
            }

        locators = _capture_locators(bundle)
        if source_id is not None:
            source = store.source_by_id(source_id)
            resolved_source_id = source.source_id
        else:
            candidates = {
                source.source_id
                for kind, value in locators
                for source in store.sources_by_locator(kind, value)
            }
            if len(candidates) > 1:
                raise ValueError("Ambiguous Source resolution from capture locators")
            resolved_source_id = (
                next(iter(candidates))
                if candidates
                else store.create_source(label or manifest["page"].get("title"))
            )

        locator_ids = {}
        for index, (kind, value) in enumerate(locators):
            locator_ids[(kind, value)] = store.ensure_locator(
                resolved_source_id, kind, value, preferred=index == 0
            )
        page_url = manifest["page"]["url"]
        observed_locator_id = locator_ids[("url", page_url)]
        completeness = {
            "success": SnapshotCompleteness.COMPLETE,
            "partial": SnapshotCompleteness.PARTIAL,
            "failed": SnapshotCompleteness.FAILED,
        }.get(manifest.get("completeness"))
        if completeness is None:
            raise ValueError("Unsupported capture completeness")

        document = bundle.metadata.get("document", {})
        store.create_snapshot(
            resolved_source_id,
            manifest["captured_at"],
            "web_capture",
            observed_locator_id=observed_locator_id,
            capture_tool=manifest.get("capture_tool", {}).get("name"),
            capture_version=manifest.get("capture_tool", {}).get("version"),
            completeness=completeness,
            title=manifest["page"].get("title"),
            manifest=manifest,
            metadata={
                "bundle_sha256": bundle.sha256,
                "artifact_set_sha256": _artifact_set_digest(bundle),
                "importer_version": self.importer.version,
                "capture_metadata": bundle.metadata,
            },
            warnings=manifest.get("warnings", []),
            snapshot_id=snapshot_id,
        )
        for logical_path, raw in bundle.artifacts.items():
            store.add_raw_artifact(
                snapshot_id,
                _artifact_kind(logical_path),
                bundle.path,
                digest(raw),
                len(raw),
                logical_path=logical_path,
                media_type=_artifact_media_type(logical_path, document.get("content_type")),
            )

        site, document_genre = classify(page_url)
        store.observe_classification(
            resolved_source_id,
            "resource_type",
            "web_page",
            MetadataOrigin.DETERMINISTIC,
            snapshot_id=snapshot_id,
        )
        if site:
            store.observe_classification(
                resolved_source_id,
                "site",
                site,
                MetadataOrigin.DETERMINISTIC,
                snapshot_id=snapshot_id,
            )
        store.observe_classification(
            resolved_source_id,
            "document_genre",
            document_genre,
            MetadataOrigin.DETERMINISTIC,
            snapshot_id=snapshot_id,
        )
        if document.get("content_type"):
            store.observe_classification(
                resolved_source_id,
                "media_type",
                document["content_type"],
                MetadataOrigin.CAPTURED,
                snapshot_id=snapshot_id,
            )
        for key in ("canonical_url", "language"):
            if document.get(key):
                store.observe_metadata(
                    resolved_source_id,
                    key,
                    document[key],
                    MetadataOrigin.CAPTURED,
                    snapshot_id=snapshot_id,
                )

        effective = store.effective_snapshot(resolved_source_id)
        if effective is None and completeness is not SnapshotCompleteness.FAILED:
            store.select_effective_snapshot(
                resolved_source_id,
                snapshot_id,
                origin_kind="automatic_initial",
                reason="first_usable_snapshot",
            )
            effective = store.snapshot_by_id(snapshot_id)
        return {
            "source": resolved_source_id,
            "snapshot": snapshot_id,
            "duplicate": False,
            "raw_artifacts": len(bundle.artifacts),
            "effective": bool(effective and effective.snapshot_id == snapshot_id),
        }

    def process_source_snapshot(self, snapshot_id, size=1000, overlap=100, include_auxiliary=False):
        """Normalize a canonical Snapshot and persist canonical Evidence only."""
        store = self.repository.source_store
        snapshot = store.snapshot_by_id(snapshot_id)
        artifacts = store.raw_artifacts(snapshot_id)
        by_path = {row["logical_path"]: row for row in artifacts if row["logical_path"]}
        manifest_artifact = by_path.get("manifest.json")
        if manifest_artifact is None:
            raise ValueError("Canonical Snapshot has no capture manifest Raw Artifact")
        bundle = self.importer.read(manifest_artifact["storage_ref"])
        stored_digest = store.snapshot_metadata(snapshot_id).get("artifact_set_sha256")
        if stored_digest != _artifact_set_digest(bundle):
            raise ValueError("Raw changed since canonical import; refusing reprocessing")

        page_url = bundle.manifest["page"]["url"]
        site, document_genre = classify(page_url)
        extractor = self.registry.select(site)
        input_paths = _normalization_input_paths(bundle, include_auxiliary)
        missing = [path for path in input_paths if path not in by_path]
        if missing:
            raise ValueError(f"Normalization input Raw Artifact missing: {missing[0]}")
        artifact_ids = [by_path[path]["id"] for path in input_paths]
        configuration = {
            "extractor": extractor.name,
            "extractor_version": extractor.version,
            "normalization": NORMALIZATION_VERSION,
            "chunk_size": size,
            "overlap": overlap,
            "include_auxiliary": include_auxiliary,
            "bundle_sha256": bundle.sha256,
        }

        try:
            blocks = extractor.extract(bundle, include_auxiliary)
            evidence = chunks(blocks, size, overlap)
            if not evidence:
                raise ValueError("Extraction produced no text")
            context = analyze(
                bundle,
                {
                    "title": snapshot.title or bundle.manifest["page"].get("title", ""),
                    "site": site,
                    "source_type": {
                        "social_post": "social",
                        "news_article": "news",
                    }.get(document_genre, document_genre),
                },
                blocks,
            )
        except Exception as error:
            store.create_normalization_run(
                snapshot_id,
                extractor.name,
                extractor.version,
                artifact_ids,
                configuration=configuration,
                output={"error_type": type(error).__name__, "error": str(error)},
                status=NormalizationStatus.FAILED,
            )
            raise

        run_id = store.create_normalization_run(
            snapshot_id,
            extractor.name,
            extractor.version,
            artifact_ids,
            configuration=configuration,
            output={
                "normalization_version": NORMALIZATION_VERSION,
                "blocks": [asdict(block) for block in blocks],
            },
            status=NormalizationStatus.COMPLETE,
        )
        language = bundle.metadata.get("document", {}).get("language") or None
        evidence_ids = []
        for ordinal, item in enumerate(evidence):
            metadata = {key: value for key, value in item.items() if key != "content"}
            evidence_id = store.add_evidence(
                run_id,
                item["content"],
                EvidenceExtractionMode.NORMALIZED,
                ordinal=ordinal,
                language=language,
                metadata=metadata,
            )
            location_ordinal = 0
            for position in item.get("positions", []):
                store.add_evidence_location(
                    evidence_id,
                    "dom_path",
                    {"artifact": item.get("artifact"), "path": position},
                    ordinal=location_ordinal,
                )
                location_ordinal += 1
            if item.get("section"):
                store.add_evidence_location(
                    evidence_id,
                    "heading_path",
                    {"headings": item["section"]},
                    ordinal=location_ordinal,
                )
                location_ordinal += 1
            store.add_evidence_location(
                evidence_id,
                "block_order",
                {"evidence_ordinal": ordinal, "start": item.get("start", 0)},
                ordinal=location_ordinal,
            )
            evidence_ids.append(evidence_id)

        for axis, key in (("publisher_kind", "publisher_type"), ("page_purpose", "page_purpose")):
            value = context.get(key)
            if value:
                store.observe_classification(
                    snapshot.source_id,
                    axis,
                    value,
                    MetadataOrigin.DETERMINISTIC,
                    snapshot_id=snapshot_id,
                )
        for key in (
            "page_summary",
            "subject_candidates",
            "source_published_at",
            "source_updated_at",
            "source_independence",
        ):
            value = context.get(key)
            if value is not None and value != "":
                store.observe_metadata(
                    snapshot.source_id,
                    key,
                    value,
                    MetadataOrigin.DETERMINISTIC,
                    snapshot_id=snapshot_id,
                )

        effective_snapshot = store.effective_snapshot(snapshot.source_id)
        effective_run = store.effective_run(snapshot_id)
        if (
            effective_snapshot is not None
            and effective_snapshot.snapshot_id == snapshot_id
            and effective_run is None
        ):
            store.select_effective_run(
                snapshot_id,
                run_id,
                origin_kind="automatic_initial",
                reason="first_successful_normalization",
            )
            effective_run = store.normalization_run(run_id)
        return {
            "source": snapshot.source_id,
            "snapshot": snapshot_id,
            "run": run_id,
            "blocks": len(blocks),
            "evidence": len(evidence_ids),
            "evidence_ids": evidence_ids,
            "extractor": extractor.name,
            "effective": bool(effective_run and effective_run["id"] == run_id),
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

    def retrieve_object_evidence(
        self,
        object_id,
        *,
        max_candidates=500,
        semantic=None,
        semantic_batch_size=32,
        manual_include=(),
        manual_exclude=(),
    ):
        """Retrieve canonical Evidence for one Object without generating Fragments."""
        result = ObjectEvidenceRetriever(self.repository, self.embedder).retrieve(
            object_id,
            max_candidates=max_candidates,
            semantic=semantic,
            semantic_batch_size=semantic_batch_size,
            manual_include=manual_include,
            manual_exclude=manual_exclude,
        )
        return dict(
            result,
            candidates=[asdict(candidate) for candidate in result["candidates"]],
        )

    def select_object_evidence(
        self,
        object_id,
        *,
        max_estimated_tokens=12000,
        max_bytes=65536,
        max_items=64,
        max_candidates=500,
        semantic=None,
        semantic_batch_size=32,
        manual_include=(),
        manual_exclude=(),
    ):
        """Build a bounded Evidence selection from the canonical F-03 candidate set."""
        retrieval = ObjectEvidenceRetriever(self.repository, self.embedder).retrieve(
            object_id,
            max_candidates=max_candidates,
            semantic=semantic,
            semantic_batch_size=semantic_batch_size,
            manual_include=manual_include,
            manual_exclude=manual_exclude,
        )
        budget = EvidenceBudget(
            max_estimated_tokens=max_estimated_tokens,
            max_bytes=max_bytes,
            max_items=max_items,
        )
        result = EvidencePackageSelector(budget).select(
            retrieval,
            protected_evidence_ids=manual_include,
        )
        return dict(
            result,
            controls={
                "manual_include": list(dict.fromkeys(manual_include)),
                "manual_exclude": list(dict.fromkeys(manual_exclude)),
            },
            selected=[asdict(item) for item in result["selected"]],
            omitted=[asdict(item) for item in result["omitted"]],
        )

    def legacy_capture_fragments(self, snapshot_id, entity_id, **options):
        from .capture import HighRecallCapture

        return HighRecallCapture(self).run(snapshot_id, entity_id, **options)

    def legacy_build_document(self, entity_id, **options):
        from .final import StructuredFinal

        return StructuredFinal(self).build(entity_id, **options)

    def legacy_fragment(self, snapshot_id, entity_id, limit=6, max_chars=5000):
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

    # Prototype Fragment / Final workflows are retained only for compatibility and research.
    # Canonical standard processing ends at Evidence and must not call these methods.
    def capture_fragments(self, snapshot_id, entity_id, **options):
        return self.legacy_capture_fragments(snapshot_id, entity_id, **options)

    def build_document(self, entity_id, **options):
        return self.legacy_build_document(entity_id, **options)

    def fragment(self, snapshot_id, entity_id, limit=6, max_chars=5000):
        return self.legacy_fragment(snapshot_id, entity_id, limit, max_chars)

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

    def legacy_generate(self, entity_id, query=None, limit=10):
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
            markdown, citations = self.legacy_render_document(entity["name"], parsed, selected)
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

    def generate(self, entity_id, query=None, limit=10):
        return self.legacy_generate(entity_id, query, limit)

    def legacy_render_document(self, name, parsed, selected):
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
