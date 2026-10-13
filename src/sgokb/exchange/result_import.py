"""Phase H / H-02 explicit import of validated Object Result receipts."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from sgokb.storage import PackageExchangeAuditRepository, ResultImportRepository

from .result_receipt import DEFAULT_INCOMING_ROOT, RESULT_FILENAME


@dataclass(frozen=True, slots=True)
class ObjectVersionImportResult:
    import_id: str
    receipt_id: str
    package_id: str
    version_id: str
    object_id: str
    base_version_id: str | None
    result_sha256: str
    result_status: str
    review_acknowledged: bool
    imported_at: str
    duplicate: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def load_immutable_result_artifact(
    receipt: Mapping[str, Any], incoming_root: str | Path
) -> tuple[Mapping[str, Any], str, int]:
    """Read an audited Result receipt without allowing path/hash drift."""

    root = Path(incoming_root).resolve()
    storage_ref = Path(str(receipt["storage_ref"]))
    if storage_ref.is_absolute() or ".." in storage_ref.parts:
        raise ValueError("Receipt storage reference is not a safe incoming-root relative path")
    path = (root / storage_ref).resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise ValueError("Receipt storage reference escapes the incoming root") from exc
    if path.name != RESULT_FILENAME or path.is_symlink() or not path.is_file():
        raise ValueError("Immutable receipt result.json is missing or is not a regular file")
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if len(raw) != int(receipt["byte_count"]):
        raise ValueError("Immutable Result byte count no longer matches receipt audit")
    if digest != receipt["result_sha256"]:
        raise ValueError("Immutable Result SHA-256 no longer matches receipt audit")
    try:
        parsed = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("Previously validated Result artifact can no longer be parsed") from exc
    if not isinstance(parsed, Mapping):
        raise ValueError("Object Result top level must be a JSON object")
    return parsed, digest, len(raw)


class ObjectVersionImportService:
    """Turn one H-01-valid immutable receipt into one accepted Object Version."""

    def __init__(
        self,
        repository,
        audit: PackageExchangeAuditRepository | None = None,
        *,
        failure_hook: Callable[[str], None] | None = None,
    ):
        self.repository = repository
        self.audit = audit or PackageExchangeAuditRepository(repository.db)
        self.import_store = ResultImportRepository(repository.db)
        self.failure_hook = failure_hook

    def import_receipt(
        self,
        receipt_id: str,
        *,
        incoming_root: str | Path = DEFAULT_INCOMING_ROOT,
        acknowledge_review: bool = False,
    ) -> ObjectVersionImportResult:
        existing = self.import_store.import_by_receipt(receipt_id)
        if existing is not None:
            return self._result(existing, duplicate=True)

        receipt = self.audit.result_receipt(receipt_id)
        if receipt is None:
            raise ValueError("Unknown Result receipt ID")
        if receipt["validation_state"] != "valid":
            raise ValueError("Object Result import requires successful H-01 validation")

        # H-04 adds deterministic review reasons such as destructive full-snapshot
        # omissions. Recompute them immediately before Import so a review preview cannot
        # be acknowledged against an older current Version and then silently drift.
        from sgokb.review.diff import DiffReviewService

        review = DiffReviewService(self.repository, self.audit).review_result(
            receipt_id,
            incoming_root=incoming_root,
        )
        if review.blocked:
            raise ValueError("Object Result import is blocked by H-04 review")
        if review.requires_review and not acknowledge_review:
            raise ValueError("Object Result import requires explicit review acknowledgement")

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

    @staticmethod
    def _result(row: Mapping[str, Any], *, duplicate: bool) -> ObjectVersionImportResult:
        return ObjectVersionImportResult(
            import_id=str(row["id"]),
            receipt_id=str(row["receipt_id"]),
            package_id=str(row["package_id"]),
            version_id=str(row["version_id"]),
            object_id=str(row["object_id"]),
            base_version_id=row["base_version_id"],
            result_sha256=str(row["result_sha256"]),
            result_status=str(row["result_status"]),
            review_acknowledged=bool(row["review_acknowledged"]),
            imported_at=str(row["imported_at"]),
            duplicate=duplicate,
        )

    @staticmethod
    def _load_immutable_result(
        receipt: Mapping[str, Any], incoming_root: str | Path
    ) -> tuple[Mapping[str, Any], str, int]:
        """Compatibility wrapper for the shared immutable Result artifact loader."""

        return load_immutable_result_artifact(receipt, incoming_root)
