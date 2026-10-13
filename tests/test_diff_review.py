import json
from pathlib import Path

import pytest
from test_markdown_renderer import _rich_import
from test_object_version_import import _import, _validate
from test_result_validation import _valid_result

from sgokb.exchange import (
    ObjectEvidencePackageBuilder,
    PackageTransferService,
    ResultValidationService,
)
from sgokb.package_cli import main as package_cli_main
from sgokb.repository import Repository
from sgokb.review import DiffReviewMarkdownRenderer, DiffReviewService


def _next_package(repository, audit, object_id, tmp_path, suffix="next"):
    built = ObjectEvidencePackageBuilder(repository).build(
        object_id,
        build_root=tmp_path / f"build-{suffix}",
        semantic=False,
    )
    transfer = PackageTransferService()
    staged = transfer.stage_from_directory(built.path, tmp_path / f"staging-{suffix}")
    manifest = json.loads(Path(staged.path, "manifest.json").read_text(encoding="utf-8"))
    audit.record_staged(manifest, staged.path, staged.preflight.to_dict())
    exported = transfer.export(staged.path, tmp_path / f"DriveSync-{suffix}")
    audit.record_export(
        exported.package_id,
        exported.manifest_sha256,
        exported.destination_root,
        exported.path,
        acknowledged_review=False,
        already_present=exported.already_present,
    )
    return manifest


def _validated_candidate(repository, audit, manifest, tmp_path, result):
    tmp_path.mkdir(parents=True, exist_ok=True)
    return _validate(repository, audit, manifest, tmp_path, result)


def _reason_codes(report):
    return {item.code for item in report.reasons}


def _destructive_sections(report):
    return {str(item.get("section")) for item in report.diff.destructive_omissions}


def test_initial_complete_result_is_ready_to_import_without_review_reasons(tmp_path):
    repository = Repository(tmp_path / "sgokb.sqlite")
    try:
        from test_result_validation import _build_and_stage

        audit, manifest, object_id, _, _, _ = _build_and_stage(repository, tmp_path)
        result = _valid_result(repository, manifest)
        receipt, incoming, _ = _validated_candidate(
            repository, audit, manifest, tmp_path / "receipt", result
        )

        report = DiffReviewService(repository, audit).review_result(
            receipt.receipt_id,
            incoming_root=incoming,
        )

        assert report.object_id == object_id
        assert report.validation_state == "valid"
        assert report.review_state == "ready_to_import"
        assert report.reasons == ()
        assert report.diff.before_version_id is None
        assert report.diff.after_kind == "result_candidate"
        assert report.diff.destructive_omissions == ()
        assert any(item["change"] == "added" for item in report.diff.changes["summary_statements"])
    finally:
        repository.close()


def test_partial_candidate_highlights_destructive_omissions_and_requires_review(tmp_path):
    repository = Repository(tmp_path / "sgokb.sqlite")
    try:
        audit, first, object_id, _, _ = _rich_import(repository, tmp_path)
        manifest = _next_package(repository, audit, object_id, tmp_path)
        result = _valid_result(repository, manifest)
        result["result_status"] = "partial"
        result["gaps"] = [
            {
                "local_key": "gap-h04",
                "kind": "not_analyzed",
                "description": "The update intentionally did not analyze all prior knowledge.",
                "evidence": [],
            }
        ]
        receipt, incoming, validation = _validated_candidate(
            repository,
            audit,
            manifest,
            tmp_path / "receipt-partial",
            result,
        )
        assert validation.validation_state == "valid"

        report = DiffReviewService(repository, audit).review_result(
            receipt.receipt_id,
            incoming_root=incoming,
        )

        assert report.review_state == "review_required"
        assert report.base_version_id == first.version_id
        assert report.current_version_id == first.version_id
        assert "result_requires_review" in _reason_codes(report)
        assert "destructive_omission" in _reason_codes(report)
        sections = _destructive_sections(report)
        assert "attributes" in sections
        assert "relations" in sections
        assert "facets" in sections
        assert any(section.startswith("facet:") for section in sections)
        assert any(
            item["before_status"] == "content" and item["after_status"] == "not_analyzed"
            for item in report.diff.changes["facets"]
        )

        markdown = DiffReviewMarkdownRenderer().render_review(report)
        assert "# Object Result Review" in markdown
        assert "Review state: **review_required**" in markdown
        assert "### Destructive omissions" in markdown
        assert "destructive_omission" in markdown
        assert "explicit H-02 Import" in markdown
    finally:
        repository.close()


