"""Transport-neutral Evidence read facade for operator clients."""

from __future__ import annotations

from dataclasses import asdict

from .application_read import KnowledgeReadApplication


class EvidenceReadApplication:
    def __init__(self, repository, *, read_application: KnowledgeReadApplication | None = None) -> None:
        self.repository = repository
        self.read = read_application or KnowledgeReadApplication(repository)

    def show(self, evidence_id: str):
        return self.read.get_evidence(evidence_id)

    def provenance(self, evidence_id: str) -> dict:
        return asdict(self.repository.source_store.evidence_provenance(evidence_id))

    def search(self, query: str, **options):
        return self.read.search_evidence(query, **options)
