"""Explicit import of one validated Raw-grounded Object Result v2 receipt."""

from __future__ import annotations

from pathlib import Path

from sgokb.review.raw_diff import RawDiffReviewService
from sgokb.storage import PackageExchangeAuditRepository
from sgokb.storage.result_import_repository_v2 import RawResultImportRepository

from .result_import import ObjectVersionImportService, load_immutable_result_artifact
from .result_receipt import DEFAULT_INCOMING_ROOT


class RawObjectVersionImportService(ObjectVersionImportService):
    def __init__(
        self,
        repository,
        audit: PackageExchangeAuditRepository | None = None,
        *,
        failure_hook=None,
    ):
        super().__init__(repository, audit, failure_hook=failure_hook)
        self.import_store = RawResultImportRepository(repository.db)

    def import_receipt(
        self,
        receipt_id: str,
        *,
        incoming_root: str | Path = DEFAULT_INCOMING_ROOT,
        acknowledge_review: bool = False,
    ):
        existing = self.import_store.import_by_receipt(receipt_id)
        if existing is not None:
            return self._result(existing, duplicate=True)

        receipt = self.audit.result_receipt(receipt_id)
        if receipt is None:
            raise ValueError("Unknown Result receipt ID")
        if receipt["validation_state"] != "valid":
            raise ValueError("Object Result import requires successful validation")

        review = RawDiffReviewService(self.repository, self.audit).review_result(
            receipt_id,
            incoming_root=incoming_root,
        )
        if review.blocked:
            raise ValueError("Object Result v2 import is blocked by review")
        if review.requires_review and not acknowledge_review:
            raise ValueError("Object Result v2 import requires explicit review acknowledgement")

        result, sha256, byte_count = load_immutable_result_artifact(receipt, incoming_root)
        imported = self.import_store.import_result(
            receipt_id,
            result,
            artifact_sha256=sha256,
            artifact_byte_count=byte_count,
            review_acknowledged=acknowledge_review,
            failure_hook=self.failure_hook,
        )
        return self._result(imported, duplicate=bool(imported.get("duplicate")))
