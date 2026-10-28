"""Transport-neutral Package / Result exchange applications.

These facades own audit sequencing that previously lived in the CLI adapter.
P-RAW may replace the underlying Package/Result schemas later without changing
this operator-facing lifecycle boundary.
"""

from __future__ import annotations

import json
from pathlib import Path

from .exchange.package_builder import DEFAULT_BUILD_ROOT, ObjectEvidencePackageBuilder
from .exchange.package_transfer import PackageTransferService
from .exchange.result_import import ObjectVersionImportService
from .exchange.result_receipt import DEFAULT_INCOMING_ROOT, ResultReceiptService
from .exchange.result_validation import ResultValidationService
from .review import DiffReviewService
from .storage import PackageExchangeAuditRepository


def _manifest(path: Path) -> dict:
    return json.loads((path / "manifest.json").read_text(encoding="utf-8"))


class PackageExchangeApplication:
    def __init__(self, repository) -> None:
        self.repository = repository
        self.transfer = PackageTransferService()
        self.audit = PackageExchangeAuditRepository(repository.db)

    def build(
        self,
        object_id: str,
        *,
        build_root: str | Path = DEFAULT_BUILD_ROOT,
        include_evidence=(),
        exclude_evidence=(),
        max_estimated_tokens: int = 12000,
        max_bytes: int = 65536,
        max_items: int = 64,
        max_candidates: int = 500,
        knowledge_language: str = "ja",
    ):
        return ObjectEvidencePackageBuilder(self.repository).build(
            object_id,
            build_root=Path(build_root),
            max_estimated_tokens=max_estimated_tokens,
            max_bytes=max_bytes,
            max_items=max_items,
            max_candidates=max_candidates,
            semantic=False,
            manual_include=include_evidence,
            manual_exclude=exclude_evidence,
            knowledge_language=knowledge_language,
        )

    def stage(self, source: str | Path, *, staging_root: str | Path = "exchange/staging"):
        staged = self.transfer.stage_from_directory(Path(source), Path(staging_root))
        manifest = _manifest(Path(staged.path))
        self.audit.record_staged(manifest, staged.path, staged.preflight.to_dict())
        return staged

    def preflight(self, package: str | Path, *, destination: str | Path | None = None):
        resolved_destination = None if destination is None else Path(destination)
        return self.transfer.preflight(Path(package), resolved_destination)

    def export(
        self,
        package: str | Path,
        *,
        destination: str | Path,
        acknowledge_review: bool = False,
    ):
        package_path = Path(package)
        exported = self.transfer.export(
            package_path,
            Path(destination),
            acknowledge_review=acknowledge_review,
        )
        event_id = self.audit.record_export(
            exported.package_id,
            exported.manifest_sha256,
            exported.destination_root,
            exported.path,
            acknowledged_review=exported.acknowledged_review,
            already_present=exported.already_present,
        )
        result = exported.to_dict()
        result["audit_event_id"] = event_id
        return result


class ResultExchangeApplication:
    def __init__(self, repository) -> None:
        self.repository = repository
        self.audit = PackageExchangeAuditRepository(repository.db)
        self.receipts = ResultReceiptService(self.audit)

    def detect(self, *, incoming_root: str | Path = DEFAULT_INCOMING_ROOT):
        return tuple(item.to_dict() for item in self.receipts.detect(Path(incoming_root)))

    def receive(
        self,
        result: str | Path,
        *,
        package_id: str,
        incoming_root: str | Path = DEFAULT_INCOMING_ROOT,
    ):
        return self.receipts.receive(Path(result), package_id, Path(incoming_root))

    def list(self, *, package_id: str | None = None):
        return tuple(self.audit.result_receipts(package_id))

    def pending(self):
        return tuple(self.audit.pending_result_receipts())

    def validate(
        self,
        receipt_id: str,
        *,
        incoming_root: str | Path = DEFAULT_INCOMING_ROOT,
        force: bool = False,
    ):
        return ResultValidationService(self.repository, self.audit).validate_receipt(
            receipt_id,
            incoming_root=Path(incoming_root),
            force=force,
        )

    def review(
        self,
        receipt_id: str,
        *,
        incoming_root: str | Path = DEFAULT_INCOMING_ROOT,
    ):
        return DiffReviewService(self.repository, self.audit).review_result(
            receipt_id,
            incoming_root=Path(incoming_root),
        )

    def import_result(
        self,
        receipt_id: str,
        *,
        incoming_root: str | Path = DEFAULT_INCOMING_ROOT,
        acknowledge_review: bool = False,
    ):
        return ObjectVersionImportService(self.repository, self.audit).import_receipt(
            receipt_id,
            incoming_root=Path(incoming_root),
            acknowledge_review=acknowledge_review,
        )
