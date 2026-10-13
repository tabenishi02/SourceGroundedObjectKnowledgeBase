"""Phase H / H-04 deterministic Object Knowledge diff and Result review preview."""

from __future__ import annotations

import copy
import json
from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable

from sgokb.exchange.result_import import load_immutable_result_artifact
from sgokb.exchange.result_receipt import DEFAULT_INCOMING_ROOT
from sgokb.storage import MarkdownRenderReadRepository, PackageExchangeAuditRepository

DIFF_SCHEMA_VERSION = "sgokb.object-diff/1.0"
REVIEW_SCHEMA_VERSION = "sgokb.result-review/1.0"


@dataclass(frozen=True, slots=True)
class ReviewReason:
    severity: str
    code: str
    message: str
    path: str | None = None
    source: str = "h04"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ObjectDiffReport:
    object_id: str
    before_version_id: str | None
    after_version_id: str | None
    after_kind: str
    changes: dict[str, Any]
    destructive_omissions: tuple[dict[str, Any], ...]

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["schema_version"] = DIFF_SCHEMA_VERSION
        return value


@dataclass(frozen=True, slots=True)
class ResultReviewReport:
    receipt_id: str
    package_id: str
    object_id: str
    validation_state: str
    review_state: str
    base_version_id: str | None
    current_version_id: str | None
    result_status: str | None
    result_sha256: str
    reasons: tuple[ReviewReason, ...]
    diff: ObjectDiffReport
    imported_version_id: str | None = None
    review_acknowledged: bool | None = None

    @property
    def requires_review(self) -> bool:
        return self.review_state == "review_required"

    @property
    def blocked(self) -> bool:
        return self.review_state == "blocked"

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["schema_version"] = REVIEW_SCHEMA_VERSION
        value["requires_review"] = self.requires_review
        value["blocked"] = self.blocked
        value["reasons"] = [item.to_dict() for item in self.reasons]
        value["diff"] = self.diff.to_dict()
        return value


