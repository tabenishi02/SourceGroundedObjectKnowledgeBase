-- Additive derived state; existing generations remain readable.
CREATE TABLE extraction_windows (
 job_id TEXT NOT NULL REFERENCES extraction_jobs(id), window_key TEXT NOT NULL,
 membership TEXT NOT NULL, result TEXT NOT NULL, ai_run TEXT REFERENCES ai_runs(id),
 PRIMARY KEY(job_id,window_key)
);
CREATE TABLE window_splits (
 job_id TEXT NOT NULL REFERENCES extraction_jobs(id), window_key TEXT NOT NULL,
 children TEXT NOT NULL, PRIMARY KEY(job_id,window_key)
);
CREATE TABLE claim_generations (
 id TEXT PRIMARY KEY, entity_id TEXT NOT NULL REFERENCES entities(id),
 configuration TEXT NOT NULL, input_hash TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE knowledge_claims (
 generation_id TEXT NOT NULL REFERENCES claim_generations(id), id TEXT NOT NULL,
 claim TEXT NOT NULL, PRIMARY KEY(generation_id,id)
);
CREATE TABLE claim_support (
 generation_id TEXT NOT NULL, claim_id TEXT NOT NULL,
 fragment_id TEXT NOT NULL REFERENCES fragments(id),
 PRIMARY KEY(generation_id,claim_id,fragment_id),
 FOREIGN KEY(generation_id,claim_id) REFERENCES knowledge_claims(generation_id,id)
);
CREATE TABLE vector_cache (
 cache_key TEXT PRIMARY KEY, model TEXT NOT NULL, revision TEXT NOT NULL,
 configuration TEXT NOT NULL, dimension INTEGER NOT NULL, vector TEXT NOT NULL
);
