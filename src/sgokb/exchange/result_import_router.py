"""Version router for explicit Object Result import."""

from __future__ import annotations

from pathlib import Path

from sgokb.storage import PackageExchangeAuditRepository

from .package_manifest_v2 import PACKAGE_SCHEMA_VERSION_V2
from .result_import import ObjectVersionImportService
from .result_import_v2 import RawObjectVersionImportService
from .result_receipt import DEFAULT_INCOMING_ROOT


class VersionedObjectVersionImportService:
    def __init__(self, repository, audit: PackageExchangeAuditRepository | None = None):
        self.repository = repository
        self.audit = audit or PackageExchangeAuditRepository(repository.db)

    def import_receipt(
        self,
        receipt_id: str,
        *,
        incoming_root: str | Path = DEFAULT_INCOMING_ROOT,
        acknowledge_review: bool = False,
    ):
        receipt = self.audit.result_receipt(receipt_id)
        if receipt is None:
            raise ValueError("Unknown Result receipt ID")
        package = self.audit.package_record(str(receipt["package_id"]))
        if package is None:
            raise ValueError("Result receipt Package audit record is missing")
        version = package["schema_version"]
        if version == PACKAGE_SCHEMA_VERSION_V2:
            return RawObjectVersionImportService(self.repository, self.audit).import_receipt(
                receipt_id,
                incoming_root=incoming_root,
                acknowledge_review=acknowledge_review,
            )
        if version == "sgokb.object-evidence-package/1.0":
            return ObjectVersionImportService(self.repository, self.audit).import_receipt(
                receipt_id,
                incoming_root=incoming_root,
                acknowledge_review=acknowledge_review,
            )
        raise ValueError(f"Unsupported Package schema version: {version}")
