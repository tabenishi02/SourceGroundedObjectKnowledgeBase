import copy
import re

from sgokb.exchange import (
    MANIFEST_CANONICALIZATION,
    PACKAGE_SCHEMA_ID,
    PACKAGE_SCHEMA_VERSION,
    calculate_manifest_sha256,
    load_package_manifest_schema,
    new_package_id,
    validate_package_manifest,
    with_manifest_sha256,
)


def _manifest(*, update=False):
    files = [
        {
            "path": "instructions.md",
            "role": "instructions",
            "media_type": "text/markdown",
            "size_bytes": 100,
            "sha256": "a" * 64,
        },
        {
            "path": "schema/object-result-v1.schema.json",
            "role": "result_schema",
            "media_type": "application/json",
            "size_bytes": 100,
            "sha256": "b" * 64,
        },
        {
            "path": "evidence/source_001.md",
            "role": "evidence",
            "media_type": "text/markdown",
            "size_bytes": 100,
            "sha256": "c" * 64,
        },
    ]
    if update:
        files.insert(
            2,
            {
                "path": "current_object.json",
                "role": "current_object",
                "media_type": "application/json",
                "size_bytes": 100,
                "sha256": "d" * 64,
            },
        )
    manifest = {
        "schema_version": PACKAGE_SCHEMA_VERSION,
        "package_id": "pkg_123e4567-e89b-42d3-a456-426614174000",
        "created_at": "2026-10-13T00:00:00Z",
        "extracted_at": "2026-10-13T00:00:00Z",
        "target": {
            "object_id": "object-1",
            "primary_class_id": "class:character",
            "additional_class_ids": [],
            "name": "Character A",
            "aliases": ["Alias A"],
        },
        "binding": {
            "base_version_id": "version-1" if update else None,
            "expected_result_schema_version": "sgokb.object-result/1.0",
            "instructions_version": "sgokb.object-analysis/1.0",
        },
        "artifacts": {
            "instructions_path": "instructions.md",
            "result_schema_path": "schema/object-result-v1.schema.json",
            "current_object_path": "current_object.json" if update else None,
        },
        "evidence": {
            "included_source_ids": ["source-1"],
            "included_evidence_ids": ["evidence-1"],
            "source_generations": [
                {
                    "source_id": "source-1",
                    "snapshot_id": "snapshot-1",
                    "normalization_run_id": "run-1",
                    "file_path": "evidence/source_001.md",
                    "evidence_ids": ["evidence-1"],
                }
            ],
            "items": [
                {
                    "evidence_id": "evidence-1",
                    "source_id": "source-1",
                    "snapshot_id": "snapshot-1",
                    "normalization_run_id": "run-1",
                    "file_path": "evidence/source_001.md",
                    "selected_by": "relevance_fill",
                    "package_roles": ["retrieved"],
                    "retrieval_reasons": ["lexical"],
                    "related_selected_evidence_ids": [],
                }
            ],
        },
        "selection": {
            "token_estimator": "ascii_div4_plus_non_ascii_v1",
            "budget": {
                "max_estimated_tokens": 12000,
                "max_bytes": 65536,
                "max_items": 64,
            },
            "usage": {
                "estimated_tokens": 100,
                "bytes": 1000,
                "items": 1,
                "sources": 1,
            },
            "candidate_count": 1,
            "selected_count": 1,
            "omitted_count": 0,
        },
        "files": files,
        "warnings": [],
        "export_preflight": {
            "disposition": "allow",
            "reasons": [],
            "credential_material_included": False,
        },
        "integrity": {
            "hash_algorithm": "sha256",
            "canonicalization": MANIFEST_CANONICALIZATION,
            "manifest_sha256": "0" * 64,
        },
    }
    return with_manifest_sha256(manifest)


def test_manifest_schema_is_canonical_draft_2020_12_contract():
    schema = load_package_manifest_schema()
    assert schema["$id"] == PACKAGE_SCHEMA_ID
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["properties"]["schema_version"]["const"] == PACKAGE_SCHEMA_VERSION


def test_initial_and_update_manifests_are_valid():
    assert validate_package_manifest(_manifest()) == ()
    assert validate_package_manifest(_manifest(update=True)) == ()


def test_package_id_is_uuid4_based_and_path_independent():
    value = new_package_id()
    assert re.fullmatch(
        r"pkg_[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}",
        value,
    )


