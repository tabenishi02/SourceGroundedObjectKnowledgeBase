"""Isolated deterministic N-05 fixture and the normal canonical processing path."""

from __future__ import annotations

import copy
import hashlib
import json
import sqlite3
import time
import traceback
from dataclasses import asdict, is_dataclass
from enum import Enum
from pathlib import Path

from sgokb.application_maintenance import DerivedSearchMaintenanceApplication
from sgokb.exchange import (
    ObjectEvidencePackageBuilder,
    ObjectVersionImportService,
    PackageTransferService,
    ResultReceiptService,
    ResultValidationService,
)
from sgokb.rendering.markdown import MarkdownRenderService
from sgokb.repository import Repository
from sgokb.review.diff import DiffReviewService
from sgokb.storage import PackageExchangeAuditRepository

SEGMENTS = (
    "package_build",
    "package_stage",
    "package_preflight",
    "result_validation",
    "diff_review",
    "result_import",
    "derived_incremental_sync",
    "render",
)


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)

    def encode(item):
        if isinstance(item, Enum):
            return item.value
        if is_dataclass(item):
            return asdict(item)
        if isinstance(item, Path):
            return str(item)
        raise TypeError(type(item).__name__)

    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False, default=encode) + "\n", encoding="utf-8"
    )


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def readings(index):
    return [f"Reading {index:04d}-{part} is {index * 4 + part}." for part in range(4)]


def fixture_counts(repo):
    return {
        "source_count": repo.one("SELECT count(*) AS n FROM source_records")["n"],
        "candidate_evidence_count": repo.one("SELECT count(*) AS n FROM evidence_records")["n"],
        "object_count": repo.one("SELECT count(*) AS n FROM objects")["n"],
        "version_count": repo.one("SELECT count(*) AS n FROM object_versions")["n"],
        "embedding_count": repo.one("SELECT count(*) AS n FROM search_representation_embeddings")[
            "n"
        ],
        "membership_count": repo.one(
            "SELECT count(*) AS n FROM knowledge_search_representation_memberships"
        )["n"],
    }


def prepare_fixture(directory, profile, target):
    """Use canonical Source/Object/Evidence APIs; never write canonical rows with SQL."""
    directory.mkdir(parents=True, exist_ok=False)
    repo = Repository(directory / "starting.sqlite")
    evidence_facts = {}
    try:
        object_id = repo.object_store.create_object(
            "N05 Subject",
            repo.object_store.class_by_key("character").class_id,
            object_id=f"object-n05-{profile}",
        )
        store = repo.source_store
        source_count, candidate_count = target["source_count"], target["candidate_evidence_count"]
        if candidate_count % source_count:
            raise ValueError("Deterministic fixture requires equal candidates per Source")
        per_source = candidate_count // source_count
        for source_index in range(source_count):
            source = store.create_source(
                f"N05 Source {source_index:02d}",
                source_id=f"source-n05-{profile}-{source_index:02d}",
            )
            locator = store.ensure_locator(
                source, "url", f"https://example.invalid/n05/{profile}/{source_index:02d}"
            )
            snapshot = store.create_snapshot(
                source,
                "2026-10-22T00:00:00Z",
                "synthetic_fixture",
                observed_locator_id=locator,
                snapshot_id=f"snapshot-n05-{profile}-{source_index:02d}",
            )
            source_facts = [readings(source_index * per_source + i) for i in range(per_source)]
            html = (
                "<html><body><main>"
                + "".join("<p>N05 Subject: " + " ".join(facts) + "</p>" for facts in source_facts)
                + "</main></body></html>"
            )
            raw = directory / "raw" / f"source-{source_index:02d}.html"
            raw.parent.mkdir(exist_ok=True)
            raw.write_bytes(html.encode("utf-8"))
            artifact = store.add_raw_artifact(
                snapshot,
                "rendered_dom",
                f"fixture/{profile}/raw/{raw.name}",
                sha(raw),
                raw.stat().st_size,
            )
            normalization = store.create_normalization_run(
                snapshot,
                "n05-deterministic-synthetic",
                "1",
                [artifact],
                configuration={"network": False, "synthetic": True},
                run_id=f"run-n05-{profile}-{source_index:02d}",
            )
            for ordinal, facts in enumerate(source_facts):
                index = source_index * per_source + ordinal
                eid = store.add_evidence(
                    normalization,
                    "N05 Subject: " + " ".join(facts),
                    "normalized",
                    ordinal=ordinal,
                    language="en",
                    evidence_id=f"evidence-n05-{profile}-{index:04d}",
                )
                store.add_evidence_location(
                    eid, "dom_path", {"selector": f"p:nth-of-type({ordinal + 1})"}
                )
                evidence_facts[eid] = facts
            store.select_effective_snapshot(
                source, snapshot, reason="isolated N-05 synthetic fixture"
            )
            store.select_effective_run(
                snapshot, normalization, reason="isolated N-05 synthetic fixture"
            )
            store.associate_object(
                source, object_id, "confirmed", subject_relationship="primary_subject"
            )
        counts = fixture_counts(repo)
        assert (
            counts["source_count"] == source_count
            and counts["candidate_evidence_count"] == candidate_count
        )
        assert (
            counts["object_count"] == 1
            and counts["version_count"]
            == counts["embedding_count"]
            == counts["membership_count"]
            == 0
        )
        facets = repo.semantic_store.facets_for_classes(
            (repo.object_store.class_by_key("character").class_id,)
        )
        template = {
            "schema_version": "sgokb.object-result/1.0",
            "result_status": "complete",
            "target": None,
            "binding": None,
            "generation": None,
            "knowledge": {
                "default_language": "en",
                "summary": [],
                "facets": [
                    {"facet_id": f.facet_id, "status": "not_analyzed", "statements": []}
                    for f in facets
                ],
                "attributes": [],
                "relations": [],
            },
            "conflicts": [],
            "gaps": [],
            "unresolved_references": [],
            "registry_proposals": [],
            "class_extensions": [],
        }
        write(directory / "result-template.json", template)
        write(directory / "evidence-facts.json", evidence_facts)
    finally:
        repo.close()
    description = {
        "profile": profile,
        "object_id": object_id,
        "workload": target,
        "actual_start_counts": counts,
        "database_sha256": sha(directory / "starting.sqlite"),
        "semantic_package_retrieval": False,
        "package_retrieval": "default Evidence retrieval; optional semantic reranking disabled",
        "fixture_authority": "canonical store APIs; no direct SQL inserts or network capture",
        "statement_policy": "fixed explicit readings from included Evidence; no generated facts",
        "initial_version": None,
    }
    write(directory / "fixture.json", description)
    return description


