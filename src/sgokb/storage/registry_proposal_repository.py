"""Persistence for Phase M Registry proposal review/apply operations."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from hashlib import sha256

from sgokb.domain.object import new_persistent_id


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _proposal_ref(version_id: str, local_key: str) -> str:
    return f"{version_id}:{local_key}"


class RegistryProposalRepository:
    """Review Object Result registry proposals and apply only accepted proposals."""

    def __init__(self, db: sqlite3.Connection):
        self.db = db

    def _version_proposals(self) -> list[dict]:
        rows = self.db.execute(
            """SELECT m.version_id,m.registry_proposals_json,v.object_id
               FROM object_version_result_metadata m
               JOIN object_versions v ON v.id=m.version_id
               ORDER BY m.version_id"""
        ).fetchall()
        output: list[dict] = []
        for row in rows:
            proposals = json.loads(row["registry_proposals_json"])
            for item in proposals:
                local_key = str(item["local_key"])
                output.append(
                    {
                        "proposal_ref": _proposal_ref(row["version_id"], local_key),
                        "version_id": row["version_id"],
                        "object_id": row["object_id"],
                        **item,
                    }
                )
        return output

    def list_proposals(self, *, decision: str | None = None) -> list[dict]:
        reviews = {
            row["proposal_ref"]: dict(row)
            for row in self.db.execute(
                "SELECT * FROM registry_proposal_reviews ORDER BY decided_at,proposal_ref"
            )
        }
        output = []
        for proposal in self._version_proposals():
            review = reviews.get(proposal["proposal_ref"])
            item = dict(proposal)
            item["decision"] = review["decision"] if review else "pending"
            item["review_note"] = review["review_note"] if review else None
            item["decided_at"] = review["decided_at"] if review else None
            item["applied_at"] = review["applied_at"] if review else None
            item["applied_result"] = (
                json.loads(review["applied_result_json"])
                if review and review["applied_result_json"]
                else None
            )
            if decision is None or item["decision"] == decision:
                output.append(item)
        return output

    def proposal(self, proposal_ref: str) -> dict:
        matches = [item for item in self.list_proposals() if item["proposal_ref"] == proposal_ref]
        if not matches:
            raise ValueError("Unknown Registry proposal reference")
        return matches[0]

    def decide(self, proposal_ref: str, decision: str, *, note: str = "") -> dict:
        if decision not in {"accepted", "rejected"}:
            raise ValueError("Registry proposal decision must be accepted or rejected")
        proposal = self.proposal(proposal_ref)
        payload_json = _json(proposal["payload"])
        proposal_hash = sha256(
            _json(
                {
                    "proposal_kind": proposal["proposal_kind"],
                    "rationale": proposal["rationale"],
                    "payload": proposal["payload"],
                    "evidence": proposal["evidence"],
                }
            ).encode("utf-8")
        ).hexdigest()
        existing = self.db.execute(
            "SELECT * FROM registry_proposal_reviews WHERE proposal_ref=?", (proposal_ref,)
        ).fetchone()
        if existing and existing["applied_at"] is not None:
            raise ValueError("Applied Registry proposal decision is immutable")
        timestamp = _now()
        with self.db:
            self.db.execute(
                """INSERT INTO registry_proposal_reviews
                   (proposal_ref,version_id,local_key,proposal_kind,payload_json,proposal_hash,
                    decision,review_note,decided_at,applied_at,applied_result_json)
                   VALUES(?,?,?,?,?,?,?,?,?,NULL,NULL)
                   ON CONFLICT(proposal_ref) DO UPDATE SET
                     proposal_kind=excluded.proposal_kind,
                     payload_json=excluded.payload_json,
                     proposal_hash=excluded.proposal_hash,
                     decision=excluded.decision,
                     review_note=excluded.review_note,
                     decided_at=excluded.decided_at""",
                (
                    proposal_ref,
                    proposal["version_id"],
                    proposal["local_key"],
                    proposal["proposal_kind"],
                    payload_json,
                    proposal_hash,
                    decision,
                    note,
                    timestamp,
                ),
            )
        return self.proposal(proposal_ref)

    def _object_event(self, object_id: str, event_type: str, payload: dict, timestamp: str) -> None:
        self.db.execute(
            "INSERT INTO object_registry_events VALUES(?,?,?,?,?)",
            (new_persistent_id(), object_id, event_type, _json(payload), timestamp),
        )

    @staticmethod
    def _require(payload: dict, name: str):
        if name not in payload:
            raise ValueError(f"Registry proposal payload requires {name!r}")
        return payload[name]

    def apply(self, proposal_ref: str) -> dict:
        proposal = self.proposal(proposal_ref)
        review = self.db.execute(
            "SELECT * FROM registry_proposal_reviews WHERE proposal_ref=?", (proposal_ref,)
        ).fetchone()
        if not review or review["decision"] != "accepted":
            raise ValueError("Registry proposal must be explicitly accepted before apply")
        if review["applied_at"] is not None:
            return {
                "proposal_ref": proposal_ref,
                "duplicate": True,
                "result": json.loads(review["applied_result_json"]),
            }

        payload = proposal["payload"]
        kind = proposal["proposal_kind"]
        timestamp = _now()
        object_id = proposal["object_id"]
        result: dict[str, object]

        self.db.execute("BEGIN IMMEDIATE")
        try:
            if kind == "object_name":
                name = str(self._require(payload, "name")).strip()
                if not name:
                    raise ValueError("Object name proposal cannot be empty")
                self.db.execute(
                    "UPDATE objects SET name=?,updated_at=? WHERE id=?",
                    (name, timestamp, object_id),
                )
                self._object_event(
                    object_id, "name_changed_by_registry_proposal", {"after": name}, timestamp
                )
                result = {"object_id": object_id, "name": name}

            elif kind == "object_alias":
                value = str(self._require(payload, "value")).strip()
                if not value:
                    raise ValueError("Object alias proposal cannot be empty")
                alias_id = new_persistent_id()
                self.db.execute(
                    "INSERT INTO object_aliases VALUES(?,?,?,?,?,?)",
                    (
                        alias_id,
                        object_id,
                        value,
                        payload.get("language"),
                        str(payload.get("kind", "alias")),
                        timestamp,
                    ),
                )
                self.db.execute(
                    "UPDATE objects SET updated_at=? WHERE id=?", (timestamp, object_id)
                )
                self._object_event(
                    object_id,
                    "alias_added_by_registry_proposal",
                    {"alias_id": alias_id, "value": value},
                    timestamp,
                )
                result = {"object_id": object_id, "alias_id": alias_id}

            elif kind == "primary_class":
                class_id = str(self._require(payload, "class_id"))
                self.db.execute(
                    "UPDATE objects SET primary_class_id=?,updated_at=? WHERE id=?",
                    (class_id, timestamp, object_id),
                )
                self._object_event(
                    object_id,
                    "primary_class_changed_by_registry_proposal",
                    {"after": class_id},
                    timestamp,
                )
                result = {"object_id": object_id, "primary_class_id": class_id}

            elif kind == "additional_class":
                class_id = str(self._require(payload, "class_id"))
                action = str(payload.get("action", "add"))
                if action == "add":
                    self.db.execute(
                        "INSERT INTO object_additional_classes VALUES(?,?,?)",
                        (object_id, class_id, timestamp),
                    )
                elif action == "remove":
                    cursor = self.db.execute(
                        "DELETE FROM object_additional_classes WHERE object_id=? AND class_id=?",
                        (object_id, class_id),
                    )
                    if cursor.rowcount == 0:
                        raise ValueError("Additional Class proposal target is not assigned")
                else:
                    raise ValueError("additional_class action must be add or remove")
                self.db.execute(
                    "UPDATE objects SET updated_at=? WHERE id=?", (timestamp, object_id)
                )
                self._object_event(
                    object_id,
                    f"additional_class_{action}_by_registry_proposal",
                    {"class_id": class_id},
                    timestamp,
                )
                result = {"object_id": object_id, "class_id": class_id, "action": action}

            elif kind == "new_class":
                key = str(self._require(payload, "key")).strip()
                name = str(self._require(payload, "name")).strip()
                policy = str(self._require(payload, "assignment_policy"))
                class_id = str(payload.get("class_id") or f"class:{key}")
                self.db.execute(
                    "INSERT INTO object_classes VALUES(?,?,?,?,?,?,?,?)",
                    (
                        class_id,
                        key,
                        name,
                        str(payload.get("description", "")),
                        policy,
                        "active",
                        timestamp,
                        timestamp,
                    ),
                )
                for parent_id in payload.get("parent_class_ids", []):
                    self.db.execute(
                        "INSERT INTO object_class_parents VALUES(?,?,?)",
                        (class_id, str(parent_id), timestamp),
                    )
                result = {"class_id": class_id, "key": key}

            elif kind == "new_facet":
                key = str(self._require(payload, "key")).strip()
                name = str(self._require(payload, "name")).strip()
                facet_id = str(payload.get("facet_id") or f"facet:{key}")
                self.db.execute(
                    "INSERT INTO facet_definitions VALUES(?,?,?,?,?,?,?,?)",
                    (
                        facet_id,
                        key,
                        name,
                        str(payload.get("description", "")),
                        int(bool(payload.get("is_common", False))),
                        "active",
                        timestamp,
                        timestamp,
                    ),
                )
                for profile in payload.get("class_profiles", []):
                    self.db.execute(
                        "INSERT INTO class_facet_profiles VALUES(?,?,?,?,?)",
                        (
                            str(self._require(profile, "class_id")),
                            facet_id,
                            int(profile.get("position", 0)),
                            int(bool(profile.get("inherit_to_descendants", True))),
                            timestamp,
                        ),
                    )
                result = {"facet_id": facet_id, "key": key}

            elif kind == "new_attribute":
                key = str(self._require(payload, "key")).strip()
                name = str(self._require(payload, "name")).strip()
                value_type = str(self._require(payload, "value_type"))
                attribute_id = str(payload.get("attribute_id") or f"attribute:{key}")
                self.db.execute(
                    "INSERT INTO attribute_definitions VALUES(?,?,?,?,?,?,?,?)",
                    (
                        attribute_id,
                        key,
                        name,
                        str(payload.get("description", "")),
                        value_type,
                        "active",
                        timestamp,
                        timestamp,
                    ),
                )
                result = {"attribute_id": attribute_id, "key": key}

            elif kind == "new_relation_type":
                key = str(self._require(payload, "key")).strip()
                name = str(self._require(payload, "name")).strip()
                relation_type_id = str(payload.get("relation_type_id") or f"relation:{key}")
                self.db.execute(
                    "INSERT INTO relation_types VALUES(?,?,?,?,?,?,?)",
                    (
                        relation_type_id,
                        key,
                        name,
                        str(payload.get("description", "")),
                        "active",
                        timestamp,
                        timestamp,
                    ),
                )
                result = {"relation_type_id": relation_type_id, "key": key}
            else:
                raise ValueError(f"Unsupported Registry proposal kind: {kind}")

            self.db.execute(
                """UPDATE registry_proposal_reviews
                   SET applied_at=?,applied_result_json=? WHERE proposal_ref=?""",
                (timestamp, _json(result), proposal_ref),
            )
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        return {"proposal_ref": proposal_ref, "duplicate": False, "result": result}
