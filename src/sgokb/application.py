"""Application services shared by CLI and future UIs. No SQL or provider-specific logic."""

import json
from dataclasses import asdict

from .domain import (
    EvidenceExtractionMode,
    MetadataOrigin,
    NormalizationStatus,
    SnapshotCompleteness,
    digest,
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
    def __init__(self, repository, embedder=None, registry=None):
        self.repository, self.embedder = repository, embedder
        self.importer = WebCaptureImporter()
        self.registry = registry or ExtractorRegistry()

    def import_source_path(self, path, *, source_id=None, label=None):
        """Import one validated Web Capture Bundle into the canonical Source chain."""
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

    def list_source_object_associations(self, object_id):
        """Return persistent Source↔Object operator associations for one canonical Object."""
        self.repository.object_store.get_object(object_id)
        return list(self.repository.source_store.associations_for_object(object_id))

    def set_source_object_association(
        self,
        object_id,
        source_id,
        status,
        *,
        subject_relationship=None,
        note=None,
    ):
        """Create or replace one manual Source↔Object association."""
        self.repository.object_store.get_object(object_id)
        self.repository.source_store.source_by_id(source_id)
        self.repository.source_store.associate_object(
            source_id,
            object_id,
            status,
            subject_relationship=subject_relationship,
            origin_kind="manual",
            note=note,
        )
        return self.repository.source_store.association_for_object_source(object_id, source_id)

    def clear_source_object_association(self, object_id, source_id):
        """Remove the explicit association; this is not the same as setting excluded."""
        self.repository.object_store.get_object(object_id)
        self.repository.source_store.source_by_id(source_id)
        removed = self.repository.source_store.remove_object_association(source_id, object_id)
        return {"object_id": object_id, "source_id": source_id, "cleared": removed}

    def suggest_source_associations(
        self,
        object_id,
        *,
        max_candidates=500,
        semantic=None,
        semantic_batch_size=32,
    ):
        """Aggregate F-03 Evidence candidates into read-only Source association suggestions."""
        retrieval = self.retrieve_object_evidence(
            object_id,
            max_candidates=max_candidates,
            semantic=semantic,
            semantic_batch_size=semantic_batch_size,
        )
        existing = {
            row["source_id"]: row for row in self.list_source_object_associations(object_id)
        }
        grouped = {}
        for candidate in retrieval["candidates"]:
            source_id = candidate["source_id"]
            item = grouped.setdefault(
                source_id,
                {
                    "source_id": source_id,
                    "source_label": candidate["context"].get("source_label"),
                    "association": existing.get(source_id),
                    "evidence_count": 0,
                    "top_retrieval_score": candidate["retrieval_score"],
                    "reason_channels": [],
                    "sample_evidence_ids": [],
                },
            )
            item["evidence_count"] += 1
            item["top_retrieval_score"] = max(
                item["top_retrieval_score"], candidate["retrieval_score"]
            )
            for reason in candidate["reasons"]:
                channel = reason["channel"]
                if channel not in item["reason_channels"]:
                    item["reason_channels"].append(channel)
            if len(item["sample_evidence_ids"]) < 3:
                item["sample_evidence_ids"].append(candidate["evidence_id"])
        suggestions = sorted(
            grouped.values(),
            key=lambda item: (-item["top_retrieval_score"], item["source_id"]),
        )
        return {
            "object_id": retrieval["object_id"],
            "name": retrieval["name"],
            "semantic": retrieval["semantic"],
            "suggestion_count": len(suggestions),
            "suggestions": suggestions,
            "note": "Suggestions are read-only until an operator sets an association.",
        }