def clone_fixture(fixture, sample):
    sample.mkdir(parents=True, exist_ok=False)
    source = sqlite3.connect(
        (fixture / "starting.sqlite").resolve().as_uri() + "?mode=ro", uri=True
    )
    destination = sqlite3.connect(sample / "sgokb.sqlite")
    try:
        source.backup(destination)
        assert destination.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    finally:
        destination.close()
        source.close()


def prebuilt_result(fixture, manifest, statement_count):
    template = copy.deepcopy(read(fixture / "result-template.json"))
    evidence_facts = read(fixture / "evidence-facts.json")
    target = manifest["target"]
    template["schema_version"] = manifest["binding"]["expected_result_schema_version"]
    template["target"] = {
        key: target[key] for key in ("object_id", "primary_class_id", "additional_class_ids")
    }
    template["binding"] = {
        "package_id": manifest["package_id"],
        "package_schema_version": manifest["schema_version"],
        "manifest_sha256": manifest["integrity"]["manifest_sha256"],
        "package_created_at": manifest["created_at"],
        "base_version_id": manifest["binding"]["base_version_id"],
    }
    template["generation"] = {
        "instructions_version": manifest["binding"]["instructions_version"],
        "generator_kind": "tool",
        "application": "N05 deterministic prebuilt Result fixture",
        "generated_at": "2026-10-22T00:00:00Z",
    }
    statements = []
    for eid in manifest["evidence"]["included_evidence_ids"]:
        for text in evidence_facts[eid]:
            statements.append(
                {
                    "local_key": f"reading-{len(statements):04d}",
                    "text": text,
                    "derivation_kind": "direct_statement",
                    "evidence": [{"evidence_id": eid, "role": "supports"}],
                }
            )
            if len(statements) == statement_count:
                template["knowledge"]["summary"] = statements[:5]
                facets = template["knowledge"]["facets"][:3]
                if not facets:
                    raise ValueError("Fixture requires canonical Facet profiles")
                for index, statement in enumerate(statements[5:]):
                    facet = facets[index % len(facets)]
                    facet["status"] = "content"
                    facet["statements"].append(statement)
                return template
    raise ValueError("Included synthetic Evidence cannot supply the required valid Statements")


class SegmentClock:
    def __init__(self):
        self.seconds = {}
        self.events = []

    def measure(self, name, operation):
        if name not in SEGMENTS or name in self.seconds:
            raise ValueError("Unexpected or repeated timed segment")
        started = time.perf_counter_ns()
        status = "PASS"
        try:
            return operation()
        except BaseException:
            status = "FAIL"
            raise
        finally:
            ended = time.perf_counter_ns()
            self.seconds[name] = (ended - started) / 1e9
            self.events.append(
                {"segment": name, "start_ns": started, "end_ns": ended, "status": status}
            )


