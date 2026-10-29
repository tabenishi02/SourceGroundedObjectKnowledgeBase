"""Version router for Object Result validation."""

from __future__ import annotations

from pathlib import Path

from .package_manifest_v2 import PACKAGE_SCHEMA_VERSION_V2
from .result_validation import ResultValidationService
from .result_validation_v2 import RawResultValidationService


class VersionedResultValidationService:
    def __init__(self, repository, audit):
        self.repository = repository
        self.audit = audit

    def validate_receipt(self, receipt_id: str, *, incoming_root: Path, force: bool = False):
        receipt = self.audit.result_receipt(receipt_id)
        if receipt is None:
            raise ValueError("Unknown Result receipt ID")
        package = self.audit.package_record(str(receipt["package_id"]))
        if package is None:
            raise ValueError("Result receipt Package audit record is missing")
        version = package["schema_version"]
        if version == PACKAGE_SCHEMA_VERSION_V2:
            return RawResultValidationService(self.repository, self.audit).validate_receipt(
                receipt_id, incoming_root=incoming_root, force=force
            )
        if version == "sgokb.object-evidence-package/1.0":
            return ResultValidationService(self.repository, self.audit).validate_receipt(
                receipt_id, incoming_root=incoming_root, force=force
            )
        raise ValueError(f"Unsupported Package schema version: {version}")
