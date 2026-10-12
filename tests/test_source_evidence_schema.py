import json
import sqlite3

import pytest

from sgokb.domain import (
    AssociationStatus,
    AttributeValueType,
    DerivationKind,
    EvidenceExtractionMode,
    EvidenceRole,
    EvidenceTargetKind,
    MetadataOrigin,
)
from sgokb.repository import Repository


@pytest.fixture
def repo(tmp_path):
    value = Repository(tmp_path / "source-evidence-schema.sqlite")
    yield value
    value.close()


def _object_and_version(repo, *, class_key="character", suffix="a"):
    class_id = repo.object_store.class_by_key(class_key).class_id
    object_id = repo.object_store.create_object(f"Object {suffix}", class_id)
    version_id = f"version-{suffix}"
    with repo.db:
        repo.db.execute(
            "INSERT INTO object_versions VALUES(?,?,?,?)",
            (version_id, object_id, 1, "2026-10-12T00:00:00Z"),
        )
    return object_id, version_id


def _provenance(repo, *, suffix="a", url="https://example.test/page"):
    source_id = repo.source_store.create_source(f"Source {suffix}")
    locator_id = repo.source_store.add_locator(source_id, "url", url, preferred=True)
    snapshot_id = repo.source_store.create_snapshot(
        source_id,
        "2026-10-12T00:00:00Z",
        "web_capture",
        observed_locator_id=locator_id,
        capture_tool="web-page-capture",
        capture_version="1",
        title=f"Page {suffix}",
    )
    artifact_id = repo.source_store.add_raw_artifact(
        snapshot_id,
        "rendered_dom",
        f"raw/{suffix}/dom.html",
        f"sha256-{suffix}",
        100,
        logical_path="dom.html",
        media_type="text/html",
    )
    run_id = repo.source_store.create_normalization_run(
        snapshot_id,
        "generic-html",
        "1",
        [artifact_id],
        configuration={"noise_filter": "v1"},
    )
    evidence_id = repo.source_store.add_evidence(
        run_id,
        f"Evidence text {suffix}",
        EvidenceExtractionMode.NORMALIZED,
        language="en",
    )
    repo.source_store.add_evidence_location(
        evidence_id,
        "dom_path",
        {"path": "/html/body/main/p[1]"},
    )
    return source_id, locator_id, snapshot_id, artifact_id, run_id, evidence_id


def test_source_identity_is_independent_from_locator_and_locator_is_not_globally_unique(repo):
    first = repo.source_store.create_source("First")
    second = repo.source_store.create_source("Second")
    assert first != second
    assert repo.source_store.locators(first) == ()

    first_locator = repo.source_store.add_locator(first, "url", "https://example.test/shared")
    second_locator = repo.source_store.add_locator(second, "url", "https://example.test/shared")
    assert first_locator != second_locator
    assert repo.source_store.locators(first)[0].value == "https://example.test/shared"
    assert repo.source_store.locators(second)[0].value == "https://example.test/shared"


def test_snapshot_observed_locator_must_belong_to_same_source(repo):
    first = repo.source_store.create_source("First")
    second = repo.source_store.create_source("Second")
    locator = repo.source_store.add_locator(first, "url", "https://example.test/a")

    with pytest.raises(sqlite3.IntegrityError, match="snapshot locator must belong"):
        repo.source_store.create_snapshot(
            second,
            "2026-10-12T00:00:00Z",
            "web_capture",
            observed_locator_id=locator,
        )


