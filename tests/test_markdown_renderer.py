import json
from pathlib import Path

import pytest
from test_object_version_import import _import, _validate
from test_result_validation import _build_and_stage, _valid_result

from sgokb.cli import main as cli_main
from sgokb.exchange import ObjectEvidencePackageBuilder, PackageTransferService
from sgokb.rendering import MarkdownRenderService, ObjectMarkdownRenderer
from sgokb.repository import Repository
from sgokb.storage import MarkdownRenderReadRepository, PackageBuildReadRepository


def _rich_import(repository, tmp_path):
    repository.semantic_store.register_attribute_definition(
        "test_power", "Test Power", "integer", attribute_id="attribute:test_power"
    )
    repository.object_store.register_relation_type(
        "knows", "Knows", relation_type_id="relation:knows"
    )
    relation_target = repository.object_store.create_object(
        "Bob Example", "class:character", object_id="object-h03-bob"
    )
    audit, manifest, object_id, source_id, evidence_id, _ = _build_and_stage(repository, tmp_path)
    result = _valid_result(repository, manifest)
    result["knowledge"]["summary"][0]["temporal_scope"] = {"as_of": "2026-10-13"}
    facet = result["knowledge"]["facets"][0]
    facet["status"] = "content"
    facet["statements"] = [
        {
            "local_key": "facet-view-1",
            "text": "Source attributes a view to Alice.",
            "derivation_kind": "reported_view",
            "attribution": {"kind": "source", "source_id": source_id},
            "evidence": [{"evidence_id": evidence_id, "role": "supports"}],
        }
    ]
    result["knowledge"]["attributes"] = [
        {
            "local_key": "power-1",
            "attribute_id": "attribute:test_power",
            "status": "known",
            "value": 7,
            "evidence": [{"evidence_id": evidence_id, "role": "supports"}],
        }
    ]
    result["knowledge"]["relations"] = [
        {
            "local_key": "knows-1",
            "subject_object_id": object_id,
            "relation_type_id": "relation:knows",
            "object_object_id": relation_target,
            "evidence": [{"evidence_id": evidence_id, "role": "supports"}],
        }
    ]
    receipt, incoming, _ = _validate(repository, audit, manifest, tmp_path, result)
    imported = _import(repository, audit, receipt, incoming)
    return audit, imported, object_id, source_id, evidence_id


def _rendering_state(repository, object_id):
    return repository.one(
        "SELECT * FROM object_derived_states WHERE object_id=? AND kind='rendering'",
        (object_id,),
    )


def test_db_renderer_emits_human_document_and_marks_rendering_ready(tmp_path):
    repository = Repository(tmp_path / "sgokb.sqlite")
    try:
        _, imported, object_id, source_id, evidence_id = _rich_import(repository, tmp_path)
        before_counts = {
            table: repository.one(f"SELECT count(*) n FROM {table}")["n"]
            for table in (
                "knowledge_statements",
                "object_version_attributes",
                "object_relations",
                "evidence_links",
                "object_result_imports",
            )
        }
        state = _rendering_state(repository, object_id)
        assert state["status"] == "pending"
        revision = state["revision"]

        rendered = MarkdownRenderService(repository).render_version(
            imported.version_id,
            output_root=tmp_path / "rendered",
        )
        path = Path(rendered.output_path)
        text = path.read_text(encoding="utf-8")

        assert rendered.derived_state_update == "ready"
        assert rendered.byte_count == len(text.encode("utf-8"))
        assert rendered.sha256
        assert path.name == f"{imported.version_id}.md"
        assert "Derived read-only view" in text
        assert "# Alice Example" in text
        assert f"Version ID: `{imported.version_id}`" in text
        assert "Character" in text
        assert "Alice Exampleについての根拠付き要約。" in text
        assert "Source attributes a view to Alice." in text
        assert source_id in text
        assert "Alice source" in text
        assert "Test Power" in text
        assert "| 7 |" in text
        assert "Bob Example" in text
        assert "Knows" in text
        assert f"Evidence ID: `{evidence_id}`" in text
        assert "Alice Example is a fictional character used for H-01 validation tests." in text
        assert "## Import provenance" in text
        assert "Canonical data remains in SQLite / structured JSON" in text

        state = _rendering_state(repository, object_id)
        assert state["status"] == "ready"
        assert state["revision"] == revision
        after_counts = {
            table: repository.one(f"SELECT count(*) n FROM {table}")["n"] for table in before_counts
        }
        assert after_counts == before_counts
    finally:
        repository.close()


