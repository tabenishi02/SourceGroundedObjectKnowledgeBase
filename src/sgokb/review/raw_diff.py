"""Raw-grounded Result v2 review while preserving v1 H-04 semantics."""

from __future__ import annotations

import copy
import json
from collections import defaultdict
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from sgokb.exchange.result_import import load_immutable_result_artifact
from sgokb.exchange.result_receipt import DEFAULT_INCOMING_ROOT
from sgokb.storage import MarkdownRenderReadRepository, PackageExchangeAuditRepository

from .diff import DiffReviewService, ObjectKnowledgeDiffEngine, ResultReviewReport


def _strip_grounding(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            key: _strip_grounding(item)
            for key, item in value.items()
            if key not in {"evidence", "grounding"}
        }
    if isinstance(value, list):
        return [_strip_grounding(item) for item in value]
    return copy.deepcopy(value)


def _normalized_refs(refs, kind: str):
    result = []
    for ref in refs or []:
        if kind == "raw":
            item = {
                "raw_artifact_id": ref.get("raw_artifact_id"),
                "role": ref.get("role"),
            }
            if ref.get("locator") is not None:
                item["locator"] = ref.get("locator")
        else:
            item = {"evidence_id": ref.get("evidence_id"), "role": ref.get("role")}
        result.append(item)
    return sorted(result, key=lambda item: json.dumps(item, sort_keys=True, ensure_ascii=False))


