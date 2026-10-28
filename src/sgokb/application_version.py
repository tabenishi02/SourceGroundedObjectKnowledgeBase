"""Transport-neutral accepted Version read/diff application."""

from __future__ import annotations

from .application_read import KnowledgeReadApplication
from .review import DiffReviewService
from .storage import PackageExchangeAuditRepository


class VersionReadApplication:
    def __init__(self, repository) -> None:
        self.repository = repository

    def show(self, version_id: str):
        row = self.repository.db.execute(
            "SELECT object_id FROM object_versions WHERE id=?", (version_id,)
        ).fetchone()
        if not row:
            raise ValueError("Object Version was not found")
        return KnowledgeReadApplication(self.repository).get_object(
            row["object_id"], version_id=version_id
        )

    def diff(self, before_version_id: str, after_version_id: str):
        return DiffReviewService(
            self.repository, PackageExchangeAuditRepository(self.repository.db)
        ).diff_versions(before_version_id, after_version_id)
