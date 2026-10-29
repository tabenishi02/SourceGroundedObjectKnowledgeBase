"""Version router for immutable Object Result review."""

from __future__ import annotations

from pathlib import Path

from sgokb.exchange.package_manifest_v2 import PACKAGE_SCHEMA_VERSION_V2
from sgokb.exchange.result_receipt import DEFAULT_INCOMING_ROOT
from sgokb.storage import PackageExchangeAuditRepository

from .diff import DiffReviewService
from .raw_diff import RawDiffReviewService


class VersionedDiffReviewService:
    def __init__(self, repository, audit: PackageExchangeAuditRepository | None = None):
        self.repository = repository
        self.audit = audit or PackageExchangeAuditRepository(repository.db)

    def review_result(
        self,
        receipt_id: str,
        *,
        incoming_root: str | Path = DEFAULT_INCOMING_ROOT,
    ):
        receipt = self.audit.result_receipt(receipt_id)
        if receipt is None:
            raise ValueError("Unknown Result receipt ID")
        package = self.audit.package_record(str(receipt["package_id"]))
        if package is None:
            raise ValueError("Result receipt Package audit record is missing")
        version = package["schema_version"]
        if version == PACKAGE_SCHEMA_VERSION_V2:
            return RawDiffReviewService(self.repository, self.audit).review_result(
                receipt_id, incoming_root=incoming_root
            )
        if version == "sgokb.object-evidence-package/1.0":
            return DiffReviewService(self.repository, self.audit).review_result(
                receipt_id, incoming_root=incoming_root
            )
        raise ValueError(f"Unsupported Package schema version: {version}")