def test_manual_markdown_edit_is_not_canonical_and_rerender_restores_db_view(tmp_path):
    repository = Repository(tmp_path / "sgokb.sqlite")
    try:
        _, imported, _, _, _ = _rich_import(repository, tmp_path)
        service = MarkdownRenderService(repository)
        first = service.render_version(imported.version_id, output_root=tmp_path / "rendered")
        path = Path(first.output_path)
        original = path.read_bytes()
        original_statement = repository.one(
            "SELECT text FROM knowledge_statements WHERE version_id=? ORDER BY rowid LIMIT 1",
            (imported.version_id,),
        )["text"]

        path.write_text(
            "# manually edited\n\nThis must never become canonical.\n", encoding="utf-8"
        )
        assert (
            repository.one(
                "SELECT text FROM knowledge_statements WHERE version_id=? ORDER BY rowid LIMIT 1",
                (imported.version_id,),
            )["text"]
            == original_statement
        )

        second = service.render_version(imported.version_id, output_root=tmp_path / "rendered")
        assert Path(second.output_path).read_bytes() == original
        assert second.sha256 == first.sha256
        assert "manually edited" not in Path(second.output_path).read_text(encoding="utf-8")
    finally:
        repository.close()


def test_json_rendering_is_deterministic_and_does_not_touch_derived_state(tmp_path):
    repository = Repository(tmp_path / "sgokb.sqlite")
    try:
        _, imported, object_id, _, _ = _rich_import(repository, tmp_path)
        model = MarkdownRenderReadRepository(repository.db).build_model(imported.version_id)
        round_tripped = json.loads(json.dumps(model, ensure_ascii=False))
        renderer = ObjectMarkdownRenderer()
        before = dict(_rendering_state(repository, object_id))

        first = renderer.render(round_tripped)
        second = renderer.render(round_tripped)

        assert first == second
        assert "# Alice Example" in first
        assert dict(_rendering_state(repository, object_id)) == before

        package_snapshot = PackageBuildReadRepository(repository.db).current_object_snapshot(
            object_id
        )
        package_text = renderer.render(package_snapshot)
        assert object_id in package_text
        assert "Alice Exampleについての根拠付き要約。" in package_text
        assert dict(_rendering_state(repository, object_id)) == before
    finally:
        repository.close()


def test_historical_render_does_not_mark_current_target_ready(tmp_path):
    repository = Repository(tmp_path / "sgokb.sqlite")
    try:
        audit, first, object_id, _, _ = _rich_import(repository, tmp_path)
        first_render = MarkdownRenderService(repository).render_version(
            first.version_id, output_root=tmp_path / "rendered"
        )
        assert first_render.derived_state_update == "ready"

        built = ObjectEvidencePackageBuilder(repository).build(
            object_id, build_root=tmp_path / "build2", semantic=False
        )
        transfer = PackageTransferService()
        staged = transfer.stage_from_directory(built.path, tmp_path / "staging2")
        manifest = json.loads(Path(staged.path, "manifest.json").read_text(encoding="utf-8"))
        audit.record_staged(manifest, staged.path, staged.preflight.to_dict())
        exported = transfer.export(staged.path, tmp_path / "DriveSync2")
        audit.record_export(
            exported.package_id,
            exported.manifest_sha256,
            exported.destination_root,
            exported.path,
            acknowledged_review=False,
            already_present=exported.already_present,
        )
        result = _valid_result(repository, manifest)
        result["knowledge"]["summary"][0]["text"] = "Second Version grounded summary."
        second_root = tmp_path / "second"
        second_root.mkdir()
        receipt, incoming, _ = _validate(repository, audit, manifest, second_root, result)
        second = _import(
            repository,
            audit,
            receipt,
            incoming,
            acknowledge_review=True,
        )
        state = _rendering_state(repository, object_id)
        assert state["target_version_id"] == second.version_id
        assert state["status"] == "pending"

        historical = MarkdownRenderService(repository).render_version(
            first.version_id, output_root=tmp_path / "rendered"
        )

        assert historical.derived_state_update == "not_current"
        state = _rendering_state(repository, object_id)
        assert state["target_version_id"] == second.version_id
        assert state["status"] == "pending"
    finally:
        repository.close()


def test_render_failure_marks_only_current_rendering_state_failed(tmp_path):
    class BrokenRenderer(ObjectMarkdownRenderer):
        def render(self, value):
            raise RuntimeError("synthetic rendering failure")

    repository = Repository(tmp_path / "sgokb.sqlite")
    try:
        _, imported, object_id, _, _ = _rich_import(repository, tmp_path)
        with pytest.raises(RuntimeError, match="synthetic rendering failure"):
            MarkdownRenderService(repository, renderer=BrokenRenderer()).render_version(
                imported.version_id, output_root=tmp_path / "rendered"
            )

        state = _rendering_state(repository, object_id)
        assert state["status"] == "failed"
        assert "synthetic rendering failure" in state["last_error"]
        assert repository.version_store.current_version_id(object_id) == imported.version_id
        assert (
            repository.one(
                "SELECT count(*) n FROM knowledge_statements WHERE version_id=?",
                (imported.version_id,),
            )["n"]
            > 0
        )

        recovered = MarkdownRenderService(repository).render_version(
            imported.version_id, output_root=tmp_path / "rendered"
        )
        assert recovered.derived_state_update == "ready"
        assert _rendering_state(repository, object_id)["status"] == "ready"
    finally:
        repository.close()


