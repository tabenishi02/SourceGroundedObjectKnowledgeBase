from test_object_version_import import _import, _validate
from test_result_validation import _build_and_stage, _valid_result

from sgokb.repository import Repository


def test_registry_proposal_requires_accept_then_explicit_apply(tmp_path):
    repository = Repository(tmp_path / "registry-proposal.sqlite")
    try:
        audit, manifest, object_id, _, evidence_id, _ = _build_and_stage(repository, tmp_path)
        result = _valid_result(repository, manifest)
        result["registry_proposals"] = [
            {
                "local_key": "proposal-m01-alias",
                "proposal_kind": "object_alias",
                "rationale": "Evidence supports an additional alias.",
                "payload": {"value": "Alice M01 Alias", "language": "en"},
                "evidence": [{"evidence_id": evidence_id, "role": "supports"}],
            }
        ]
        receipt, incoming, report = _validate(repository, audit, manifest, tmp_path, result)
        assert any(
            finding.code == "registry_proposal_requires_review" and finding.severity == "review"
            for finding in report.findings
        )
        imported = _import(
            repository,
            audit,
            receipt,
            incoming,
            acknowledge_review=True,
        )

        proposals = repository.registry_proposals.list_proposals()
        assert len(proposals) == 1
        proposal = proposals[0]
        assert proposal["version_id"] == imported.version_id
        assert proposal["object_id"] == object_id
        assert proposal["decision"] == "pending"
        proposal_ref = proposal["proposal_ref"]

        aliases = {alias.value for alias in repository.object_store.get_object(object_id).aliases}
        assert "Alice M01 Alias" not in aliases

        accepted = repository.registry_proposals.decide(
            proposal_ref,
            "accepted",
            note="operator reviewed evidence",
        )
        assert accepted["decision"] == "accepted"
        aliases = {alias.value for alias in repository.object_store.get_object(object_id).aliases}
        assert "Alice M01 Alias" not in aliases

        applied = repository.registry_proposals.apply(proposal_ref)
        assert applied["duplicate"] is False
        aliases = {alias.value for alias in repository.object_store.get_object(object_id).aliases}
        assert "Alice M01 Alias" in aliases

        duplicate = repository.registry_proposals.apply(proposal_ref)
        assert duplicate["duplicate"] is True
        aliases = [
            alias.value
            for alias in repository.object_store.get_object(object_id).aliases
            if alias.value == "Alice M01 Alias"
        ]
        assert aliases == ["Alice M01 Alias"]
    finally:
        repository.close()


def test_rejected_registry_proposal_cannot_apply(tmp_path):
    repository = Repository(tmp_path / "registry-proposal-reject.sqlite")
    try:
        audit, manifest, _, _, evidence_id, _ = _build_and_stage(repository, tmp_path)
        result = _valid_result(repository, manifest)
        result["registry_proposals"] = [
            {
                "local_key": "proposal-m01-reject",
                "proposal_kind": "object_alias",
                "rationale": "Review fixture.",
                "payload": {"value": "Rejected Alias"},
                "evidence": [{"evidence_id": evidence_id, "role": "supports"}],
            }
        ]
        receipt, incoming, _ = _validate(repository, audit, manifest, tmp_path, result)
        _import(repository, audit, receipt, incoming, acknowledge_review=True)
        proposal_ref = repository.registry_proposals.list_proposals()[0]["proposal_ref"]
        repository.registry_proposals.decide(proposal_ref, "rejected", note="not accepted")

        try:
            repository.registry_proposals.apply(proposal_ref)
        except ValueError as error:
            assert "explicitly accepted" in str(error)
        else:
            raise AssertionError("Rejected proposal must not be applicable")
    finally:
        repository.close()