def test_source_classification_metadata_and_object_association_keep_separate_axes(repo):
    source_id, _, snapshot_id, *_ = _provenance(repo)
    object_id, _ = _object_and_version(repo)

    repo.source_store.add_classification(
        source_id,
        "resource_type",
        "web_page",
        MetadataOrigin.DETERMINISTIC,
        snapshot_id=snapshot_id,
    )
    repo.source_store.add_classification(
        source_id,
        "document_genre",
        "interview",
        MetadataOrigin.INFERRED,
        snapshot_id=snapshot_id,
    )
    repo.source_store.add_metadata(
        source_id,
        "publisher",
        "Example Publisher",
        MetadataOrigin.CAPTURED,
        snapshot_id=snapshot_id,
    )
    repo.source_store.associate_object(
        source_id,
        object_id,
        AssociationStatus.CONFIRMED,
        subject_relationship="first_party",
        origin_kind="manual",
    )

    classifications = repo.rows(
        "SELECT axis,value,origin_kind FROM source_classifications WHERE source_id=? ORDER BY axis",
        (source_id,),
    )
    assert classifications == [
        {"axis": "document_genre", "value": "interview", "origin_kind": "inferred"},
        {
            "axis": "resource_type",
            "value": "web_page",
            "origin_kind": "deterministic",
        },
    ]
    metadata = repo.one("SELECT * FROM source_metadata_values WHERE source_id=?", (source_id,))
    assert json.loads(metadata["value_json"]) == "Example Publisher"
    association = repo.one(
        "SELECT status,subject_relationship FROM source_object_associations "
        "WHERE source_id=? AND object_id=?",
        (source_id, object_id),
    )
    assert association == {"status": "confirmed", "subject_relationship": "first_party"}


def test_normalization_run_only_accepts_raw_artifacts_from_its_snapshot(repo):
    source_a, _, snapshot_a, *_ = _provenance(repo, suffix="a")
    del source_a
    source_b = repo.source_store.create_source("B")
    snapshot_b = repo.source_store.create_snapshot(
        source_b, "2026-10-12T01:00:00Z", "manual_import"
    )
    artifact_b = repo.source_store.add_raw_artifact(
        snapshot_b, "document", "raw/b.txt", "sha256-b", 10
    )

    with pytest.raises(sqlite3.IntegrityError, match="artifact must belong"):
        repo.source_store.create_normalization_run(snapshot_a, "text", "1", [artifact_b])


def test_evidence_requires_complete_provenance_chain_and_is_content_immutable(repo):
    source_id, _, snapshot_id, artifact_id, run_id, evidence_id = _provenance(repo)
    provenance = repo.source_store.evidence_provenance(evidence_id)
    assert provenance.source.source_id == source_id
    assert provenance.snapshot.snapshot_id == snapshot_id
    assert provenance.raw_artifact_ids == (artifact_id,)
    assert provenance.evidence.run_id == run_id

    with pytest.raises(sqlite3.IntegrityError, match="immutable"):
        with repo.db:
            repo.db.execute(
                "UPDATE evidence_records SET content='changed' WHERE id=?", (evidence_id,)
            )

    orphan_run = "orphan-run"
    with repo.db:
        repo.db.execute(
            "INSERT INTO normalization_runs VALUES(?,?,?,?,?,?,?,?)",
            (orphan_run, snapshot_id, "text", "1", "{}", "{}", "complete", "now"),
        )
    with pytest.raises(sqlite3.IntegrityError, match="requires raw artifact"):
        repo.source_store.add_evidence(orphan_run, "orphan", EvidenceExtractionMode.VERBATIM)


def test_evidence_location_keeps_human_verifiable_source_position(repo):
    *_, evidence_id = _provenance(repo)
    location = repo.one("SELECT * FROM evidence_locations WHERE evidence_id=?", (evidence_id,))
    assert location["kind"] == "dom_path"
    assert json.loads(location["value_json"])["path"] == "/html/body/main/p[1]"


def test_source_dependency_registry_is_separate_from_object_relations(repo):
    first = repo.source_store.create_source("First")
    second = repo.source_store.create_source("Second")
    relation_id = repo.source_store.relate_sources(first, "cites", second)
    relation = repo.one("SELECT * FROM source_relations WHERE id=?", (relation_id,))
    relation_type = repo.one(
        "SELECT key FROM source_relation_types WHERE id=?", (relation["relation_type_id"],)
    )
    assert relation_type["key"] == "cites"
    assert repo.object_store.relation_type_by_key("cites") is None