class RawDiffReviewService:
    def __init__(self, repository, audit: PackageExchangeAuditRepository | None = None):
        self.repository = repository
        self.audit = audit or PackageExchangeAuditRepository(repository.db)
        self.read_store = MarkdownRenderReadRepository(repository.db)
        self.engine = ObjectKnowledgeDiffEngine()
        self.legacy = DiffReviewService(repository, self.audit)

    def review_result(
        self,
        receipt_id: str,
        *,
        incoming_root: str | Path = DEFAULT_INCOMING_ROOT,
    ) -> ResultReviewReport:
        receipt = self.audit.result_receipt(receipt_id)
        if receipt is None:
            raise ValueError("Unknown Result receipt ID")
        if receipt["validation_state"] in {"pending", "running"}:
            raise ValueError("Result review requires completed validation")
        result, digest, _ = load_immutable_result_artifact(receipt, incoming_root)
        candidate = self.legacy._candidate_model(result)
        object_id = str((result.get("target") or {}).get("object_id"))
        base_version_id = (result.get("binding") or {}).get("base_version_id")
        current_version_id = self.repository.version_store.current_version_id(object_id)
        base = self.read_store.build_model(base_version_id) if base_version_id else None
        diff = self.engine.compare(
            _strip_grounding(base) if base is not None else None,
            _strip_grounding(candidate),
            before_version_id=base_version_id,
            after_version_id=None,
            after_kind="result_candidate",
        )
        diff.changes["grounding"] = self._grounding_changes(base_version_id, result)
        reasons = self.legacy._review_reasons(receipt, result, diff)
        imported = self.repository.db.execute(
            "SELECT version_id,review_acknowledged FROM object_result_imports WHERE receipt_id=?",
            (receipt_id,),
        ).fetchone()
        if imported:
            review_state = "imported"
        elif receipt["validation_state"] in {"invalid", "error"}:
            review_state = "blocked"
        elif any(item.severity == "review" for item in reasons):
            review_state = "review_required"
        else:
            review_state = "ready_to_import"
        return ResultReviewReport(
            receipt_id=receipt_id,
            package_id=str(receipt["package_id"]),
            object_id=object_id,
            validation_state=str(receipt["validation_state"]),
            review_state=review_state,
            base_version_id=base_version_id,
            current_version_id=current_version_id,
            result_status=result.get("result_status"),
            result_sha256=digest,
            reasons=tuple(reasons),
            diff=diff,
            imported_version_id=str(imported["version_id"]) if imported else None,
            review_acknowledged=bool(imported["review_acknowledged"]) if imported else None,
        )

    def _grounding_changes(self, base_version_id: str | None, result: Mapping[str, Any]):
        before = self._accepted_grounding(base_version_id) if base_version_id else {}
        after = self._result_grounding(result)
        changes = []
        for key in sorted(set(before) | set(after)):
            left = before.get(key)
            right = after.get(key)
            if left != right:
                changes.append({"key": key, "before": left, "after": right})
        return changes

    def _accepted_grounding(self, version_id: str) -> dict[str, Any]:
        result: dict[str, Any] = {}
        db = self.repository.db
        target_keys = self._target_keys(version_id)
        evidence: defaultdict[tuple[str, str], list[dict]] = defaultdict(list)
        for row in db.execute(
            """SELECT l.target_kind,l.target_id,l.evidence_id,r.key AS role
               FROM evidence_links l JOIN evidence_roles r ON r.id=l.role_id
               WHERE l.version_id=? ORDER BY l.rowid""",
            (version_id,),
        ):
            evidence[(row["target_kind"], row["target_id"])].append(
                {"evidence_id": row["evidence_id"], "role": row["role"]}
            )
        raw: defaultdict[tuple[str, str], list[dict]] = defaultdict(list)
        for row in db.execute(
            """SELECT target_kind,target_id,raw_artifact_id,role,locator_json
               FROM raw_grounding_links WHERE version_id=? ORDER BY rowid""",
            (version_id,),
        ):
            item = {"raw_artifact_id": row["raw_artifact_id"], "role": row["role"]}
            if row["locator_json"] is not None:
                item["locator"] = json.loads(row["locator_json"])
            raw[(row["target_kind"], row["target_id"])].append(item)
        for target, key in target_keys.items():
            if raw.get(target):
                result[key] = {"kind": "raw", "refs": _normalized_refs(raw[target], "raw")}
            elif evidence.get(target):
                result[key] = {
                    "kind": "evidence",
                    "refs": _normalized_refs(evidence[target], "evidence"),
                }
        return result

    def _target_keys(self, version_id: str):
        db = self.repository.db
        keys: dict[tuple[str, str], str] = {}
        for row in db.execute(
            "SELECT id,local_key FROM knowledge_statements WHERE version_id=?", (version_id,)
        ):
            keys[("statement", row["id"])] = f"statement:{row['local_key']}"
        for row in db.execute(
            """SELECT id,attribute_id,ordinal FROM object_version_attributes
               WHERE version_id=?""",
            (version_id,),
        ):
            keys[("attribute", row["id"])] = f"attribute:{row['attribute_id']}#{row['ordinal']}"
        for row in db.execute(
            """SELECT id,subject_object_id,relation_type_id,object_object_id
               FROM object_relations WHERE version_id=?""",
            (version_id,),
        ):
            keys[("relation", row["id"])] = (
                "relation:"
                + "|".join(
                    str(row[name])
                    for name in ("subject_object_id", "relation_type_id", "object_object_id")
                )
            )
        return keys

    @staticmethod
    def _result_grounding(result: Mapping[str, Any]) -> dict[str, Any]:
        output: dict[str, Any] = {}
        knowledge = result.get("knowledge") or {}
        for item in knowledge.get("summary", []):
            output[f"statement:{item['local_key']}"] = {
                "kind": "raw",
                "refs": _normalized_refs(item.get("grounding"), "raw"),
            }
        for facet in knowledge.get("facets", []):
            for item in facet.get("statements", []):
                output[f"statement:{item['local_key']}"] = {
                    "kind": "raw",
                    "refs": _normalized_refs(item.get("grounding"), "raw"),
                }
        counters: defaultdict[str, int] = defaultdict(int)
        for item in knowledge.get("attributes", []):
            attribute_id = str(item["attribute_id"])
            ordinal = counters[attribute_id]
            counters[attribute_id] += 1
            output[f"attribute:{attribute_id}#{ordinal}"] = {
                "kind": "raw",
                "refs": _normalized_refs(item.get("grounding"), "raw"),
            }
        for item in knowledge.get("relations", []):
            key = "relation:" + "|".join(
                str(item[name])
                for name in ("subject_object_id", "relation_type_id", "object_object_id")
            )
            output[key] = {"kind": "raw", "refs": _normalized_refs(item.get("grounding"), "raw")}
        return output