def test_manifest_hash_excludes_only_its_own_digest_field():
    manifest = _manifest()
    original = manifest["integrity"]["manifest_sha256"]
    assert original == calculate_manifest_sha256(manifest)

    changed_digest = copy.deepcopy(manifest)
    changed_digest["integrity"]["manifest_sha256"] = "f" * 64
    assert calculate_manifest_sha256(changed_digest) == original

    changed_payload = copy.deepcopy(manifest)
    changed_payload["target"]["name"] = "Changed"
    assert calculate_manifest_sha256(changed_payload) != original


def test_update_package_requires_current_object_and_initial_package_forbids_it():
    update = _manifest(update=True)
    update["artifacts"]["current_object_path"] = None
    update = with_manifest_sha256(update)
    assert any("current_object.json" in issue for issue in validate_package_manifest(update))

    initial = _manifest()
    initial["artifacts"]["current_object_path"] = "current_object.json"
    initial["files"].append(
        {
            "path": "current_object.json",
            "role": "current_object",
            "media_type": "application/json",
            "size_bytes": 100,
            "sha256": "d" * 64,
        }
    )
    initial = with_manifest_sha256(initial)
    assert any("initial Package" in issue for issue in validate_package_manifest(initial))


def test_package_membership_must_exactly_match_evidence_items_and_generation_mapping():
    manifest = _manifest()
    manifest["evidence"]["included_evidence_ids"] = ["invented-evidence"]
    manifest = with_manifest_sha256(manifest)
    assert any("included_evidence_ids" in issue for issue in validate_package_manifest(manifest))

    manifest = _manifest()
    manifest["evidence"]["source_generations"][0]["snapshot_id"] = "other-snapshot"
    manifest = with_manifest_sha256(manifest)
    assert any(
        "source_generation mapping mismatch" in issue
        for issue in validate_package_manifest(manifest)
    )


def test_carry_forward_and_manual_include_are_protected():
    manifest = _manifest(update=True)
    item = manifest["evidence"]["items"][0]
    item["package_roles"] = ["carry_forward", "retrieved"]
    item["selected_by"] = "relevance_fill"
    manifest = with_manifest_sha256(manifest)
    assert any("selected_by=protected" in issue for issue in validate_package_manifest(manifest))


def test_manifest_rejects_unsafe_or_unlisted_evidence_file_paths():
    manifest = _manifest()
    manifest["evidence"]["items"][0]["file_path"] = "../outside.md"
    manifest = with_manifest_sha256(manifest)
    issues = validate_package_manifest(manifest)
    assert any("schema:" in issue or "Evidence file missing" in issue for issue in issues)

    manifest = _manifest()
    manifest["files"][2]["path"] = "..\\outside.md"
    manifest = with_manifest_sha256(manifest)
    assert any(
        "unsafe Package-relative path" in issue for issue in validate_package_manifest(manifest)
    )


def test_selection_counts_and_source_counts_are_cross_checked():
    manifest = _manifest()
    manifest["selection"]["selected_count"] = 2
    manifest["selection"]["usage"]["items"] = 2
    manifest["selection"]["usage"]["sources"] = 2
    manifest = with_manifest_sha256(manifest)
    issues = validate_package_manifest(manifest)
    assert any("selected_count" in issue for issue in issues)
    assert any("usage.items" in issue for issue in issues)
    assert any("usage.sources" in issue for issue in issues)


def test_preflight_review_or_block_requires_reason_and_credentials_cannot_be_included():
    manifest = _manifest()
    manifest["export_preflight"]["disposition"] = "review_required"
    manifest = with_manifest_sha256(manifest)
    assert any("requires reasons" in issue for issue in validate_package_manifest(manifest))

    manifest = _manifest()
    manifest["export_preflight"]["credential_material_included"] = True
    manifest = with_manifest_sha256(manifest)
    assert any("schema:" in issue for issue in validate_package_manifest(manifest))


def test_unknown_manifest_fields_are_rejected():
    manifest = _manifest()
    manifest["export_destination"] = "drive"
    manifest = with_manifest_sha256(manifest)
    assert any("schema:" in issue for issue in validate_package_manifest(manifest))


def test_tampering_is_detected_by_manifest_digest():
    manifest = _manifest()
    manifest["files"][0]["sha256"] = "e" * 64
    issues = validate_package_manifest(manifest)
    assert any("manifest_sha256 mismatch" in issue for issue in issues)