def run_sample(fixture, sample, sample_id, provider_factory, vector_factory, *, warm_provider=None):
    """Service calls and artifact materialization timed; external-boundary work untimed."""
    description = read(fixture / "fixture.json")
    target = description["workload"]
    clone_fixture(fixture, sample)
    repo = Repository(sample / "sgokb.sqlite")
    clock = SegmentClock()
    record = {
        "sample_id": sample_id,
        "status": "ABORTED",
        "retry_count": 0,
        "segments": {},
        "total_seconds": 0.0,
    }
    vector = None
    try:
        assert fixture_counts(repo) == description["actual_start_counts"]
        object_id = description["object_id"]
        transfer = PackageTransferService()
        audit = PackageExchangeAuditRepository(repo.db)

        def build():
            built = ObjectEvidencePackageBuilder(repo).build(
                object_id,
                build_root=sample / "build",
                max_items=target["package_evidence_count"],
                max_candidates=target["candidate_evidence_count"],
                max_bytes=2_000_000,
                max_estimated_tokens=500_000,
                semantic=False,
                knowledge_language="en",
            )
            write(sample / "package-build.json", built.to_dict())
            return built

        built = clock.measure("package_build", build)
        assert built.evidence_count == target["package_evidence_count"]

        def stage():
            staged = transfer.stage_from_directory(built.path, sample / "staging")
            manifest = read(Path(staged.path) / "manifest.json")
            audit.record_staged(manifest, staged.path, staged.preflight.to_dict())
            write(sample / "package-stage.json", staged.to_dict())
            return staged, manifest

        staged, manifest = clock.measure("package_stage", stage)

        def preflight():
            result = transfer.preflight(staged.path, sample / "external-boundary")
            write(sample / "package-preflight.json", result.to_dict())
            if result.disposition == "blocked":
                raise RuntimeError("Package preflight blocked")
            return result

        clock.measure("package_preflight", preflight)

        # Explicitly excluded: local simulation of export and Result return transport.
        external_start = time.perf_counter_ns()
        exported = transfer.export(
            staged.path, sample / "external-boundary", acknowledge_review=True
        )
        audit.record_export(
            exported.package_id,
            exported.manifest_sha256,
            exported.destination_root,
            exported.path,
            acknowledged_review=True,
            already_present=exported.already_present,
        )
        result = prebuilt_result(fixture, manifest, target["knowledge_statement_count"])
        result_path = sample / "external-result" / "result.json"
        write(result_path, result)
        incoming = sample / "incoming"
        receipt = ResultReceiptService(audit).receive(result_path, manifest["package_id"], incoming)
        write(
            sample / "excluded-boundary.json",
            {
                "start_ns": external_start,
                "end_ns": time.perf_counter_ns(),
                "meaning": "untimed local export and prebuilt Result receipt; no external AI",
                "receipt": receipt.to_dict(),
            },
        )

        def validate():
            validation = ResultValidationService(repo, audit).validate_receipt(
                receipt.receipt_id, incoming_root=incoming
            )
            write(sample / "result-validation.json", validation.to_dict())
            if not validation.is_valid:
                raise RuntimeError("Prebuilt Result failed normal validation")

        clock.measure("result_validation", validate)

        def review():
            reviewed = DiffReviewService(repo, audit).review_result(
                receipt.receipt_id, incoming_root=incoming
            )
            write(sample / "diff-review.json", reviewed.to_dict())
            if reviewed.blocked:
                raise RuntimeError("Normal Diff/Review blocked")

        clock.measure("diff_review", review)

        def import_result():
            imported = ObjectVersionImportService(repo, audit).import_receipt(
                receipt.receipt_id, incoming_root=incoming, acknowledge_review=True
            )
            write(sample / "result-import.json", imported.to_dict())
            return imported

        imported = clock.measure("result_import", import_result)

        def sync():
            nonlocal vector
            provider = warm_provider if warm_provider is not None else provider_factory()
            write(sample / "embedding-space.json", provider.space)
            vector = vector_factory(provider.space)
            app = DerivedSearchMaintenanceApplication(
                repo,
                embedding_provider=provider,
                vector_index=vector,
                embedding_space=provider.space,
            )
            values = {
                "search_representation": app.sync_search_representation(object_id),
                "embedding": app.sync_embedding(object_id),
                "vector_index": app.sync_vector_index(object_id),
            }
            write(sample / "derived-incremental-sync.json", values)

        clock.measure("derived_incremental_sync", sync)

        def render():
            rendered = MarkdownRenderService(repo).render_version(
                imported.version_id, output_root=sample / "rendered"
            )
            write(sample / "render.json", rendered.to_dict())

        clock.measure("render", render)
        count = repo.one(
            "SELECT count(*) AS n FROM knowledge_statements WHERE version_id=?",
            (imported.version_id,),
        )["n"]
        if count != target["knowledge_statement_count"]:
            raise RuntimeError("Imported Statement workload count mismatch")
        record.update(
            status="PASS",
            actual_workload={
                **target,
                "package_evidence_count": built.evidence_count,
                "knowledge_statement_count": count,
            },
            version_id=imported.version_id,
        )
    except BaseException as exc:
        record.update(
            status="ABORTED" if isinstance(exc, (KeyboardInterrupt, SystemExit)) else "FAIL",
            error_type=type(exc).__name__,
        )
        write(
            sample / "execution-error.json",
            {
                "traceback": traceback.format_exc(),
                "unexecuted_segments": [s for s in SEGMENTS if s not in clock.seconds],
                "missing_timings_are_not_estimated": True,
            },
        )
    finally:
        record.update(
            segments=clock.seconds,
            total_seconds=sum(clock.seconds.values()),
            segment_events=clock.events,
        )
        write(sample / "sample.json", record)
        repo.close()
        if vector is not None and hasattr(vector, "_client"):
            vector._client.close()
    return record
