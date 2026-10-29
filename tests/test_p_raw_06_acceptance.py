import hashlib
import json
import shutil
from pathlib import Path

import pytest

from sgokb.application_exchange import (
    PackageExchangeApplication,
    ResultExchangeApplication,
)
from sgokb.application_version import VersionReadApplication
from sgokb.exchange.package_manifest_v2 import validate_package_manifest_v2
from sgokb.exchange.package_transfer_v2 import inspect_package_v2
from sgokb.exchange.raw_grounding import EvidenceRawResolver
from sgokb.repository import Repository


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _setup_raw_object(
    repository,
    tmp_path,
    *,
    two_artifacts: bool = False,
    two_evidence: bool = False,
):
    object_id = repository.object_store.create_object(
        "孫悟空 RAW acceptance",
        "class:character",
        object_id="object-praw06-goku",
    )
    source_id = repository.source_store.create_source(
        "孫悟空 RAW acceptance source",
        source_id="source-praw06-goku",
    )
    locator = repository.source_store.ensure_locator(
        source_id,
        "url",
        "https://example.test/praw06-goku",
    )
    snapshot_id = "snapshot-praw06-goku"
    repository.source_store.create_snapshot(
        source_id,
        "2026-10-30T09:00:00Z",
        "test_fixture",
        observed_locator_id=locator,
        title="孫悟空 RAW acceptance source",
        snapshot_id=snapshot_id,
    )

    raw = (
        "<html><body>孫悟空はドラゴンボールの主人公として描かれる"
        "架空のキャラクターである。</body></html>"
    ).encode("utf-8")
    artifact_ids = []
    raw_paths = []
    artifact_count = 2 if two_artifacts else 1
    for index in range(artifact_count):
        raw_path = tmp_path / f"goku-raw-{index + 1}.html"
        raw_path.write_bytes(raw)
        artifact_kind = "rendered_dom" if index == 0 else f"source_html_{index + 1}"
        artifact_id = repository.source_store.add_raw_artifact(
            snapshot_id,
            artifact_kind,
            str(raw_path),
            _sha256(raw),
            len(raw),
            media_type="text/html",
            artifact_id=f"raw-praw06-goku-{index + 1}",
        )
        artifact_ids.append(artifact_id)
        raw_paths.append(raw_path)

    run_id = "run-praw06-goku"
    repository.source_store.create_normalization_run(
        snapshot_id,
        "fixture",
        "1",
        artifact_ids,
        run_id=run_id,
    )
    evidence_ids = []
    evidence_count = 2 if two_evidence else 1
    for index in range(evidence_count):
        evidence_id = f"evidence-praw06-goku-{index + 1}"
        repository.source_store.add_evidence(
            run_id,
            f"孫悟空 acceptance Evidence {index + 1}",
            "normalized",
            evidence_id=evidence_id,
        )
        evidence_ids.append(evidence_id)

    repository.source_store.select_effective_snapshot(
        source_id,
        snapshot_id,
        reason="P-RAW-06 acceptance fixture",
    )
    repository.source_store.select_effective_run(
        snapshot_id,
        run_id,
        reason="P-RAW-06 acceptance fixture",
    )
    repository.source_store.associate_object(
        source_id,
        object_id,
        "confirmed",
        subject_relationship="primary_subject",
    )
    return {
        "object_id": object_id,
        "source_id": source_id,
        "snapshot_id": snapshot_id,
        "run_id": run_id,
        "artifact_ids": tuple(artifact_ids),
        "evidence_ids": tuple(evidence_ids),
        "raw": raw,
        "raw_paths": tuple(raw_paths),
    }


def _read_manifest(path: str | Path) -> dict:
    return json.loads(Path(path, "manifest.json").read_text(encoding="utf-8"))


def _build_stage_export(
    repository,
    tmp_path,
    object_id,
    *,
    package_version="v2",
    include_evidence=(),
    suffix="v2",
):
    packages = PackageExchangeApplication(repository)
    built = packages.build(
        object_id,
        package_version=package_version,
        build_root=tmp_path / f"build-{suffix}",
        include_evidence=include_evidence,
    )
    manifest = _read_manifest(built.path)
    staged = packages.stage(
        built.path,
        staging_root=tmp_path / f"staging-{suffix}",
    )
    exported = packages.export(
        staged.path,
        destination=tmp_path / f"export-{suffix}",
    )
    return packages, built, manifest, staged, exported


def _facets(repository, manifest):
    target = manifest["target"]
    return repository.semantic_store.facets_for_classes(
        (target["primary_class_id"], *target["additional_class_ids"])
    )


