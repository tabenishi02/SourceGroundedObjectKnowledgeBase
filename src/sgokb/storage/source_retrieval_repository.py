"""Source retrieval queries preserved across canonical Source repository extensions."""

from __future__ import annotations

import json
from typing import Iterable

from .source_repository import SourceRepository as CanonicalSourceRepository


class SourceRepository(CanonicalSourceRepository):
    """Canonical Source persistence plus the accepted F-03/J-02 retrieval contract."""

    def lexical_evidence_rows(
        self,
        query: str,
        *,
        source_ids: Iterable[str] | None = None,
        limit: int = 200,
    ) -> tuple[dict, ...]:
        query = query.strip()
        if not query:
            return ()
        if not 1 <= limit <= 5000:
            raise ValueError("Evidence lexical limit must be 1..5000")
        source_ids = tuple(dict.fromkeys(source_ids or ()))
        source_filter = ""
        parameters: list[object] = [query]
        if source_ids:
            placeholders = ",".join("?" for _ in source_ids)
            source_filter = f" AND er.source_id IN ({placeholders})"
            parameters.extend(source_ids)
        parameters.append(limit)
        rows = self.db.execute(
            """WITH latest_snapshot AS (
                   SELECT e.source_id,e.snapshot_id
                   FROM source_selection_events e
                   JOIN (
                     SELECT source_id,max(rowid) AS rid
                     FROM source_selection_events
                     WHERE selection_kind='snapshot'
                     GROUP BY source_id
                   ) x ON x.rid=e.rowid
               ), latest_run AS (
                   SELECT e.snapshot_id,e.run_id
                   FROM source_selection_events e
                   JOIN (
                     SELECT snapshot_id,max(rowid) AS rid
                     FROM source_selection_events
                     WHERE selection_kind='run'
                     GROUP BY snapshot_id
                   ) x ON x.rid=e.rowid
               )
               SELECT er.*,bm25(evidence_retrieval_fts) AS lexical_rank_score
               FROM evidence_retrieval_fts
               JOIN evidence_records er ON er.rowid=evidence_retrieval_fts.rowid
               JOIN latest_snapshot s
                 ON s.source_id=er.source_id AND s.snapshot_id=er.snapshot_id
               JOIN latest_run r
                 ON r.snapshot_id=er.snapshot_id AND r.run_id=er.run_id
               WHERE evidence_retrieval_fts MATCH ?"""
            + source_filter
            + " ORDER BY lexical_rank_score,er.id LIMIT ?",
            parameters,
        ).fetchall()
        return tuple(dict(row) for row in rows)

    def metadata_matching_sources(self, terms: Iterable[str]) -> dict[str, tuple[str, ...]]:
        normalized = tuple(
            dict.fromkeys(term.strip().casefold() for term in terms if term.strip())
        )
        if not normalized:
            return {}
        rows = self.db.execute(
            """WITH latest_snapshot AS (
                 SELECT e.source_id,e.snapshot_id
                 FROM source_selection_events e
                 JOIN (
                   SELECT source_id,max(rowid) AS rid
                   FROM source_selection_events
                   WHERE selection_kind='snapshot'
                   GROUP BY source_id
                 ) x ON x.rid=e.rowid
               )
               SELECT source_id,kind,value FROM (
                 SELECT id AS source_id,'source_label' AS kind,coalesce(label,'') AS value
                 FROM source_records WHERE status='active'
                 UNION ALL
                 SELECT source_id,'locator:' || kind,value
                 FROM source_locators WHERE status='active'
                 UNION ALL
                 SELECT c.source_id,'classification:' || c.axis,c.value
                 FROM source_classifications c
                 LEFT JOIN latest_snapshot s ON s.source_id=c.source_id
                 WHERE c.snapshot_id IS NULL OR c.snapshot_id=s.snapshot_id
                 UNION ALL
                 SELECT m.source_id,'metadata:' || m.key,m.value_json
                 FROM source_metadata_values m
                 LEFT JOIN latest_snapshot s ON s.source_id=m.source_id
                 WHERE m.snapshot_id IS NULL OR m.snapshot_id=s.snapshot_id
                 UNION ALL
                 SELECT ss.source_id,'snapshot_title',coalesce(ss.title,'')
                 FROM source_snapshots ss
                 JOIN latest_snapshot s
                   ON s.source_id=ss.source_id AND s.snapshot_id=ss.id
               )
               ORDER BY source_id,kind,value"""
        ).fetchall()
        matches: dict[str, list[str]] = {}
        for row in rows:
            value = row["value"].casefold()
            hit = next((term for term in normalized if term in value), None)
            if hit is not None:
                matches.setdefault(row["source_id"], []).append(f"{row['kind']}:{hit}")
        return {key: tuple(dict.fromkeys(values)) for key, values in matches.items()}

    def evidence_context(self, evidence_id: str) -> dict:
        row = self.db.execute(
            """SELECT er.*,ss.title AS snapshot_title,sr.label AS source_label
               FROM evidence_records er
               JOIN source_snapshots ss ON ss.id=er.snapshot_id
               JOIN source_records sr ON sr.id=er.source_id
               WHERE er.id=?""",
            (evidence_id,),
        ).fetchone()
        if not row:
            raise ValueError("Unknown evidence ID")
        locators = [
            {
                "kind": item["kind"],
                "value": item["value"],
                "preferred": bool(item["is_preferred"]),
            }
            for item in self.db.execute(
                """SELECT kind,value,is_preferred FROM source_locators
                   WHERE source_id=? AND status='active'
                   ORDER BY is_preferred DESC,rowid""",
                (row["source_id"],),
            )
        ]
        locations = [
            {
                "kind": item["kind"],
                "value": json.loads(item["value_json"]),
                "ordinal": item["ordinal"],
            }
            for item in self.db.execute(
                """SELECT kind,value_json,ordinal FROM evidence_locations
                   WHERE evidence_id=? ORDER BY ordinal,rowid""",
                (evidence_id,),
            )
        ]
        result = dict(row)
        result["metadata"] = json.loads(result.pop("metadata_json"))
        result["locators"] = locators
        result["locations"] = locations
        return result
