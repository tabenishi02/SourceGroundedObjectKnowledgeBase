"""Atomic import persistence for Raw-grounded Object Result v2."""

from __future__ import annotations

import copy
from collections.abc import Mapping
from typing import Any

from sgokb.exchange.object_result_v2 import iter_raw_grounding_refs

from .raw_grounding_repository import RawGroundingRepository
from .result_import_repository import ResultImportRepository


class RawResultImportRepository(ResultImportRepository):
    """Reuse canonical Knowledge writes while replacing Evidence links with Raw links."""

    def __init__(self, db):
        super().__init__(db)
        self.raw_store = RawGroundingRepository(db)

    def _validate_import_preconditions(
        self,
        receipt,
        package,
        result: Mapping[str, Any],
        *,
        artifact_sha256: str,
        artifact_byte_count: int,
        review_acknowledged: bool,
    ) -> None:
        super()._validate_import_preconditions(
            receipt,
            package,
            result,
            artifact_sha256=artifact_sha256,
            artifact_byte_count=artifact_byte_count,
            review_acknowledged=review_acknowledged,
        )
        if package["schema_version"] != "sgokb.object-evidence-package/2.0":
            raise ValueError("Raw Result import requires Package v2")
        if result.get("schema_version") != "sgokb.object-result/2.0":
            raise ValueError("Raw Result import requires Object Result v2")

        raw_audit = self.raw_store.package_grounding(str(package["package_id"]))
        if raw_audit is None:
            raise ValueError("Package v2 Raw grounding audit is missing")
        binding = result.get("binding") or {}
        if binding.get("grounding_contract") != raw_audit["grounding_contract"]:
            raise ValueError("Result Raw grounding contract does not match Package audit")
        if binding.get("grounding_set_sha256") != raw_audit["grounding_set_sha256"]:
            raise ValueError("Result grounding-set hash does not match Package audit")

        membership = set(raw_audit["included_raw_artifact_ids"])
        referenced: set[str] = set()
        for _path, reference in iter_raw_grounding_refs(result):
            raw_id = str(reference["raw_artifact_id"])
            referenced.add(raw_id)
            if raw_id not in membership:
                raise ValueError("Result references Raw Artifact outside its audited Package")
        if referenced:
            placeholders = ",".join("?" for _ in referenced)
            rows = self.db.execute(
                f"SELECT id FROM raw_artifacts WHERE id IN ({placeholders})",
                tuple(sorted(referenced)),
            ).fetchall()
            if {row["id"] for row in rows} != referenced:
                raise ValueError("Result references unknown canonical Raw Artifact")

    def _insert_knowledge(
        self,
        version_id: str,
        import_id: str,
        result: Mapping[str, Any],
        timestamp: str,
    ) -> None:
        """Adapt only the in-memory call shape expected by the v1 Knowledge writer.

        The temporary `evidence` key carries Raw refs only until `_insert_evidence_links`
        dispatches them to `raw_grounding_links`. No Evidence Link row is created.
        """
        adapted = copy.deepcopy(dict(result))
        knowledge = adapted["knowledge"]
        for statement in knowledge["summary"]:
            statement["evidence"] = statement.pop("grounding")
        for facet in knowledge["facets"]:
            for statement in facet["statements"]:
                statement["evidence"] = statement.pop("grounding")
        for item in knowledge["attributes"]:
            item["evidence"] = item.pop("grounding")
        for item in knowledge["relations"]:
            item["evidence"] = item.pop("grounding")
        super()._insert_knowledge(version_id, import_id, adapted, timestamp)

    def _insert_evidence_links(
        self,
        version_id: str,
        target_kind: str,
        target_id: str,
        references: list[Mapping[str, Any]],
        role_ids: Mapping[str, str],
        import_id: str,
        timestamp: str,
    ) -> None:
        del role_ids, timestamp
        row = self.db.execute(
            "SELECT package_id FROM object_result_imports WHERE id=?", (import_id,)
        ).fetchone()
        if not row:
            raise ValueError("Raw grounding import audit row is missing")
        package_id = str(row["package_id"])
        for reference in references:
            self.raw_store.link_raw_grounding(
                version_id,
                target_kind,
                target_id,
                package_id,
                reference,
                origin_ref=import_id,
            )
