"""Transport-neutral Package / Result exchange applications."""

from __future__ import annotations

import json
from pathlib import Path

from .exchange.package_builder import DEFAULT_BUILD_ROOT, ObjectEvidencePackageBuilder
from .exchange.package_manifest_v2 import PACKAGE_SCHEMA_VERSION_V2
from .exchange.package_transfer import PackageTransferService
from .exchange.package_transfer_v2 import RawPackageTransferService
from .exchange.raw_package_builder import ObjectRawPackageBuilder
from .exchange.result_import import ObjectVersionImportService
from .exchange.result_receipt import DEFAULT_INCOMING_ROOT, ResultReceiptService
from .exchange.result_validation_router import VersionedResultValidationService
from .review import DiffReviewService
from .storage import PackageExchangeAuditRepository, RawGroundingRepository


def _manifest(path: Path) -> dict:
    return json.loads((path / "manifest.json").read_text(encoding="utf-8"))


def _is_v2(value: object) -> bool:
    return str(value) in {"2", "v2", PACKAGE_SCHEMA_VERSION_V2}


class PackageExchangeApplication:
    def __init__(self, repository) -> None:
        self.repository = repository
        self.audit = PackageExchangeAuditRepository(repository.db)
        self.raw_audit = RawGroundingRepository(repository.db)

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
        package_version: str = "v1",
        max_total_raw_bytes: int = 16 * 1024 * 1024,
        max_single_raw_bytes: int = 8 * 1024 * 1024,
        max_raw_artifacts: int = 64,
    ):
        common = dict(
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
        if _is_v2(package_version):
            return ObjectRawPackageBuilder(self.repository).build(
                object_id,
                **common,
                max_total_raw_bytes=max_total_raw_bytes,
                max_single_raw_bytes=max_single_raw_bytes,
                max_raw_artifacts=max_raw_artifacts,
            )
        if str(package_version) not in {"1", "v1", "sgokb.object-evidence-package/1.0"}:
            raise ValueError(f"Unsupported Package version: {package_version}")
        return ObjectEvidencePackageBuilder(self.repository).build(object_id, **common)

    @staticmethod
    def _transfer(package: str | Path):
        manifest = _manifest(Path(package))
        if manifest.get("schema_version") == PACKAGE_SCHEMA_VERSION_V2:
            return RawPackageTransferService()
        if manifest.get("schema_version") == "sgokb.object-evidence-package/1.0":
            return PackageTransferService()
        raise ValueError(f"Unsupported Package schema version: {manifest.get('schema_version')}")

    def stage(self, source: str | Path, *, staging_root: str | Path = "exchange/staging"):
        source_path = Path(source)
        transfer = self._transfer(source_path)
        staged = transfer.stage_from_directory(source_path, Path(staging_root))
        manifest = _manifest(Path(staged.path))
        self.audit.record_staged(manifest, staged.path, staged.preflight.to_dict())
        self.raw_audit.record_package(manifest)
        return staged

    def preflight(self, package: str | Path, *, destination: str | Path | None = None):
        package_path = Path(package)
        resolved_destination = None if destination is None else Path(destination)
        return self._transfer(package_path).preflight(package_path, resolved_destination)

    def export(
        self,
        package: str | Path,
        *,
        destination: str | Path,
        acknowledge_review: bool = False,
    ):
        package_path = Path(package)
        exported = self._transfer(package_path).export(
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
        return VersionedResultValidationService(self.repository, self.audit).validate_receipt(
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
