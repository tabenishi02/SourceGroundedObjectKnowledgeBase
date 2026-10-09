CREATE TABLE sources (
 id TEXT PRIMARY KEY, url TEXT NOT NULL UNIQUE, site TEXT NOT NULL,
 source_type TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE snapshots (
 id TEXT PRIMARY KEY, source_id TEXT NOT NULL REFERENCES sources(id),
 title TEXT NOT NULL, captured_at TEXT NOT NULL, raw_path TEXT NOT NULL,
 raw_sha256 TEXT NOT NULL, manifest TEXT NOT NULL, metadata TEXT NOT NULL,
 imported_at TEXT NOT NULL, active_run TEXT REFERENCES normalized_runs(id)
);
CREATE TABLE artifacts (
 snapshot_id TEXT NOT NULL REFERENCES snapshots(id), path TEXT NOT NULL,
 sha256 TEXT NOT NULL, bytes INTEGER NOT NULL, PRIMARY KEY(snapshot_id,path)
);
CREATE TABLE normalized_runs (
 id TEXT PRIMARY KEY, snapshot_id TEXT NOT NULL REFERENCES snapshots(id),
 configuration TEXT NOT NULL, blocks TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE evidence (
 id TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES normalized_runs(id),
 source_id TEXT NOT NULL REFERENCES sources(id), snapshot_id TEXT NOT NULL REFERENCES snapshots(id),
 content TEXT NOT NULL, metadata TEXT NOT NULL, content_hash TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE entities (
 id TEXT PRIMARY KEY, type TEXT NOT NULL, name TEXT NOT NULL,
 aliases TEXT NOT NULL, created_at TEXT NOT NULL, UNIQUE(type,name)
);
CREATE TABLE entity_relations (
 subject_id TEXT NOT NULL REFERENCES entities(id), predicate TEXT NOT NULL,
 object_id TEXT NOT NULL REFERENCES entities(id), metadata TEXT NOT NULL,
 PRIMARY KEY(subject_id,predicate,object_id)
);
CREATE TABLE entity_evidence (
 entity_id TEXT NOT NULL REFERENCES entities(id), evidence_id TEXT NOT NULL REFERENCES evidence(id),
 PRIMARY KEY(entity_id,evidence_id)
);
CREATE TABLE ai_runs (
 id TEXT PRIMARY KEY, task_type TEXT NOT NULL, model TEXT NOT NULL, revision TEXT NOT NULL,
 prompt TEXT NOT NULL, prompt_version TEXT NOT NULL, input TEXT NOT NULL, output TEXT,
 executed_at TEXT NOT NULL, status TEXT NOT NULL, error TEXT
);
CREATE TABLE fragment_runs (
 id TEXT PRIMARY KEY, normalized_run TEXT NOT NULL REFERENCES normalized_runs(id),
 snapshot_id TEXT NOT NULL REFERENCES snapshots(id), entity_id TEXT NOT NULL REFERENCES entities(id),
 ai_run TEXT NOT NULL REFERENCES ai_runs(id), configuration TEXT NOT NULL,
 active INTEGER NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE fragments (
 id TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES fragment_runs(id),
 entity_id TEXT NOT NULL REFERENCES entities(id), facet TEXT NOT NULL, content TEXT NOT NULL,
 metadata TEXT NOT NULL, content_hash TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE fragment_evidence (
 fragment_id TEXT NOT NULL REFERENCES fragments(id), evidence_id TEXT NOT NULL REFERENCES evidence(id),
 PRIMARY KEY(fragment_id,evidence_id)
);
CREATE TABLE search_items (
 id INTEGER PRIMARY KEY, kind TEXT NOT NULL CHECK(kind IN ('evidence','fragment')),
 target_id TEXT NOT NULL, content TEXT NOT NULL, UNIQUE(kind,target_id)
);
CREATE VIRTUAL TABLE search_fts USING fts5(content, content=search_items, content_rowid=id, tokenize=trigram);
CREATE TRIGGER search_insert AFTER INSERT ON search_items BEGIN
 INSERT INTO search_fts(rowid,content) VALUES(new.id,new.content);
END;
CREATE TABLE embedding_spaces (
 id TEXT PRIMARY KEY, model TEXT NOT NULL, revision TEXT NOT NULL,
 dimension INTEGER NOT NULL, configuration TEXT NOT NULL
);
CREATE TABLE embeddings (
 space_id TEXT NOT NULL REFERENCES embedding_spaces(id),
 item_id INTEGER NOT NULL REFERENCES search_items(id), content_hash TEXT NOT NULL,
 data_version TEXT NOT NULL, vector TEXT NOT NULL, created_at TEXT NOT NULL,
 PRIMARY KEY(space_id,item_id)
);
CREATE TABLE documents (
 id TEXT PRIMARY KEY, entity_id TEXT NOT NULL REFERENCES entities(id),
 ai_run TEXT NOT NULL REFERENCES ai_runs(id), markdown TEXT NOT NULL,
 citations TEXT NOT NULL, configuration TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE INDEX evidence_snapshot ON evidence(snapshot_id,run_id);
CREATE INDEX fragment_active ON fragment_runs(snapshot_id,entity_id,active);
CREATE INDEX fragment_refs ON fragment_evidence(evidence_id);