def test_conflict_is_prominent_attention_but_does_not_alone_require_review(tmp_path):
    repository = Repository(tmp_path / "sgokb.sqlite")
    try:
        from test_result_validation import _build_and_stage

        audit, manifest, _, _, evidence_id, _ = _build_and_stage(repository, tmp_path)
        result = _valid_result(repository, manifest)
        result["conflicts"] = [
            {
                "local_key": "conflict-h04",
                "description": "Two source-grounded descriptions remain unresolved.",
                "related_knowledge": [{"kind": "statement", "local_key": "summary-1"}],
                "evidence": [
                    {"evidence_id": evidence_id, "role": "supports"},
                    {"evidence_id": evidence_id, "role": "contradicts"},
                ],
            }
        ]
        receipt, incoming, validation = _validated_candidate(
            repository,
            audit,
            manifest,
            tmp_path / "receipt-conflict",
            result,
        )
        assert validation.validation_state == "valid"

        report = DiffReviewService(repository, audit).review_result(
            receipt.receipt_id,
            incoming_root=incoming,
        )

        assert report.review_state == "ready_to_import"
        reason = next(item for item in report.reasons if item.code == "conflicts_present")
        assert reason.severity == "attention"
        conflict_changes = report.diff.changes["review_metadata"]["conflicts"]
        assert any(item["change"] == "added" for item in conflict_changes)
    finally:
        repository.close()


def test_registry_proposal_and_identity_ambiguity_are_review_reasons(tmp_path):
    repository = Repository(tmp_path / "sgokb.sqlite")
    try:
        from test_result_validation import _build_and_stage

        audit, manifest, _, _, evidence_id, _ = _build_and_stage(repository, tmp_path)
        result = _valid_result(repository, manifest)
        result["registry_proposals"] = [
            {
                "local_key": "proposal-h04",
                "proposal_kind": "object_alias",
                "rationale": "Source suggests another alias.",
                "payload": {"value": "Alice Review Alias"},
                "evidence": [{"evidence_id": evidence_id, "role": "supports"}],
            }
        ]
        result["gaps"] = [
            {
                "local_key": "gap-identity-h04",
                "kind": "identity_ambiguity",
                "description": "A referenced Alice may be a different Object.",
                "evidence": [{"evidence_id": evidence_id, "role": "contextualizes"}],
            }
        ]
        receipt, incoming, _ = _validated_candidate(
            repository,
            audit,
            manifest,
            tmp_path / "receipt-identity",
            result,
        )

        report = DiffReviewService(repository, audit).review_result(
            receipt.receipt_id,
            incoming_root=incoming,
        )

        assert report.review_state == "review_required"
        assert "registry_proposal_requires_review" in _reason_codes(report)
        assert "identity_ambiguity_requires_review" in _reason_codes(report)
        assert any(
            item["change"] == "added"
            for item in report.diff.changes["review_metadata"]["registry_proposals"]
        )
    finally:
        repository.close()


def test_stale_candidate_is_blocked_but_still_shows_base_candidate_diff(tmp_path):
    repository = Repository(tmp_path / "sgokb.sqlite")
    try:
        audit, first, object_id, _, _ = _rich_import(repository, tmp_path)
        manifest = _next_package(repository, audit, object_id, tmp_path, "stale")
        result = _valid_result(repository, manifest)
        result["knowledge"]["summary"][0]["text"] = "Candidate based on the old current Version."
        receipt, incoming, validation = _validated_candidate(
            repository,
            audit,
            manifest,
            tmp_path / "receipt-stale",
            result,
        )
        assert validation.validation_state == "valid"

        intervening = repository.version_store.begin_candidate(object_id, first.version_id)
        # The acceptance gate permits an empty manually-created snapshot here; this is enough
        # to make the received Result stale without changing its immutable artifact.
        repository.version_store.accept_candidate(intervening)
        forced = ResultValidationService(repository, audit).validate_receipt(
            receipt.receipt_id,
            incoming_root=incoming,
            force=True,
        )
        assert forced.validation_state == "invalid"

        report = DiffReviewService(repository, audit).review_result(
            receipt.receipt_id,
            incoming_root=incoming,
        )

        assert report.review_state == "blocked"
        assert report.base_version_id == first.version_id
        assert report.current_version_id == intervening
        assert "stale_base_version" in _reason_codes(report)
        assert report.diff.before_version_id == first.version_id
        assert any(
            item["change"] == "modified" for item in report.diff.changes["summary_statements"]
        )
    finally:
        repository.close()


