"""All SQL lives here; immutable generations and transactional promotion of active data."""

import json
import sqlite3
from pathlib import Path

from .domain import digest, json_text, now, uid
from .knowledge_repository import KnowledgeRepository


class Repository(KnowledgeRepository):
    def __init__(self, path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA busy_timeout=5000")
        self.migrate()

    def close(self):
        self.db.close()

    def migrate(self):
        self.db.execute("CREATE TABLE IF NOT EXISTS schema_migrations(version INTEGER PRIMARY KEY)")
        self.db.commit()
        for file in sorted(Path(__file__).with_name("migrations").glob("*.sql")):
            version = int(file.name.split("_")[0])
            if not self.db.execute(
                "SELECT 1 FROM schema_migrations WHERE version=?", (version,)
            ).fetchone():
                try:
                    self.db.executescript(
                        "BEGIN;\n"
                        + file.read_text(encoding="utf-8")
                        + f"\nINSERT INTO schema_migrations VALUES({version});\nCOMMIT;"
                    )
                except Exception:
                    self.db.rollback()
                    raise

    def one(self, sql, parameters=()):
        result = self.db.execute(sql, parameters).fetchone()
        return dict(result) if result else None

    def rows(self, sql, parameters=()):
        return [dict(row) for row in self.db.execute(sql, parameters)]

    def import_bundle(self, bundle, site, source_type):
        manifest = bundle.manifest
        snapshot_id = manifest["capture_id"]
        existing = self.snapshot(snapshot_id)
        if existing:
            if existing["raw_sha256"] != bundle.sha256:
                raise ValueError("Existing capture_id has different raw bytes")
            return {"snapshot": snapshot_id, "duplicate": True}
        with self.db:
            source = self.one("SELECT id FROM sources WHERE url=?", (manifest["page"]["url"],))
            source_id = source["id"] if source else uid()
            if not source:
                self.db.execute(
                    "INSERT INTO sources VALUES(?,?,?,?,?)",
                    (source_id, manifest["page"]["url"], site, source_type, now()),
                )
            self.db.execute(
                "INSERT INTO snapshots VALUES(?,?,?,?,?,?,?,?,?,NULL)",
                (
                    snapshot_id,
                    source_id,
                    manifest["page"]["title"],
                    manifest["captured_at"],
                    bundle.path,
                    bundle.sha256,
                    json_text(manifest),
                    json_text(bundle.metadata),
                    now(),
                ),
            )
            self.db.executemany(
                "INSERT INTO artifacts VALUES(?,?,?,?)",
                [
                    (snapshot_id, name, digest(value), len(value))
                    for name, value in bundle.artifacts.items()
                ],
            )
        return {"snapshot": snapshot_id, "source": source_id, "duplicate": False}

    def snapshot(self, snapshot_id):
        return self.one(
            "SELECT n.*, s.url, s.site, s.source_type FROM snapshots n "
            "JOIN sources s ON s.id=n.source_id WHERE n.id=?",
            (snapshot_id,),
        )

    def snapshots(self):
        return self.rows(
            "SELECT n.*, s.url, s.site, s.source_type FROM snapshots n "
            "JOIN sources s ON s.id=n.source_id ORDER BY captured_at,id"
        )

    def save_normalized(self, snapshot, blocks, evidence, configuration, context=None):
        run_id = uid()
        with self.db:
            self.db.execute(
                "INSERT INTO normalized_runs VALUES(?,?,?,?,?)",
                (run_id, snapshot["id"], json_text(configuration), json_text(blocks), now()),
            )
            for item in evidence:
                evidence_id = uid()
                self.db.execute(
                    "INSERT INTO evidence VALUES(?,?,?,?,?,?,?,?)",
                    (
                        evidence_id,
                        run_id,
                        snapshot["source_id"],
                        snapshot["id"],
                        item["content"],
                        json_text(item),
                        digest(item["content"]),
                        now(),
                    ),
                )
                self.db.execute(
                    "INSERT INTO search_items(kind,target_id,content) VALUES(?,?,?)",
                    ("evidence", evidence_id, item["content"]),
                )
            if context is not None:
                self._insert_context(run_id, snapshot["id"], context, {}, {})
            self.db.execute(
                "UPDATE snapshots SET active_run=? WHERE id=?", (run_id, snapshot["id"])
            )
        return run_id

    def evidence(self, snapshot_id):
        return self.rows(
            "SELECT e.* FROM evidence e JOIN snapshots s ON s.active_run=e.run_id "
            "WHERE s.id=? ORDER BY e.rowid",
            (snapshot_id,),
        )

    def entity(self, entity_id):
        value = self.one("SELECT * FROM entities WHERE id=?", (entity_id,))
        if not value:
            raise ValueError("Unknown entity ID; use entity list")
        value["aliases"] = json.loads(value["aliases"])
        return value

    def add_entity(self, kind, name, aliases=()):
        if not kind.strip() or not name.strip():
            raise ValueError("Entity type and name required")
        existing = self.one("SELECT id FROM entities WHERE type=? AND name=?", (kind, name))
        if existing:
            return existing["id"]
        entity_id = uid()
        with self.db:
            self.db.execute(
                "INSERT INTO entities VALUES(?,?,?,?,?)",
                (entity_id, kind, name, json_text(list(aliases)), now()),
            )
        return entity_id

    def entities(self):
        return self.rows("SELECT * FROM entities ORDER BY type,name")

    def relate(self, subject, predicate, object_id):
        with self.db:
            self.db.execute(
                "INSERT OR IGNORE INTO entity_relations VALUES(?,?,?,?)",
                (subject, predicate, object_id, json_text({"origin": "user"})),
            )

    def link_evidence(self, entity_id, evidence_ids):
        with self.db:
            self.db.executemany(
                "INSERT OR IGNORE INTO entity_evidence VALUES(?,?)",
                [(entity_id, eid) for eid in evidence_ids],
            )

    def begin_ai(self, task, model, revision, prompt, version, payload):
        ai_id = uid()
        with self.db:
            self.db.execute(
                "INSERT INTO ai_runs VALUES(?,?,?,?,?,?,?,NULL,?,?,NULL)",
                (
                    ai_id,
                    task,
                    model,
                    revision,
                    prompt,
                    version,
                    json_text(payload),
                    now(),
                    "running",
                ),
            )
        return ai_id

    def finish_ai(self, ai_id, output=None, error=None):
        with self.db:
            self.db.execute(
                "UPDATE ai_runs SET output=coalesce(?,output),status=?,error=? WHERE id=?",
                (output, "failed" if error else "success", error, ai_id),
            )

    def save_fragments(self, snapshot, entity_id, items, ai_id, configuration):
        with self.db:
            ids, _ = self._insert_fragment_generation(
                snapshot, entity_id, items, ai_id, configuration
            )
        return ids

    def _insert_fragment_generation(self, snapshot, entity_id, items, ai_id, configuration):
        run_id = uid()
        self.db.execute(
            "UPDATE fragment_runs SET active=0 WHERE snapshot_id=? AND entity_id=?",
            (snapshot["id"], entity_id),
        )
        self.db.execute(
            "INSERT INTO fragment_runs VALUES(?,?,?,?,?,?,1,?)",
            (
                run_id,
                snapshot["active_run"],
                snapshot["id"],
                entity_id,
                ai_id,
                json_text(configuration),
                now(),
            ),
        )
        ids = []
        for item in items:
            fragment_id = uid()
            ids.append(fragment_id)
            self.db.execute(
                "INSERT INTO fragments VALUES(?,?,?,?,?,?,?,?)",
                (
                    fragment_id,
                    run_id,
                    entity_id,
                    item["facet"],
                    item["content"],
                    json_text(item),
                    digest(item["content"]),
                    now(),
                ),
            )
            self.db.executemany(
                "INSERT INTO fragment_evidence VALUES(?,?)",
                [(fragment_id, e) for e in set(item["evidence_ids"])],
            )
            self.db.executemany(
                "INSERT OR IGNORE INTO entity_evidence VALUES(?,?)",
                [(entity_id, e) for e in set(item["evidence_ids"])],
            )
            self.db.execute(
                "INSERT INTO search_items(kind,target_id,content) VALUES(?,?,?)",
                ("fragment", fragment_id, item["content"]),
            )
        return ids, run_id

    def candidates(self, filters):
        # Active generations only; filtering happens before lexical/vector candidate limits.
        sql = """SELECT i.id AS item_id, i.kind, i.target_id, i.content,
                 coalesce(e.source_id,s.id) AS source_id,
                 coalesce(e.snapshot_id,r.snapshot_id) AS snapshot_id,
                 s.site,
                 coalesce(json_extract(pc.effective,'$.source_type'),s.source_type) AS source_type,
                 f.entity_id,f.facet,
                 coalesce(e.run_id,f.run_id) AS data_version,
                 coalesce(e.content_hash,f.content_hash) AS content_hash
          FROM search_items i
          LEFT JOIN evidence e ON i.kind='evidence' AND e.id=i.target_id
          LEFT JOIN fragments f ON i.kind='fragment' AND f.id=i.target_id
          LEFT JOIN fragment_runs r ON r.id=f.run_id
          JOIN snapshots n ON n.id=coalesce(e.snapshot_id,r.snapshot_id)
          JOIN sources s ON s.id=n.source_id
          LEFT JOIN page_contexts pc ON pc.id=(SELECT id FROM page_contexts
            WHERE normalized_run=n.active_run ORDER BY rowid DESC LIMIT 1)
          WHERE (i.kind='evidence' AND n.active_run=e.run_id)
             OR (i.kind='fragment' AND r.active=1 AND n.active_run=r.normalized_run)"""
        clauses, parameters = [], []
        for key, column in [
            ("source", "source_id"),
            ("snapshot", "snapshot_id"),
            ("site", "site"),
            ("source_type", "source_type"),
            ("facet", "facet"),
        ]:
            value = getattr(filters, key)
            if value:
                if key == "source_type" and value in {"generic", "generic_web"}:
                    clauses.append("source_type IN ('generic','generic_web')")
                    continue
                clauses.append(f"{column}=?")
                parameters.append(value)
        if filters.entity:
            clauses.append("""(entity_id=? OR (kind='evidence' AND target_id IN
                            (SELECT evidence_id FROM entity_evidence WHERE entity_id=?)))""")
            parameters.extend([filters.entity, filters.entity])
        wrapped = "SELECT * FROM (" + sql + ")"
        if clauses:
            wrapped += " WHERE " + " AND ".join(clauses)
        return self.rows(wrapped, parameters)

    def lexical(self, query, eligible, limit):
        allowed = {row["item_id"]: row for row in eligible}
        terms = query.split()
        if not terms:
            return []
        if any(len(t) < 3 for t in terms):
            # trigram MATCH cannot find 1-2 character Japanese terms. Literal containment fallback.
            found = [
                r for r in eligible if any(t.casefold() in r["content"].casefold() for t in terms)
            ]
        else:
            expression = " OR ".join('"' + t.replace('"', '""') + '"' for t in terms)
            rows = self.rows(
                "SELECT rowid FROM search_fts WHERE search_fts MATCH ? "
                "ORDER BY bm25(search_fts),rowid",
                (expression,),
            )
            found = [allowed[r["rowid"]] for r in rows if r["rowid"] in allowed]
        return [dict(row, lexical_rank=i + 1) for i, row in enumerate(found[:limit])]

    def save_embeddings(self, space, rows, vectors):
        with self.db:
            self.db.execute(
                "INSERT OR IGNORE INTO embedding_spaces VALUES(?,?,?,?,?)",
                (space.key, space.model, space.revision, space.dimension, space.configuration),
            )
            self.db.executemany(
                "INSERT OR REPLACE INTO embeddings VALUES(?,?,?,?,?,?)",
                [
                    (
                        space.key,
                        r["item_id"],
                        r["content_hash"],
                        r["data_version"],
                        json_text(v),
                        now(),
                    )
                    for r, v in zip(rows, vectors)
                ],
            )

    def vector_rows(self, space, eligible):
        allowed = {r["item_id"]: r for r in eligible}
        rows = self.rows("SELECT * FROM embeddings WHERE space_id=?", (space.key,))
        return [
            dict(allowed[r["item_id"]], vector=json.loads(r["vector"]))
            for r in rows
            if r["item_id"] in allowed
            and allowed[r["item_id"]]["content_hash"] == r["content_hash"]
        ]

    def provenance(self, kind, target_id):
        fragment_metadata = None
        if kind == "fragment":
            fragment = self.one("SELECT metadata FROM fragments WHERE id=?", (target_id,))
            fragment_metadata = json.loads(fragment["metadata"]) if fragment else None
            evidence_ids = [
                r["evidence_id"]
                for r in self.rows(
                    "SELECT evidence_id FROM fragment_evidence WHERE fragment_id=?", (target_id,)
                )
            ]
        elif kind == "evidence":
            evidence_ids = [target_id]
        else:
            raise ValueError("Unknown provenance kind")
        if not evidence_ids:
            raise ValueError("Provenance target not found")
        result = []
        for evidence_id in evidence_ids:
            row = self.one(
                "SELECT e.id AS evidence_id,e.content,e.metadata,e.run_id,"
                "e.snapshot_id,e.source_id,"
                "n.raw_path,n.raw_sha256,n.captured_at,n.title,s.url,s.site FROM evidence e "
                "JOIN snapshots n ON n.id=e.snapshot_id JOIN sources s ON s.id=e.source_id "
                "WHERE e.id=?",
                (evidence_id,),
            )
            if not row:
                raise ValueError("Evidence not found")
            row["metadata"] = json.loads(row["metadata"])
            result.append(row)
        value = {"kind": kind, "target_id": target_id, "evidence": result}
        if fragment_metadata is not None:
            value["fragment_metadata"] = fragment_metadata
        value["page_contexts"] = [
            self.page_context(r["run_id"], (fragment_metadata or {}).get("context_id"))
            for r in result
        ]
        return value

    def save_document(self, entity_id, ai_id, markdown, citations, configuration):
        document_id = uid()
        with self.db:
            self.db.execute(
                "INSERT INTO documents VALUES(?,?,?,?,?,?,?)",
                (
                    document_id,
                    entity_id,
                    ai_id,
                    markdown,
                    json_text(citations),
                    json_text(configuration),
                    now(),
                ),
            )
        return document_id

    def document(self, document_id):
        return self.one("SELECT * FROM documents WHERE id=?", (document_id,))

    def status(self):
        tables = (
            "sources",
            "snapshots",
            "normalized_runs",
            "evidence",
            "entities",
            "fragments",
            "embedding_spaces",
            "embeddings",
            "documents",
            "ai_runs",
            "page_contexts",
            "extraction_jobs",
            "structured_documents",
            "benchmark_runs",
        )
        return {table: self.one(f"SELECT count(*) AS n FROM {table}")["n"] for table in tables}