def _valid_v1_result(repository, manifest):
    target = manifest["target"]
    evidence_id = manifest["evidence"]["included_evidence_ids"][0]
    return {
        "schema_version": "sgokb.object-result/1.0",
        "result_status": "complete",
        "target": {
            "object_id": target["object_id"],
            "primary_class_id": target["primary_class_id"],
            "additional_class_ids": target["additional_class_ids"],
        },
        "binding": {
            "package_id": manifest["package_id"],
            "package_schema_version": manifest["schema_version"],
            "manifest_sha256": manifest["integrity"]["manifest_sha256"],
            "package_created_at": manifest["created_at"],
            "base_version_id": manifest["binding"]["base_version_id"],
        },
        "generation": {
            "instructions_version": manifest["binding"]["instructions_version"],
            "generator_kind": "interactive_ai",
            "application": "ChatGPT",
            "generated_at": "2026-10-30T09:05:00Z",
        },
        "knowledge": {
            "default_language": "ja",
            "summary": [
                {
                    "local_key": "summary-1",
                    "text": "孫悟空は架空のキャラクターである。",
                    "derivation_kind": "direct_statement",
                    "evidence": [
                        {"evidence_id": evidence_id, "role": "supports"}
                    ],
                }
            ],
            "facets": [
                {
                    "facet_id": facet.facet_id,
                    "status": "not_analyzed",
                    "statements": [],
                }
                for facet in _facets(repository, manifest)
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


def _valid_v2_result(repository, manifest, *, raw_id=None, locator=None):
    target = manifest["target"]
    if raw_id is None:
        raw_id = manifest["raw_grounding"]["included_raw_artifact_ids"][0]
    grounding = {"raw_artifact_id": raw_id, "role": "supports"}
    if locator is not None:
        grounding["locator"] = locator
    return {
        "schema_version": "sgokb.object-result/2.0",
        "result_status": "complete",
        "target": {
            "object_id": target["object_id"],
            "primary_class_id": target["primary_class_id"],
            "additional_class_ids": target["additional_class_ids"],
        },
        "binding": {
            "package_id": manifest["package_id"],
            "package_schema_version": manifest["schema_version"],
            "manifest_sha256": manifest["integrity"]["manifest_sha256"],
            "package_created_at": manifest["created_at"],
            "base_version_id": manifest["binding"]["base_version_id"],
            "grounding_contract": manifest["binding"]["grounding_contract"],
            "grounding_set_sha256": manifest["raw_grounding"]["integrity"][
                "grounding_set_sha256"
            ],
        },
        "generation": {
            "instructions_version": manifest["binding"]["instructions_version"],
            "generator_kind": "interactive_ai",
            "application": "ChatGPT",
            "generated_at": "2026-10-30T09:10:00Z",
        },
        "knowledge": {
            "default_language": "ja",
            "summary": [
                {
                    "local_key": "summary-1",
                    "text": "孫悟空は架空のキャラクターである。",
                    "derivation_kind": "direct_statement",
                    "grounding": [grounding],
                }
            ],
            "facets": [
                {
                    "facet_id": facet.facet_id,
                    "status": "not_analyzed",
                    "statements": [],
                }
                for facet in _facets(repository, manifest)
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


def _write_result(tmp_path, result, *, suffix):
    result_dir = tmp_path / f"result-{suffix}"
    result_dir.mkdir()
    result_path = result_dir / "result.json"
    result_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return result_path


def _receive_validate_import(repository, tmp_path, manifest, result, *, suffix):
    result_path = _write_result(tmp_path, result, suffix=suffix)
    incoming = tmp_path / f"incoming-{suffix}"
    results = ResultExchangeApplication(repository)
    receipt = results.receive(
        result_path,
        package_id=manifest["package_id"],
        incoming_root=incoming,
    )
    report = results.validate(receipt.receipt_id, incoming_root=incoming)
    assert report.validation_state == "valid"
    review = results.review(receipt.receipt_id, incoming_root=incoming)
    assert not review.blocked
    imported = results.import_result(
        receipt.receipt_id,
        incoming_root=incoming,
        acknowledge_review=review.requires_review,
    )
    return receipt, report, review, imported


def test_raw_resolution_is_deterministic_and_preserves_distinct_same_hash_ids(tmp_path):
    repository = Repository(tmp_path / "sgokb.sqlite")
    try:
        fixture = _setup_raw_object(
            repository,
            tmp_path,
            two_artifacts=True,
            two_evidence=True,
        )
        evidence_1, evidence_2 = fixture["evidence_ids"]
        first = EvidenceRawResolver(repository).resolve(
            (evidence_2, evidence_1, evidence_2)
        )
        second = EvidenceRawResolver(repository).resolve((evidence_1, evidence_2))

        expected_ids = tuple(sorted(fixture["artifact_ids"]))
        assert first.included_raw_artifact_ids == expected_ids
        assert second.included_raw_artifact_ids == expected_ids
        assert len(first.artifacts) == 2
        assert len({item.sha256 for item in first.artifacts}) == 1
        assert {item.raw_artifact_id for item in first.artifacts} == set(expected_ids)
        assert all(binding.raw_artifact_ids == expected_ids for binding in first.bindings)
        assert {binding.evidence_id for binding in first.bindings} == {
            evidence_1,
            evidence_2,
        }
    finally:
        repository.close()


def test_missing_or_modified_raw_bytes_fail_closed(tmp_path):
    repository = Repository(tmp_path / "sgokb.sqlite")
    try:
        fixture = _setup_raw_object(repository, tmp_path)
        evidence_ids = fixture["evidence_ids"]
        raw_path = fixture["raw_paths"][0]
        raw = fixture["raw"]

        assert EvidenceRawResolver(repository).resolve(evidence_ids).artifacts

        raw_path.unlink()
        with pytest.raises(ValueError, match="physical bytes cannot be resolved"):
            EvidenceRawResolver(repository).resolve(evidence_ids)

        raw_path.write_bytes(raw)
        assert EvidenceRawResolver(repository).resolve(evidence_ids).artifacts

        raw_path.write_bytes(b"X" * len(raw))
        with pytest.raises(ValueError, match="physical bytes cannot be resolved"):
            EvidenceRawResolver(repository).resolve(evidence_ids)
    finally:
        repository.close()


def test_package_v2_integrity_preflight_and_egress_are_fail_closed(tmp_path):
    repository = Repository(tmp_path / "sgokb.sqlite")
    try:
        fixture = _setup_raw_object(repository, tmp_path)
        packages, built, manifest, staged, exported = _build_stage_export(
            repository,
            tmp_path,
            fixture["object_id"],
            include_evidence=fixture["evidence_ids"],
            suffix="integrity",
        )

        assert validate_package_manifest_v2(manifest) == ()
        assert staged.preflight.disposition == "allow"
        assert Path(exported["path"]).is_dir()
        assert packages.preflight(
            staged.path,
            destination=tmp_path / "external-safe",
        ).disposition == "allow"

        unsafe = packages.preflight(
            staged.path,
            destination=Path(staged.path) / "nested-destination",
        )
        assert unsafe.disposition == "blocked"
        assert "destination_must_not_be_inside_package" in unsafe.reasons

        manifest_tamper = tmp_path / "manifest-tamper"
        shutil.copytree(staged.path, manifest_tamper)
        tampered_manifest = _read_manifest(manifest_tamper)
        tampered_manifest["target"]["name"] = "tampered"
        Path(manifest_tamper, "manifest.json").write_text(
            json.dumps(tampered_manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        manifest_check = inspect_package_v2(manifest_tamper)
        assert manifest_check.disposition == "blocked"
        assert any(
            reason.startswith("manifest_invalid:")
            for reason in manifest_check.reasons
        )

        raw_tamper = tmp_path / "raw-tamper"
        shutil.copytree(staged.path, raw_tamper)
        raw_item = manifest["raw_grounding"]["artifacts"][0]
        Path(raw_tamper, raw_item["package_path"]).write_bytes(b"tampered raw")
        raw_check = inspect_package_v2(raw_tamper)
        assert raw_check.disposition == "blocked"
        assert any("sha256_mismatch:" in reason for reason in raw_check.reasons)

        extra_file = tmp_path / "extra-file"
        shutil.copytree(staged.path, extra_file)
        Path(extra_file, "unexpected.txt").write_text("unexpected", encoding="utf-8")
        extra_check = inspect_package_v2(extra_file)
        assert extra_check.disposition == "blocked"
        assert "unexpected_file:unexpected.txt" in extra_check.reasons
        assert Path(built.path, "evidence").exists() is False
    finally:
        repository.close()


def test_result_v2_membership_and_grounding_set_binding_are_enforced(tmp_path):
    repository = Repository(tmp_path / "sgokb.sqlite")
    try:
        fixture = _setup_raw_object(repository, tmp_path)
        _, _, manifest, _, _ = _build_stage_export(
            repository,
            tmp_path,
            fixture["object_id"],
            include_evidence=fixture["evidence_ids"],
            suffix="membership",
        )
        results = ResultExchangeApplication(repository)
        incoming = tmp_path / "incoming-membership"

        outside = _valid_v2_result(
            repository,
            manifest,
            raw_id="raw-not-in-package",
        )
        outside_path = _write_result(tmp_path, outside, suffix="outside")
        outside_receipt = results.receive(
            outside_path,
            package_id=manifest["package_id"],
            incoming_root=incoming,
        )
        outside_report = results.validate(
            outside_receipt.receipt_id,
            incoming_root=incoming,
        )
        assert outside_report.validation_state == "invalid"
        assert "raw_artifact_outside_package" in {
            item.code for item in outside_report.findings
        }

        mismatched = _valid_v2_result(repository, manifest)
        mismatched["binding"]["grounding_set_sha256"] = "0" * 64
        mismatch_path = _write_result(tmp_path, mismatched, suffix="mismatch")
        mismatch_receipt = results.receive(
            mismatch_path,
            package_id=manifest["package_id"],
            incoming_root=incoming,
        )
        mismatch_report = results.validate(
            mismatch_receipt.receipt_id,
            incoming_root=incoming,
        )
        assert mismatch_report.validation_state == "invalid"
        assert "grounding_set_sha256_mismatch" in {
            item.code for item in mismatch_report.findings
        }
    finally:
        repository.close()


def test_raw_package_external_result_import_end_to_end_uses_only_raw_semantics(tmp_path):
    repository = Repository(tmp_path / "sgokb.sqlite")
    try:
        fixture = _setup_raw_object(repository, tmp_path)
        _, _, manifest, _, exported = _build_stage_export(
            repository,
            tmp_path,
            fixture["object_id"],
            include_evidence=fixture["evidence_ids"],
            suffix="e2e",
        )
        exported_root = Path(exported["path"])

        assert not (exported_root / "evidence").exists()
        raw_item = manifest["raw_grounding"]["artifacts"][0]
        external_raw = (exported_root / raw_item["package_path"]).read_bytes()
        assert external_raw == fixture["raw"]
        assert "孫悟空" in external_raw.decode("utf-8")

        result = _valid_v2_result(
            repository,
            manifest,
            locator={"kind": "text_quote", "exact": "孫悟空"},
        )
        _, _, review, imported = _receive_validate_import(
            repository,
            tmp_path,
            manifest,
            result,
            suffix="e2e",
        )

        assert not review.blocked
        assert repository.version_store.current_version_id(fixture["object_id"]) == (
            imported.version_id
        )
        assert repository.one(
            "SELECT count(*) AS n FROM evidence_links WHERE version_id=?",
            (imported.version_id,),
        )["n"] == 0
        raw_links = repository.rows(
            "SELECT raw_artifact_id,role,locator_json "
            "FROM raw_grounding_links WHERE version_id=?",
            (imported.version_id,),
        )
        assert len(raw_links) == 1
        assert raw_links[0]["raw_artifact_id"] == fixture["artifact_ids"][0]
        assert json.loads(raw_links[0]["locator_json"])["exact"] == "孫悟空"

        shown = VersionReadApplication(repository).show(imported.version_id)
        assert shown["grounding_kind"] == "raw"
        assert shown["knowledge"]["summary"][0]["evidence"] == []
        assert shown["knowledge"]["summary"][0]["grounding"][0][
            "raw_artifact_id"
        ] == fixture["artifact_ids"][0]
    finally:
        repository.close()


def test_v1_to_v2_update_is_supported_and_v2_to_v1_downgrade_is_blocked(tmp_path):
    repository = Repository(tmp_path / "sgokb.sqlite")
    try:
        fixture = _setup_raw_object(repository, tmp_path)
        packages = PackageExchangeApplication(repository)

        default_build = packages.build(
            fixture["object_id"],
            build_root=tmp_path / "default-build",
            include_evidence=fixture["evidence_ids"],
        )
        assert _read_manifest(default_build.path)["schema_version"] == (
            "sgokb.object-evidence-package/1.0"
        )

        _, _, v1_manifest, _, _ = _build_stage_export(
            repository,
            tmp_path,
            fixture["object_id"],
            package_version="v1",
            include_evidence=fixture["evidence_ids"],
            suffix="compat-v1",
        )
        v1_result = _valid_v1_result(repository, v1_manifest)
        _, _, _, v1_import = _receive_validate_import(
            repository,
            tmp_path,
            v1_manifest,
            v1_result,
            suffix="compat-v1",
        )

        _, _, v2_manifest, _, _ = _build_stage_export(
            repository,
            tmp_path,
            fixture["object_id"],
            package_version="v2",
            suffix="compat-v2",
        )
        assert v2_manifest["binding"]["base_version_id"] == v1_import.version_id
        assert fixture["evidence_ids"][0] in v2_manifest["evidence"][
            "included_evidence_ids"
        ]
        v2_result = _valid_v2_result(repository, v2_manifest)
        _, _, _, v2_import = _receive_validate_import(
            repository,
            tmp_path,
            v2_manifest,
            v2_result,
            suffix="compat-v2",
        )
        assert repository.version_store.current_version_id(fixture["object_id"]) == (
            v2_import.version_id
        )

        with pytest.raises(ValueError, match="Legacy Package v1 build is blocked"):
            packages.build(
                fixture["object_id"],
                package_version="v1",
                build_root=tmp_path / "blocked-v1-downgrade",
            )
    finally:
        repository.close()