def test_review_required_transition_uses_h02_ack_and_becomes_imported(tmp_path):
    repository = Repository(tmp_path / "sgokb.sqlite")
    try:
        audit, first, object_id, _, _ = _rich_import(repository, tmp_path)
        manifest = _next_package(repository, audit, object_id, tmp_path, "ack")
        result = _valid_result(repository, manifest)
        result["result_status"] = "partial"
        result["gaps"] = [
            {
                "local_key": "gap-ack-h04",
                "kind": "not_analyzed",
                "description": "Explicit review is required before current promotion.",
                "evidence": [],
            }
        ]
        receipt, incoming, _ = _validated_candidate(
            repository,
            audit,
            manifest,
            tmp_path / "receipt-ack",
            result,
        )
        review_service = DiffReviewService(repository, audit)
        before = review_service.review_result(receipt.receipt_id, incoming_root=incoming)
        assert before.review_state == "review_required"

        with pytest.raises(ValueError, match="review acknowledgement"):
            _import(repository, audit, receipt, incoming)
        assert repository.version_store.current_version_id(object_id) == first.version_id

        imported = _import(
            repository,
            audit,
            receipt,
            incoming,
            acknowledge_review=True,
        )
        after = review_service.review_result(receipt.receipt_id, incoming_root=incoming)

        assert after.review_state == "imported"
        assert after.imported_version_id == imported.version_id
        assert after.review_acknowledged is True
        assert repository.version_store.current_version_id(object_id) == imported.version_id
    finally:
        repository.close()


def test_removed_conflict_and_registry_proposal_are_destructive_review_items(tmp_path):
    repository = Repository(tmp_path / "sgokb.sqlite")
    try:
        from test_result_validation import _build_and_stage

        audit, manifest, object_id, _, evidence_id, _ = _build_and_stage(repository, tmp_path)
        result = _valid_result(repository, manifest)
        result["conflicts"] = [
            {
                "local_key": "conflict-persisted-h04",
                "description": "An unresolved conflict is retained in the first Version.",
                "related_knowledge": [{"kind": "statement", "local_key": "summary-1"}],
                "evidence": [
                    {"evidence_id": evidence_id, "role": "supports"},
                    {"evidence_id": evidence_id, "role": "contradicts"},
                ],
            }
        ]
        result["registry_proposals"] = [
            {
                "local_key": "proposal-persisted-h04",
                "proposal_kind": "object_alias",
                "rationale": "A Registry proposal must not disappear silently.",
                "payload": {"value": "Alice Proposed Alias"},
                "evidence": [{"evidence_id": evidence_id, "role": "supports"}],
            }
        ]
        receipt1, incoming1, _ = _validated_candidate(
            repository,
            audit,
            manifest,
            tmp_path / "receipt-metadata-v1",
            result,
        )
        first = _import(
            repository,
            audit,
            receipt1,
            incoming1,
            acknowledge_review=True,
        )

        manifest2 = _next_package(repository, audit, object_id, tmp_path, "metadata-v2")
        result2 = _valid_result(repository, manifest2)
        receipt2, incoming2, _ = _validated_candidate(
            repository,
            audit,
            manifest2,
            tmp_path / "receipt-metadata-v2",
            result2,
        )

        report = DiffReviewService(repository, audit).review_result(
            receipt2.receipt_id,
            incoming_root=incoming2,
        )

        assert report.base_version_id == first.version_id
        assert report.review_state == "review_required"
        assert "destructive_omission" in _reason_codes(report)
        sections = _destructive_sections(report)
        assert "conflicts" in sections
        assert "registry_proposals" in sections
        assert any(
            item["change"] == "removed"
            for item in report.diff.changes["review_metadata"]["conflicts"]
        )
        assert any(
            item["change"] == "removed"
            for item in report.diff.changes["review_metadata"]["registry_proposals"]
        )
    finally:
        repository.close()