def test_statement_attribute_and_relation_can_link_to_evidence_with_roles(repo):
    _, _, _, _, _, evidence_id = _provenance(repo)
    subject, version_id = _object_and_version(repo, suffix="subject")
    target, _ = _object_and_version(repo, class_key="work", suffix="target")

    statement_id = repo.semantic_store.add_statement(
        version_id,
        "summary-1",
        "A grounded summary.",
        DerivationKind.SYNTHESIS,
    )
    repo.semantic_store.register_attribute_definition(
        "release_date_e03", "Release date E03", AttributeValueType.DATE
    )
    attribute_id = repo.semantic_store.add_attribute(version_id, "release_date_e03", "2026-10-12")
    relation_type = repo.object_store.register_relation_type("appears_in_e03", "appears in")
    with repo.db:
        repo.db.execute(
            "INSERT INTO object_relations VALUES(?,?,?,?,?,?)",
            (
                "relation-e03",
                version_id,
                subject,
                relation_type,
                target,
                "2026-10-12T00:00:00Z",
            ),
        )

    repo.source_store.link_evidence(
        version_id,
        EvidenceTargetKind.STATEMENT,
        statement_id,
        evidence_id,
        EvidenceRole.SUPPORTS,
        origin_ref="result:test",
    )
    repo.source_store.link_evidence(
        version_id,
        EvidenceTargetKind.ATTRIBUTE,
        attribute_id,
        evidence_id,
        EvidenceRole.CONTEXTUALIZES,
    )
    repo.source_store.link_evidence(
        version_id,
        EvidenceTargetKind.RELATION,
        "relation-e03",
        evidence_id,
        EvidenceRole.CONTRADICTS,
    )

    links = repo.source_store.evidence_links_for_target(
        version_id, EvidenceTargetKind.STATEMENT, statement_id
    )
    assert len(links) == 1
    assert links[0].role is EvidenceRole.SUPPORTS
    assert links[0].origin_ref == "result:test"
    assert repo.one("SELECT count(*) n FROM evidence_links")["n"] == 3


def test_evidence_link_target_must_belong_to_declared_version(repo):
    *_, evidence_id = _provenance(repo)
    _, version_a = _object_and_version(repo, suffix="a")
    _, version_b = _object_and_version(repo, suffix="b")
    statement = repo.semantic_store.add_statement(
        version_a, "summary-a", "Version A only.", DerivationKind.DIRECT_STATEMENT
    )

    with pytest.raises(sqlite3.IntegrityError, match="must belong to version"):
        repo.source_store.link_evidence(
            version_b,
            EvidenceTargetKind.STATEMENT,
            statement,
            evidence_id,
            EvidenceRole.SUPPORTS,
        )


def test_source_reference_validation_rejects_invented_source_id(repo):
    source_id, *_ = _provenance(repo)
    assert repo.source_store.validate_source_references([source_id]) == (source_id,)
    with pytest.raises(ValueError, match="Unknown source ID"):
        repo.source_store.validate_source_references(["invented-source"])


def test_package_membership_validation_rejects_unknown_or_out_of_package_evidence(repo):
    *_, evidence_a = _provenance(repo, suffix="a")
    *_, evidence_b = _provenance(repo, suffix="b", url="https://example.test/b")

    assert repo.source_store.validate_evidence_references(
        [evidence_a], package_evidence_ids=[evidence_a]
    ) == (evidence_a,)
    with pytest.raises(ValueError, match="outside the input Package"):
        repo.source_store.validate_evidence_references(
            [evidence_b], package_evidence_ids=[evidence_a]
        )
    with pytest.raises(ValueError, match="Unknown evidence ID"):
        repo.source_store.validate_evidence_references(["invented-evidence"])


def test_legacy_and_canonical_source_tables_coexist_without_reissuing_ids(repo):
    with repo.db:
        repo.db.execute(
            "INSERT INTO sources VALUES(?,?,?,?,?)",
            ("same-id", "https://legacy.test", "legacy", "wiki", "2026-01-01"),
        )
    canonical_id = repo.source_store.create_source("Canonical", source_id="same-id")
    assert canonical_id == "same-id"
    assert repo.one("SELECT url FROM sources WHERE id='same-id'")["url"] == "https://legacy.test"
    assert repo.source_store.source_by_id("same-id").label == "Canonical"
