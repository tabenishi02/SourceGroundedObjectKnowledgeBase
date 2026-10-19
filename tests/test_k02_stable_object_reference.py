from copy import deepcopy

from sgokb.application_read import KnowledgeReadApplication
from sgokb.domain import DerivationKind, EvidenceExtractionMode, EvidenceTargetKind
from sgokb.mcp import MCPReadAdapter
from sgokb.repository import Repository

FACETS = ("values", "personality", "themes")


def _evidence(repo: Repository) -> str:
    source_id = repo.source_store.create_source("K-02 reference source")
    locator_id = repo.source_store.add_locator(
        source_id, "url", "https://example.test/k02-reference"
    )
    snapshot_id = repo.source_store.create_snapshot(
        source_id,
        "2026-10-14T06:00:00Z",
        "web_capture",
        observed_locator_id=locator_id,
    )
    artifact_id = repo.source_store.add_raw_artifact(
        snapshot_id,
        "document",
        "raw/k02-reference.txt",
        "sha-k02-reference",
        128,
    )
    run_id = repo.source_store.create_normalization_run(snapshot_id, "text", "1", [artifact_id])
    return repo.source_store.add_evidence(
        run_id,
        "K-02 grounded evidence",
        EvidenceExtractionMode.VERBATIM,
    )


def _accept_character_version(
    repo: Repository,
    object_id: str,
    version_id: str,
    *,
    base_version_id: str | None,
    evidence_id: str,
    revision: str,
) -> str:
    candidate = repo.version_store.begin_candidate(
        object_id,
        base_version_id,
        version_id=version_id,
    )
    for facet_key in FACETS:
        facet = repo.semantic_store.facet_by_key(facet_key)
        assert facet is not None
        repo.semantic_store.set_version_facet(candidate, facet.facet_id)
        statement_id = repo.semantic_store.add_statement(
            candidate,
            f"{facet_key}-{revision}",
            f"{facet_key} knowledge from {revision}",
            DerivationKind.DIRECT_STATEMENT,
            facet_id=facet.facet_id,
            language="en",
        )
        repo.source_store.link_evidence(
            candidate,
            EvidenceTargetKind.STATEMENT,
            statement_id,
            evidence_id,
        )
    repo.version_store.accept_candidate(candidate)
    return candidate


def _get_character(adapter: MCPReadAdapter, object_id: str, *, version_id: str | None = None):
    request = {
        "object_ids": [object_id],
        "facets": list(FACETS),
        "include_relations": False,
        "include_evidence_refs": False,
    }
    if version_id is not None:
        request["version_ids"] = {object_id: version_id}
    response = adapter.call_tool("get_objects", request)
    assert response["tool_contract_version"] == "sgokb.mcp-read-tools.v1"
    assert response["application_contract_version"] == "sgokb.application-read.v1"
    assert len(response["data"]["objects"]) == 1
    return response["data"]["objects"][0]


def _facet_texts(payload: dict) -> dict[str, str]:
    return {
        facet["key"]: facet["statements"][0]["text"] for facet in payload["knowledge"]["facets"]
    }


def test_k02_stable_object_reference_survives_version_update_and_rename(tmp_path):
    repo = Repository(tmp_path / "k02-stable-reference.sqlite")
    try:
        object_id = repo.object_store.create_object(
            "Character A",
            repo.object_store.class_by_key("character").class_id,
            object_id="object:k02:character-a",
        )
        evidence_id = _evidence(repo)
        version_1 = _accept_character_version(
            repo,
            object_id,
            "version:k02:character-a:v1",
            base_version_id=None,
            evidence_id=evidence_id,
            revision="v1",
        )
        adapter = MCPReadAdapter(KnowledgeReadApplication(repo))

        initial = _get_character(adapter, object_id)
        assert initial["object_id"] == object_id
        assert initial["requested_version_id"] is None
        assert initial["resolved_version_id"] == version_1
        assert initial["is_current"] is True
        assert initial["requested_scope"] == {
            "facets": list(FACETS),
            "include_relations": False,
            "include_evidence_refs": False,
        }
        assert _facet_texts(initial) == {facet: f"{facet} knowledge from v1" for facet in FACETS}

        # Consumer-shaped reference: this is the logical metadata K-01 requires UPDS
        # to retain.  It must not be rewritten when SGOKB advances current Knowledge.
        upds_reference = {
            "selection_event_id": "selection:k02:1",
            "sgokb_object_id": initial["object_id"],
            "sgokb_version_id": initial["resolved_version_id"],
            "requested_facets": list(FACETS),
            "mcp_tool_contract_version": "sgokb.mcp-read-tools.v1",
            "application_contract_version": "sgokb.application-read.v1",
        }
        original_reference = deepcopy(upds_reference)

        version_2 = _accept_character_version(
            repo,
            object_id,
            "version:k02:character-a:v2",
            base_version_id=version_1,
            evidence_id=evidence_id,
            revision="v2",
        )

        current = _get_character(adapter, object_id)
        assert current["object_id"] == object_id
        assert current["resolved_version_id"] == version_2
        assert current["is_current"] is True
        assert _facet_texts(current) == {facet: f"{facet} knowledge from v2" for facet in FACETS}

        pinned = _get_character(adapter, object_id, version_id=version_1)
        assert pinned["object_id"] == object_id
        assert pinned["requested_version_id"] == version_1
        assert pinned["resolved_version_id"] == version_1
        assert pinned["is_current"] is False
        assert _facet_texts(pinned) == {facet: f"{facet} knowledge from v1" for facet in FACETS}

        assert upds_reference == original_reference
        assert upds_reference["sgokb_object_id"] == object_id
        assert upds_reference["sgokb_version_id"] == version_1

        repo.object_store.rename_object(object_id, "Character A Renamed")
        repo.object_store.add_alias(object_id, "Character A")

        renamed_current = _get_character(adapter, object_id)
        renamed_pinned = _get_character(adapter, object_id, version_id=version_1)
        assert renamed_current["object_id"] == object_id
        assert renamed_current["resolved_version_id"] == version_2
        assert renamed_pinned["object_id"] == object_id
        assert renamed_pinned["resolved_version_id"] == version_1
        assert renamed_current["name"] == "Character A Renamed"
        assert renamed_pinned["name"] == "Character A Renamed"
        assert any(alias["value"] == "Character A" for alias in renamed_pinned["aliases"])

        versions = repo.version_store.versions_for_object(object_id)
        assert [(item.version_id, item.object_id) for item in versions] == [
            (version_1, object_id),
            (version_2, object_id),
        ]
        assert all(item.state.value == "accepted" for item in versions)
    finally:
        repo.close()
