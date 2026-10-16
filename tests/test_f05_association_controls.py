import json

from sgokb.application import Application
from sgokb.cli import main
from sgokb.repository import Repository


def _capture(app, make_bundle, *, url, html, timestamp="2026-01-01T00:00:00.000Z"):
    imported = app.import_source_path(make_bundle(url=url, html=html, timestamp=timestamp))
    processed = app.process_source_snapshot(imported["snapshot"])
    return imported, processed


def test_manual_source_association_lifecycle_controls_retrieval(tmp_path, make_bundle):
    repository = Repository(tmp_path / "f05-association.sqlite")
    app = Application(repository)
    try:
        object_id = repository.object_store.create_object("架空太郎", "class:character")
        imported, processed = _capture(
            app,
            make_bundle,
            url="https://example.test/association",
            html="<html><main><p>本文には対象名を含めない独立記録。</p></main></html>",
        )
        source_id = imported["source"]

        baseline = app.retrieve_object_evidence(object_id, semantic=False)
        baseline_ids = {item["evidence_id"] for item in baseline["candidates"]}

        association = app.set_source_object_association(
            object_id,
            source_id,
            "confirmed",
            subject_relationship="main_subject",
            note="operator verified",
        )
        assert association["status"] == "confirmed"
        assert association["subject_relationship"] == "main_subject"
        assert association["origin_kind"] == "manual"
        assert association["created_at"]
        assert association["updated_at"]

        retrieved = app.retrieve_object_evidence(object_id, semantic=False)
        retrieved_ids = {item["evidence_id"] for item in retrieved["candidates"]}
        assert set(processed["evidence_ids"]) <= retrieved_ids
        assert baseline_ids <= retrieved_ids
        assert any(
            reason["channel"] == "explicit_association"
            for reason in retrieved["candidates"][0]["reasons"]
        )

        excluded = app.set_source_object_association(object_id, source_id, "excluded")
        assert excluded["status"] == "excluded"
        assert app.retrieve_object_evidence(object_id, semantic=False)["candidate_count"] == 0

        cleared = app.clear_source_object_association(object_id, source_id)
        assert cleared["cleared"] is True
        assert app.list_source_object_associations(object_id) == []
        after_clear = app.retrieve_object_evidence(object_id, semantic=False)
        assert all(
            reason["channel"] != "explicit_association"
            for item in after_clear["candidates"]
            for reason in item["reasons"]
        )
    finally:
        repository.close()


def test_source_suggestions_are_read_only_and_aggregate_evidence(tmp_path, make_bundle):
    repository = Repository(tmp_path / "f05-suggest.sqlite")
    app = Application(repository)
    try:
        object_id = repository.object_store.create_object("架空太郎", "class:character")
        imported, processed = _capture(
            app,
            make_bundle,
            url="https://example.test/suggestion",
            html="<html><main><p>架空太郎についての記録。</p><p>架空太郎の追加情報。</p></main></html>",
        )

        suggested = app.suggest_source_associations(object_id, semantic=False)
        assert suggested["suggestion_count"] == 1
        item = suggested["suggestions"][0]
        assert item["source_id"] == imported["source"]
        assert item["evidence_count"] == len(processed["evidence_ids"])
        assert "name" in item["reason_channels"]
        assert item["association"] is None
        assert app.list_source_object_associations(object_id) == []
    finally:
        repository.close()


def test_cli_association_set_list_and_clear(tmp_path, make_bundle, capsys):
    path = tmp_path / "f05-cli-association.sqlite"
    repository = Repository(path)
    app = Application(repository)
    try:
        object_id = repository.object_store.create_object("架空太郎", "class:character")
        imported, _ = _capture(
            app,
            make_bundle,
            url="https://example.test/cli-association",
            html="<html><main><p>operator association fixture.</p></main></html>",
        )
        source_id = imported["source"]
    finally:
        repository.close()

    assert (
        main(
            [
                "--db",
                str(path),
                "association",
                "set",
                "--object",
                object_id,
                "--source",
                source_id,
                "--status",
                "candidate",
                "--subject-relationship",
                "mentioned_subject",
            ]
        )
        == 0
    )
    set_result = json.loads(capsys.readouterr().out)["data"]
    assert set_result["status"] == "candidate"
    assert set_result["subject_relationship"] == "mentioned_subject"

    assert main(["--db", str(path), "association", "list", "--object", object_id]) == 0
    listed = json.loads(capsys.readouterr().out)["data"]
    assert [item["source_id"] for item in listed] == [source_id]

    assert (
        main(
            [
                "--db",
                str(path),
                "association",
                "clear",
                "--object",
                object_id,
                "--source",
                source_id,
            ]
        )
        == 0
    )
    cleared = json.loads(capsys.readouterr().out)["data"]
    assert cleared["cleared"] is True


def test_cli_evidence_manual_include_exclude_reaches_selection(tmp_path, make_bundle, capsys):
    path = tmp_path / "f05-cli-evidence.sqlite"
    repository = Repository(path)
    app = Application(repository)
    try:
        object_id = repository.object_store.create_object("架空太郎", "class:character")
        _, first = _capture(
            app,
            make_bundle,
            url="https://example.test/first",
            html="<html><main><p>架空太郎の第一記録。</p></main></html>",
        )
        _, second = _capture(
            app,
            make_bundle,
            url="https://example.test/second",
            html="<html><main><p>架空太郎の第二記録。</p></main></html>",
        )
        first_id = first["evidence_ids"][0]
        second_id = second["evidence_ids"][0]
    finally:
        repository.close()

    assert (
        main(
            [
                "--db",
                str(path),
                "evidence",
                "select",
                "--object",
                object_id,
                "--include-evidence",
                second_id,
                "--exclude-evidence",
                first_id,
                "--max-items",
                "1",
                "--max-estimated-tokens",
                "100000",
                "--max-bytes",
                "1000000",
            ]
        )
        == 0
    )
    selected = json.loads(capsys.readouterr().out)["data"]
    assert selected["controls"] == {
        "manual_include": [second_id],
        "manual_exclude": [first_id],
    }
    assert [item["candidate"]["evidence_id"] for item in selected["selected"]] == [second_id]
    assert selected["selected"][0]["selected_by"] == "protected"


def test_association_suggest_cli_does_not_require_persistence(tmp_path, make_bundle, capsys):
    path = tmp_path / "f05-cli-suggest.sqlite"
    repository = Repository(path)
    app = Application(repository)
    try:
        object_id = repository.object_store.create_object("架空太郎", "class:character")
        imported, _ = _capture(
            app,
            make_bundle,
            url="https://example.test/cli-suggest",
            html="<html><main><p>架空太郎の候補Source。</p></main></html>",
        )
        source_id = imported["source"]
    finally:
        repository.close()

    assert (
        main(
            [
                "--db",
                str(path),
                "association",
                "suggest",
                "--object",
                object_id,
            ]
        )
        == 0
    )
    result = json.loads(capsys.readouterr().out)["data"]
    assert result["suggestions"][0]["source_id"] == source_id

    repository = Repository(path)
    try:
        assert repository.source_store.associations_for_object(object_id) == ()
    finally:
        repository.close()