def _normalized_evidence(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return []
    normalized = []
    for item in value:
        if not isinstance(item, Mapping):
            continue
        normalized.append(
            {
                "evidence_id": item.get("evidence_id"),
                "role": item.get("role"),
            }
        )
    return sorted(normalized, key=lambda item: (str(item["evidence_id"]), str(item["role"])))


def _normalized_scope(value: Any) -> Any:
    if not isinstance(value, Mapping):
        return value
    return {
        key: value[key]
        for key in ("as_of", "valid_from", "valid_to", "context_object_id", "label")
        if value.get(key) is not None
    }


def _statement_semantics(item: Mapping[str, Any]) -> dict[str, Any]:
    attribution = item.get("attribution")
    if isinstance(attribution, Mapping):
        attribution = {
            key: attribution.get(key)
            for key in ("kind", "source_id", "object_id", "label")
            if attribution.get(key) is not None
        }
    else:
        attribution = None
    return {
        "text": item.get("text"),
        "derivation_kind": item.get("derivation_kind"),
        "language": item.get("language"),
        "temporal_scope": _normalized_scope(item.get("temporal_scope")),
        "attribution": attribution,
        "evidence": _normalized_evidence(item.get("evidence")),
    }


def _attribute_semantics(item: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "attribute_id": item.get("attribute_id"),
        "ordinal": item.get("ordinal", 0),
        "status": item.get("status"),
        "value": item.get("value"),
        "language": item.get("language"),
        "temporal_scope": _normalized_scope(item.get("temporal_scope")),
        "evidence": _normalized_evidence(item.get("evidence")),
    }


def _relation_semantics(item: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "subject_object_id": item.get("subject_object_id"),
        "relation_type_id": item.get("relation_type_id"),
        "object_object_id": item.get("object_object_id"),
        "temporal_scope": _normalized_scope(item.get("temporal_scope")),
        "evidence": _normalized_evidence(item.get("evidence")),
    }


def _review_semantics(item: Mapping[str, Any]) -> dict[str, Any]:
    return copy.deepcopy(dict(item))


def _stable_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _identity_local_key(item: Mapping[str, Any]) -> str | None:
    value = item.get("local_key")
    return str(value) if value not in (None, "") else None


def _identity_attribute(item: Mapping[str, Any]) -> str:
    return f"{item.get('attribute_id')}#{item.get('ordinal', 0)}"


def _identity_relation(item: Mapping[str, Any]) -> str:
    return "|".join(
        str(item.get(key) or "")
        for key in ("subject_object_id", "relation_type_id", "object_object_id")
    )


def _entry_label(item: Mapping[str, Any], fallback: str) -> str:
    return str(
        item.get("local_key")
        or item.get("name")
        or item.get("key")
        or item.get("attribute_id")
        or item.get("relation_type_id")
        or item.get("text")
        or fallback
    )


def _diff_sequence(
    before: Sequence[Mapping[str, Any]],
    after: Sequence[Mapping[str, Any]],
    *,
    identity: Callable[[Mapping[str, Any]], str | None],
    semantics: Callable[[Mapping[str, Any]], dict[str, Any]],
    section: str,
    destructive_removed: bool,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    changes: list[dict[str, Any]] = []
    destructive: list[dict[str, Any]] = []
    before_left = set(range(len(before)))
    after_left = set(range(len(after)))

    before_by_key: defaultdict[str, list[int]] = defaultdict(list)
    after_by_key: defaultdict[str, list[int]] = defaultdict(list)
    for index, item in enumerate(before):
        key = identity(item)
        if key:
            before_by_key[key].append(index)
    for index, item in enumerate(after):
        key = identity(item)
        if key:
            after_by_key[key].append(index)

    for key in sorted(set(before_by_key) & set(after_by_key)):
        if len(before_by_key[key]) != 1 or len(after_by_key[key]) != 1:
            continue
        left = before_by_key[key][0]
        right = after_by_key[key][0]
        before_left.discard(left)
        after_left.discard(right)
        before_value = semantics(before[left])
        after_value = semantics(after[right])
        if before_value != after_value:
            changes.append(
                {
                    "change": "modified",
                    "key": key,
                    "before": before_value,
                    "after": after_value,
                }
            )

    # If a generator changed local keys but kept identical semantic content, avoid a
    # false destructive deletion by pairing exact semantic fingerprints next.
    semantic_before: defaultdict[str, list[int]] = defaultdict(list)
    semantic_after: defaultdict[str, list[int]] = defaultdict(list)
    for index in before_left:
        semantic_before[_stable_json(semantics(before[index]))].append(index)
    for index in after_left:
        semantic_after[_stable_json(semantics(after[index]))].append(index)
    for fingerprint in sorted(set(semantic_before) & set(semantic_after)):
        pairs = min(len(semantic_before[fingerprint]), len(semantic_after[fingerprint]))
        for offset in range(pairs):
            before_left.discard(semantic_before[fingerprint][offset])
            after_left.discard(semantic_after[fingerprint][offset])

    for index in sorted(before_left):
        item = semantics(before[index])
        entry = {
            "change": "removed",
            "key": identity(before[index]) or _entry_label(before[index], f"{section}:{index}"),
            "before": item,
            "after": None,
        }
        changes.append(entry)
        if destructive_removed:
            destructive_entry = dict(entry)
            destructive_entry["section"] = section
            destructive.append(destructive_entry)

    for index in sorted(after_left):
        changes.append(
            {
                "change": "added",
                "key": identity(after[index]) or _entry_label(after[index], f"{section}:{index}"),
                "before": None,
                "after": semantics(after[index]),
            }
        )
    return changes, destructive


class ObjectKnowledgeDiffEngine:
    """Compare full Object Knowledge snapshots without treating the diff as canonical data."""

    def compare(
        self,
        before: Mapping[str, Any] | None,
        after: Mapping[str, Any],
        *,
        before_version_id: str | None,
        after_version_id: str | None,
        after_kind: str,
    ) -> ObjectDiffReport:
        before_model = self._empty_model(after) if before is None else before
        before_id = self._object_id(before_model)
        after_id = self._object_id(after)
        if before_id != after_id:
            raise ValueError("Object Knowledge diff requires the same target Object")

        before_knowledge = before_model.get("knowledge") or {}
        after_knowledge = after.get("knowledge") or {}
        changes: dict[str, Any] = {}
        destructive: list[dict[str, Any]] = []

        summary_changes, summary_destructive = _diff_sequence(
            list(
                before_knowledge.get("summary_statements") or before_knowledge.get("summary") or []
            ),
            list(after_knowledge.get("summary_statements") or after_knowledge.get("summary") or []),
            identity=_identity_local_key,
            semantics=_statement_semantics,
            section="summary_statements",
            destructive_removed=True,
        )
        changes["summary_statements"] = summary_changes
        destructive.extend(summary_destructive)

        facet_changes, facet_destructive = self._diff_facets(
            list(before_knowledge.get("facets") or []),
            list(after_knowledge.get("facets") or []),
        )
        changes["facets"] = facet_changes
        destructive.extend(facet_destructive)

        before_attributes = self._with_attribute_ordinals(before_knowledge.get("attributes") or [])
        after_attributes = self._with_attribute_ordinals(after_knowledge.get("attributes") or [])
        attribute_changes, attribute_destructive = _diff_sequence(
            before_attributes,
            after_attributes,
            identity=_identity_attribute,
            semantics=_attribute_semantics,
            section="attributes",
            destructive_removed=True,
        )
        changes["attributes"] = attribute_changes
        destructive.extend(attribute_destructive)

        relation_changes, relation_destructive = _diff_sequence(
            list(before_knowledge.get("relations") or []),
            list(after_knowledge.get("relations") or []),
            identity=_identity_relation,
            semantics=_relation_semantics,
            section="relations",
            destructive_removed=True,
        )
        changes["relations"] = relation_changes
        destructive.extend(relation_destructive)

        before_review = before_model.get("review") or {}
        after_review = after.get("review") or {}
        review_changes: dict[str, list[dict[str, Any]]] = {}
        for collection in ("conflicts", "gaps", "unresolved_references", "registry_proposals"):
            collection_changes, collection_removed = _diff_sequence(
                list(before_review.get(collection) or []),
                list(after_review.get(collection) or []),
                identity=_identity_local_key,
                semantics=_review_semantics,
                section=collection,
                destructive_removed=collection in {"conflicts", "registry_proposals"},
            )
            review_changes[collection] = collection_changes
            destructive.extend(collection_removed)
        changes["review_metadata"] = review_changes

        return ObjectDiffReport(
            object_id=after_id,
            before_version_id=before_version_id,
            after_version_id=after_version_id,
            after_kind=after_kind,
            changes=changes,
            destructive_omissions=tuple(destructive),
        )

    def _diff_facets(
        self,
        before: list[Mapping[str, Any]],
        after: list[Mapping[str, Any]],
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        before_by_id = {str(item.get("facet_id")): item for item in before}
        after_by_id = {str(item.get("facet_id")): item for item in after}
        changes: list[dict[str, Any]] = []
        destructive: list[dict[str, Any]] = []
        for facet_id in sorted(set(before_by_id) | set(after_by_id)):
            left = before_by_id.get(facet_id)
            right = after_by_id.get(facet_id)
            if left is None:
                changes.append(
                    {
                        "facet_id": facet_id,
                        "change": "added",
                        "before_status": None,
                        "after_status": right.get("status"),
                        "statements": [],
                    }
                )
                continue
            if right is None:
                entry = {
                    "facet_id": facet_id,
                    "change": "removed",
                    "before_status": left.get("status"),
                    "after_status": None,
                    "statements": [],
                }
                changes.append(entry)
                destructive.append(dict(entry, section="facets"))
                continue

            statement_changes, statement_destructive = _diff_sequence(
                list(left.get("statements") or []),
                list(right.get("statements") or []),
                identity=_identity_local_key,
                semantics=_statement_semantics,
                section=f"facet:{facet_id}:statements",
                destructive_removed=True,
            )
            before_status = left.get("status")
            after_status = right.get("status")
            status_changed = before_status != after_status
            if status_changed or statement_changes:
                entry = {
                    "facet_id": facet_id,
                    "change": "modified",
                    "before_status": before_status,
                    "after_status": after_status,
                    "statements": statement_changes,
                }
                changes.append(entry)
                if before_status == "content" and after_status != "content":
                    destructive.append(
                        {
                            "section": "facets",
                            "change": "content_downgraded",
                            "key": facet_id,
                            "before": {"status": before_status},
                            "after": {"status": after_status},
                        }
                    )
            destructive.extend(statement_destructive)
        return changes, destructive

    @staticmethod
    def _with_attribute_ordinals(items: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
        counters: defaultdict[str, int] = defaultdict(int)
        result: list[dict[str, Any]] = []
        for raw in items:
            item = dict(raw)
            attribute_id = str(item.get("attribute_id"))
            if item.get("ordinal") is None:
                item["ordinal"] = counters[attribute_id]
            counters[attribute_id] = max(counters[attribute_id], int(item["ordinal"]) + 1)
            result.append(item)
        return result

    @staticmethod
    def _object_id(model: Mapping[str, Any]) -> str:
        if isinstance(model.get("object"), Mapping):
            return str(model["object"]["object_id"])
        return str(model["object_id"])

    @staticmethod
    def _empty_model(after: Mapping[str, Any]) -> dict[str, Any]:
        object_id = ObjectKnowledgeDiffEngine._object_id(after)
        return {
            "object": {"object_id": object_id},
            "knowledge": {
                "summary_statements": [],
                "facets": [],
                "attributes": [],
                "relations": [],
            },
            "review": {
                "conflicts": [],
                "gaps": [],
                "unresolved_references": [],
                "registry_proposals": [],
            },
        }


class DiffReviewService:
    """Read-only H-04 review material for immutable Result receipts and accepted Versions."""

    def __init__(self, repository, audit: PackageExchangeAuditRepository | None = None):
        self.repository = repository
        self.audit = audit or PackageExchangeAuditRepository(repository.db)
        self.read_store = MarkdownRenderReadRepository(repository.db)
        self.engine = ObjectKnowledgeDiffEngine()

    def diff_versions(self, before_version_id: str, after_version_id: str) -> ObjectDiffReport:
        before = self.read_store.build_model(before_version_id)
        after = self.read_store.build_model(after_version_id)
        return self.engine.compare(
            before,
            after,
            before_version_id=before_version_id,
            after_version_id=after_version_id,
            after_kind="accepted_version",
        )

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
            raise ValueError("Result review requires completed H-01 validation")

        result, digest, _ = load_immutable_result_artifact(receipt, incoming_root)
        candidate = self._candidate_model(result)
        object_id = str((result.get("target") or {}).get("object_id"))
        base_version_id = (result.get("binding") or {}).get("base_version_id")
        current_version_id = self.repository.version_store.current_version_id(object_id)
        base = self.read_store.build_model(base_version_id) if base_version_id else None
        diff = self.engine.compare(
            base,
            candidate,
            before_version_id=base_version_id,
            after_version_id=None,
            after_kind="result_candidate",
        )

        reasons = self._review_reasons(receipt, result, diff)
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

    def _review_reasons(
        self,
        receipt: Mapping[str, Any],
        result: Mapping[str, Any],
        diff: ObjectDiffReport,
    ) -> list[ReviewReason]:
        reasons: list[ReviewReason] = []
        for finding in receipt.get("validation_findings", []):
            severity = "review" if finding.get("severity") == "review" else "blocked"
            reasons.append(
                ReviewReason(
                    severity=severity,
                    code=str(finding.get("code", "validation_finding")),
                    message=str(finding.get("message", "Validation finding")),
                    path=finding.get("path"),
                    source="h01_validation",
                )
            )

        if diff.destructive_omissions:
            sections = sorted({str(item.get("section")) for item in diff.destructive_omissions})
            reasons.append(
                ReviewReason(
                    severity="review",
                    code="destructive_omission",
                    message="Full snapshot removes or downgrades prior content: "
                    + ", ".join(sections),
                    source="h04_diff",
                )
            )

        conflicts = result.get("conflicts") or []
        if conflicts:
            reasons.append(
                ReviewReason(
                    severity="attention",
                    code="conflicts_present",
                    message=(
                        f"Result preserves {len(conflicts)} conflict item(s); "
                        "conflicts do not alone block import"
                    ),
                    source="h04_review",
                )
            )

        return self._dedupe_reasons(reasons)

    @staticmethod
    def _candidate_model(result: Mapping[str, Any]) -> dict[str, Any]:
        target = result.get("target") or {}
        binding = result.get("binding") or {}
        knowledge = copy.deepcopy(result.get("knowledge") or {})
        return {
            "schema_version": "sgokb.h04-candidate-model/1.0",
            "canonical": False,
            "object": {"object_id": target.get("object_id")},
            "version": {
                "version_id": None,
                "base_version_id": binding.get("base_version_id"),
                "classification": {
                    "primary_class_id": target.get("primary_class_id"),
                    "additional_class_ids": list(target.get("additional_class_ids") or []),
                },
            },
            "knowledge": {
                "default_language": knowledge.get("default_language"),
                "summary_statements": list(knowledge.get("summary") or []),
                "facets": list(knowledge.get("facets") or []),
                "attributes": list(knowledge.get("attributes") or []),
                "relations": list(knowledge.get("relations") or []),
            },
            "review": {
                "result_status": result.get("result_status"),
                "conflicts": list(result.get("conflicts") or []),
                "gaps": list(result.get("gaps") or []),
                "unresolved_references": list(result.get("unresolved_references") or []),
                "registry_proposals": list(result.get("registry_proposals") or []),
                "class_extensions": list(result.get("class_extensions") or []),
            },
            "generation": copy.deepcopy(result.get("generation") or {}),
        }

    @staticmethod
    def _dedupe_reasons(reasons: list[ReviewReason]) -> list[ReviewReason]:
        result: list[ReviewReason] = []
        seen: set[tuple[str, str, str | None]] = set()
        for item in reasons:
            key = (item.severity, item.code, item.path)
            if key not in seen:
                seen.add(key)
                result.append(item)
        rank = {"blocked": 0, "review": 1, "attention": 2}
        return sorted(
            result, key=lambda item: (rank.get(item.severity, 9), item.code, item.path or "")
        )
