-- Additive upgrade: v1 records and generations remain readable.
CREATE TABLE page_contexts (
 id TEXT PRIMARY KEY, normalized_run TEXT NOT NULL REFERENCES normalized_runs(id),
 snapshot_id TEXT NOT NULL REFERENCES snapshots(id), deterministic TEXT NOT NULL,
 inferred TEXT NOT NULL, overrides TEXT NOT NULL, effective TEXT NOT NULL,
 version TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE INDEX context_generation ON page_contexts(normalized_run,created_at);
CREATE TABLE extraction_jobs (
 id TEXT PRIMARY KEY, snapshot_id TEXT NOT NULL REFERENCES snapshots(id),
 normalized_run TEXT NOT NULL REFERENCES normalized_runs(id),
 entity_id TEXT NOT NULL REFERENCES entities(id), context_id TEXT NOT NULL REFERENCES page_contexts(id),
 configuration TEXT NOT NULL, status TEXT NOT NULL,
 fragment_run TEXT REFERENCES fragment_runs(id), created_at TEXT NOT NULL
);
CREATE TABLE extraction_batches (
 id TEXT PRIMARY KEY, job_id TEXT NOT NULL REFERENCES extraction_jobs(id),
 batch_key TEXT NOT NULL, ai_run TEXT REFERENCES ai_runs(id), result TEXT,
 status TEXT NOT NULL, error TEXT, UNIQUE(job_id,batch_key)
);
CREATE TABLE evidence_assessments (
 job_id TEXT NOT NULL REFERENCES extraction_jobs(id), evidence_id TEXT NOT NULL REFERENCES evidence(id),
 substantive INTEGER NOT NULL, status TEXT NOT NULL, discard_reason TEXT,
 batch_id TEXT REFERENCES extraction_batches(id), fragment_count INTEGER NOT NULL DEFAULT 0,
 PRIMARY KEY(job_id,evidence_id)
);
CREATE TABLE entity_candidates (
 id TEXT PRIMARY KEY, job_id TEXT NOT NULL REFERENCES extraction_jobs(id),
 batch_id TEXT NOT NULL REFERENCES extraction_batches(id), candidate TEXT NOT NULL,
 status TEXT NOT NULL DEFAULT 'unconfirmed'
);
CREATE TABLE structured_documents (
 document_id TEXT PRIMARY KEY REFERENCES documents(id), representation TEXT NOT NULL,
 clusters TEXT NOT NULL, algorithm TEXT NOT NULL
);
CREATE TABLE ai_observations (
 ai_run TEXT PRIMARY KEY REFERENCES ai_runs(id), observations TEXT NOT NULL
);
CREATE TABLE benchmark_runs (
 id TEXT PRIMARY KEY, manifest_hash TEXT NOT NULL, configuration TEXT NOT NULL,
 created_at TEXT NOT NULL, status TEXT NOT NULL
);
CREATE TABLE benchmark_cases (
 run_id TEXT NOT NULL REFERENCES benchmark_runs(id), case_id TEXT NOT NULL,
 status TEXT NOT NULL, result TEXT, error TEXT, PRIMARY KEY(run_id,case_id)
);