def test_revision_cas_prevents_old_render_worker_from_marking_new_target_ready(tmp_path):
    repository = Repository(tmp_path / "sgokb.sqlite")
    try:
        _, imported, object_id, _, _ = _rich_import(repository, tmp_path)
        candidate = repository.version_store.begin_candidate(object_id, imported.version_id)

        class RacingRenderer(ObjectMarkdownRenderer):
            fired = False

            def render(self, value):
                text = super().render(value)
                if not self.fired:
                    self.fired = True
                    repository.version_store.accept_candidate(candidate)
                return text

        rendered = MarkdownRenderService(repository, renderer=RacingRenderer()).render_version(
            imported.version_id,
            output_root=tmp_path / "rendered",
        )

        assert rendered.derived_state_update == "superseded"
        assert repository.version_store.current_version_id(object_id) == candidate
        state = _rendering_state(repository, object_id)
        assert state["target_version_id"] == candidate
        assert state["status"] == "pending"
    finally:
        repository.close()


def test_renderer_includes_review_metadata_without_applying_registry_proposal(tmp_path):
    repository = Repository(tmp_path / "sgokb.sqlite")
    try:
        audit, manifest, object_id, _, evidence_id, _ = _build_and_stage(repository, tmp_path)
        result = _valid_result(repository, manifest)
        result["result_status"] = "partial"
        result["gaps"] = [
            {
                "local_key": "gap-1",
                "kind": "not_analyzed",
                "description": "A documented analysis gap.",
                "evidence": [],
            }
        ]
        result["registry_proposals"] = [
            {
                "local_key": "proposal-1",
                "proposal_kind": "object_alias",
                "rationale": "Evidence suggests a display alias.",
                "payload": {"value": "Alicia Example"},
                "evidence": [{"evidence_id": evidence_id, "role": "supports"}],
            }
        ]
        receipt, incoming, _ = _validate(repository, audit, manifest, tmp_path, result)
        imported = _import(
            repository,
            audit,
            receipt,
            incoming,
            acknowledge_review=True,
        )

        rendered = MarkdownRenderService(repository).render_version(
            imported.version_id, output_root=tmp_path / "rendered"
        )
        text = Path(rendered.output_path).read_text(encoding="utf-8")

        assert "## Review metadata" in text
        assert "Result status: `partial`" in text
        assert "### Gaps" in text
        assert "A documented analysis gap." in text
        assert "### Registry proposals" in text
        assert "Evidence suggests a display alias." in text
        assert "Alicia Example" in text
        assert "Review acknowledged: yes" in text
        aliases = repository.rows(
            "SELECT value FROM object_aliases WHERE object_id=?", (object_id,)
        )
        assert "Alicia Example" not in {row["value"] for row in aliases}
    finally:
        repository.close()


def test_renderer_rejects_candidate_version(tmp_path):
    repository = Repository(tmp_path / "sgokb.sqlite")
    try:
        _, _, object_id, _, _, _ = _build_and_stage(repository, tmp_path)
        candidate = repository.version_store.begin_candidate(object_id, None)
        with pytest.raises(ValueError, match="accepted Object Version"):
            MarkdownRenderService(repository).render_version(
                candidate, output_root=tmp_path / "rendered"
            )
    finally:
        repository.close()


def test_cli_render_executes_managed_render(tmp_path, capsys):
    db_path = tmp_path / "sgokb.sqlite"
    repository = Repository(db_path)
    try:
        _, imported, object_id, _, _ = _rich_import(repository, tmp_path)
        version_id = imported.version_id
    finally:
        repository.close()

    output_root = tmp_path / "cli-rendered"
    exit_code = cli_main(
        [
            "--db",
            str(db_path),
            "render",
            "--version",
            version_id,
            "--output-root",
            str(output_root),
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["data"]["version_id"] == version_id
    assert payload["data"]["derived_state_update"] == "ready"
    assert Path(payload["data"]["output_path"]).is_file()

    reopened = Repository(db_path)
    try:
        assert _rendering_state(reopened, object_id)["status"] == "ready"
    finally:
        reopened.close()


def test_managed_path_percent_encodes_windows_unsafe_id_characters(tmp_path):
    path = MarkdownRenderService._managed_path(tmp_path, "object:test", "version:test")
    assert "object%3Atest" in str(path)
    assert path.name == "version%3Atest.md"
