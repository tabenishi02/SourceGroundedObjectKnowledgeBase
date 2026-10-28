"""Transport-neutral Registry operator application."""

from __future__ import annotations

from dataclasses import asdict


def _relation_type_payload(record) -> dict:
    """Preserve the public Phase M row-shaped payload (``id`` key)."""

    return {
        "id": record.relation_type_id,
        "key": record.key,
        "name": record.name,
        "description": record.description,
        "status": record.status.value,
        "created_at": record.created_at,
        "updated_at": record.updated_at,
    }


class RegistryOperatorApplication:
    def __init__(self, repository) -> None:
        self.repository = repository
        self.objects = repository.object_store
        self.proposals_store = repository.registry_proposals

    def classes(self) -> list[dict]:
        return [asdict(item) for item in self.objects.classes()]

    def class_show(self, value: str) -> dict:
        record = self.objects.class_by_id(value) or self.objects.class_by_key(value)
        if record is None:
            raise ValueError("Object Class was not found")
        return asdict(record)

    def relation_types(self) -> list[dict]:
        return [_relation_type_payload(item) for item in self.objects.relation_types()]

    def relation_type_show(self, value: str) -> dict:
        record = self.objects.relation_type_by_id(value) or self.objects.relation_type_by_key(value)
        if record is None:
            raise ValueError("Relation Type was not found")
        return _relation_type_payload(record)

    def proposals(self, *, decision: str | None = None):
        return self.proposals_store.list_proposals(decision=decision)

    def proposal_show(self, proposal_ref: str):
        return self.proposals_store.proposal(proposal_ref)

    def proposal_decide(self, proposal_ref: str, decision: str, *, note: str = ""):
        if decision not in {"accepted", "rejected"}:
            raise ValueError("Registry proposal decision must be accepted or rejected")
        return self.proposals_store.decide(proposal_ref, decision, note=note)

    def proposal_apply(self, proposal_ref: str):
        return self.proposals_store.apply(proposal_ref)