def test_historical_version_diff_shows_removed_knowledge_after_import(tmp_path):
    repository = Repository(tmp_path / "sgokb.sqlite")
    try:
        audit, first, object_id, _, _ = _rich_import(repository, tmp_path)
        manifest = _next_package(repository, audit, object_id, tmp_path, "historical")
        result = _valid_result(repository, manifest)
        receipt, incoming, _ = _validated_candidate(
            repository,
            audit,
            manifest,
            tmp_path / "receipt-historical",
            result,
        )
        review = DiffReviewService(repository, audit).review_result(
            receipt.receipt_id,
            incoming_root=incoming,
        )
        assert review.review_state == "review_required"
        assert "destructive_omission" in _reason_codes(review)
        with pytest.raises(ValueError, match="review acknowledgement"):
            _import(repository, audit, receipt, incoming)
        second = _import(
            repository,
            audit,
            receipt,
            incoming,
            acknowledge_review=True,
        )

        report = DiffReviewService(repository, audit).diff_versions(
            first.version_id,
            second.version_id,
        )

        assert report.after_kind == "accepted_version"
        assert report.before_version_id == first.version_id
        assert report.after_version_id == second.version_id
        destructive_sections = {str(item.get("section")) for item in report.destructive_omissions}
        assert "attributes" in destructive_sections
        assert "relations" in destructive_sections
        markdown = DiffReviewMarkdownRenderer().render_diff(report)
        assert "# Object Knowledge Diff" in markdown
        assert "### Attributes" in markdown
        assert "### Relations" in markdown
    finally:
        repository.close()


def test_review_requires_completed_validation(tmp_path):
    repository = Repository(tmp_path / "sgokb.sqlite")
    try:
        from test_result_validation import _build_and_stage, _receive

        audit, manifest, _, _, _, _ = _build_and_stage(repository, tmp_path)
        result = _valid_result(repository, manifest)
        _, receipt, incoming = _receive(repository, audit, manifest, tmp_path, result)

        with pytest.raises(ValueError, match="completed H-01 validation"):
            DiffReviewService(repository, audit).review_result(
                receipt.receipt_id,
                incoming_root=incoming,
            )
    finally:
        repository.close()


def test_cli_review_and_diff_support_json_and_markdown(tmp_path, capsys):
    db_path = tmp_path / "sgokb.sqlite"
    repository = Repository(db_path)
    try:
        audit, first, object_id, _, _ = _rich_import(repository, tmp_path)
        manifest = _next_package(repository, audit, object_id, tmp_path, "cli")
        result = _valid_result(repository, manifest)
        receipt, incoming, _ = _validated_candidate(
            repository,
            audit,
            manifest,
            tmp_path / "receipt-cli",
            result,
        )
        second = _import(
            repository,
            audit,
            receipt,
            incoming,
            acknowledge_review=True,
        )
        receipt_id = receipt.receipt_id
        first_id = first.version_id
        second_id = second.version_id
    finally:
        repository.close()

    assert (
        package_cli_main(
            [
                "--db",
                str(db_path),
                "review-result",
                receipt_id,
                "--incoming-root",
                str(incoming),
            ]
        )
        == 0
    )
    review_json = json.loads(capsys.readouterr().out)
    assert review_json["review_state"] == "imported"
    assert review_json["schema_version"] == "sgokb.result-review/1.0"

    assert (
        package_cli_main(
            [
                "--db",
                str(db_path),
                "review-result",
                receipt_id,
                "--incoming-root",
                str(incoming),
                "--format",
                "markdown",
            ]
        )
        == 0
    )
    assert "# Object Result Review" in capsys.readouterr().out

    assert (
        package_cli_main(
            [
                "--db",
                str(db_path),
                "diff-versions",
                first_id,
                second_id,
            ]
        )
        == 0
    )
    diff_json = json.loads(capsys.readouterr().out)
    assert diff_json["schema_version"] == "sgokb.object-diff/1.0"

    assert (
        package_cli_main(
            [
                "--db",
                str(db_path),
                "diff-versions",
                first_id,
                second_id,
                "--format",
                "markdown",
            ]
        )
        == 0
    )
    assert "# Object Knowledge Diff" in capsys.readouterr().out
