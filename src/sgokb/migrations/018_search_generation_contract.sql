-- Phase N / N05D-04R2 / R2-04: coexistence schema for compact object_overview.
--
-- This is a schema/coexistence migration only. It preserves every v1 Search
-- Representation, Knowledge/Evidence membership, and persisted Embedding. It does
-- not create object_overview content, rebuild Qdrant, or cut over active retrieval.

-- Migration 016 installed FTS over search_representations. The parent table must be
-- rebuilt to widen its kind CHECK, so remove the derived FTS surface first and
-- recreate it after the copy/swap.
DROP TRIGGER IF EXISTS search_representation_fts_insert;
DROP TRIGGER IF EXISTS search_representation_fts_delete;
DROP TRIGGER IF EXISTS search_representation_fts_update;
DROP TABLE IF EXISTS search_representation_fts;

DROP VIEW IF EXISTS search_representation_memberships;

-- Drop named triggers before renaming tables; trigger names are database-global.
DROP TRIGGER IF EXISTS knowledge_search_memberships_validate_insert;
DROP TRIGGER IF EXISTS knowledge_search_memberships_immutable;
DROP TRIGGER IF EXISTS evidence_search_memberships_validate_insert;
DROP TRIGGER IF EXISTS evidence_search_memberships_immutable;
DROP TRIGGER IF EXISTS search_representation_embeddings_validate_insert;
DROP TRIGGER IF EXISTS search_representation_embeddings_validate_update;

-- Rename every child that references search_representations before renaming the
-- parent. SQLite rewrites the renamed child FKs to the renamed parent; new final
-- tables can then be created without deleting/cascading legacy rows.
ALTER TABLE knowledge_search_representation_memberships
 RENAME TO knowledge_search_representation_memberships_v1;
ALTER TABLE evidence_search_representation_memberships
 RENAME TO evidence_search_representation_memberships_v1;
ALTER TABLE search_representation_embeddings
 RENAME TO search_representation_embeddings_v1;
ALTER TABLE search_representations
 RENAME TO search_representations_v1;

CREATE TABLE search_representations (
 id TEXT PRIMARY KEY,
 kind TEXT NOT NULL CHECK(kind IN (
   'object_overall','object_overview','facet','statement','evidence'
 )),
 builder_key TEXT NOT NULL CHECK(length(trim(builder_key)) > 0),
 builder_version TEXT NOT NULL CHECK(length(trim(builder_version)) > 0),
 content TEXT NOT NULL CHECK(length(trim(content)) > 0),
 content_hash TEXT NOT NULL CHECK(length(content_hash) = 64),
 created_at TEXT NOT NULL,
 UNIQUE(kind,builder_key,builder_version,content_hash)
);

CREATE TABLE knowledge_search_representation_memberships (
 id TEXT PRIMARY KEY,
 representation_id TEXT NOT NULL REFERENCES search_representations(id) ON DELETE CASCADE,
 object_id TEXT NOT NULL REFERENCES objects(id),
 version_id TEXT NOT NULL REFERENCES object_versions(id),
 target_kind TEXT NOT NULL CHECK(target_kind IN (
   'object_overall','object_overview','facet','statement'
 )),
 facet_id TEXT REFERENCES facet_definitions(id),
 statement_id TEXT REFERENCES knowledge_statements(id),
 created_at TEXT NOT NULL,
 FOREIGN KEY(version_id,object_id) REFERENCES object_versions(id,object_id),
 FOREIGN KEY(version_id,facet_id) REFERENCES object_version_facets(version_id,facet_id),
 FOREIGN KEY(statement_id,version_id) REFERENCES knowledge_statements(id,version_id),
 CHECK(
   (target_kind IN ('object_overall','object_overview')
      AND facet_id IS NULL AND statement_id IS NULL)
   OR (target_kind='facet' AND facet_id IS NOT NULL AND statement_id IS NULL)
   OR (target_kind='statement' AND statement_id IS NOT NULL)
 )
);

CREATE TABLE evidence_search_representation_memberships (
 id TEXT PRIMARY KEY,
 representation_id TEXT NOT NULL REFERENCES search_representations(id) ON DELETE CASCADE,
 evidence_id TEXT NOT NULL REFERENCES evidence_records(id),
 source_id TEXT NOT NULL REFERENCES source_records(id),
 snapshot_id TEXT NOT NULL REFERENCES source_snapshots(id),
 run_id TEXT NOT NULL REFERENCES normalization_runs(id),
 created_at TEXT NOT NULL,
 UNIQUE(representation_id,evidence_id)
);

CREATE TABLE search_representation_embeddings (
 space_id TEXT NOT NULL REFERENCES search_embedding_spaces(id) ON DELETE CASCADE,
 representation_id TEXT NOT NULL REFERENCES search_representations(id) ON DELETE CASCADE,
 content_hash TEXT NOT NULL CHECK(length(content_hash) = 64),
 vector BLOB NOT NULL CHECK(length(vector) > 0),
 created_at TEXT NOT NULL,
 PRIMARY KEY(space_id,representation_id)
);

INSERT INTO search_representations
SELECT * FROM search_representations_v1;

INSERT INTO knowledge_search_representation_memberships
SELECT * FROM knowledge_search_representation_memberships_v1;

INSERT INTO evidence_search_representation_memberships
SELECT * FROM evidence_search_representation_memberships_v1;

INSERT INTO search_representation_embeddings
SELECT * FROM search_representation_embeddings_v1;

-- Drop children before the old parent so ON DELETE CASCADE cannot remove the
-- preserved rows copied into the new tables.
DROP TABLE knowledge_search_representation_memberships_v1;
DROP TABLE evidence_search_representation_memberships_v1;
DROP TABLE search_representation_embeddings_v1;
DROP TABLE search_representations_v1;

CREATE INDEX search_representation_hash
 ON search_representations(kind,builder_key,builder_version,content_hash);
CREATE INDEX knowledge_search_membership_representation
 ON knowledge_search_representation_memberships(representation_id);
CREATE INDEX knowledge_search_membership_scope
 ON knowledge_search_representation_memberships(
   object_id,version_id,target_kind,facet_id,statement_id
 );
CREATE INDEX evidence_search_membership_representation
 ON evidence_search_representation_memberships(representation_id);
CREATE INDEX evidence_search_membership_generation
 ON evidence_search_representation_memberships(source_id,snapshot_id,run_id,evidence_id);
CREATE INDEX search_representation_embeddings_representation
 ON search_representation_embeddings(representation_id,space_id);

-- One semantic membership per canonical target. Representation identity remains in
-- the row and content table; it is not part of membership uniqueness.
CREATE UNIQUE INDEX knowledge_search_object_overall_unique
 ON knowledge_search_representation_memberships(object_id,version_id)
 WHERE target_kind='object_overall';
CREATE UNIQUE INDEX knowledge_search_object_overview_unique
 ON knowledge_search_representation_memberships(object_id,version_id)
 WHERE target_kind='object_overview';
CREATE UNIQUE INDEX knowledge_search_facet_unique
 ON knowledge_search_representation_memberships(object_id,version_id,facet_id)
 WHERE target_kind='facet';
CREATE UNIQUE INDEX knowledge_search_statement_unique
 ON knowledge_search_representation_memberships(object_id,version_id,statement_id)
 WHERE target_kind='statement';

CREATE TRIGGER knowledge_search_memberships_validate_insert
BEFORE INSERT ON knowledge_search_representation_memberships
BEGIN
 SELECT CASE WHEN NOT EXISTS (
   SELECT 1 FROM search_representations r
   WHERE r.id=NEW.representation_id AND r.kind=NEW.target_kind
 ) THEN RAISE(ABORT,'representation kind must match knowledge membership') END;
 SELECT CASE WHEN NEW.target_kind='statement' AND NOT EXISTS (
   SELECT 1 FROM knowledge_statements s
   WHERE s.id=NEW.statement_id AND s.version_id=NEW.version_id
     AND s.facet_id IS NEW.facet_id
 ) THEN RAISE(ABORT,'statement membership context mismatch') END;
END;

CREATE TRIGGER knowledge_search_memberships_immutable
BEFORE UPDATE ON knowledge_search_representation_memberships
BEGIN SELECT RAISE(ABORT,'search representation membership is immutable'); END;

CREATE TRIGGER evidence_search_memberships_validate_insert
BEFORE INSERT ON evidence_search_representation_memberships
BEGIN
 SELECT CASE WHEN NOT EXISTS (
   SELECT 1 FROM search_representations r
   WHERE r.id=NEW.representation_id AND r.kind='evidence'
 ) THEN RAISE(ABORT,'representation kind must match evidence membership') END;
 SELECT CASE WHEN NOT EXISTS (
   SELECT 1 FROM evidence_records e
   WHERE e.id=NEW.evidence_id
     AND e.source_id=NEW.source_id
     AND e.snapshot_id=NEW.snapshot_id
     AND e.run_id=NEW.run_id
 ) THEN RAISE(ABORT,'evidence membership provenance mismatch') END;
END;

CREATE TRIGGER evidence_search_memberships_immutable
BEFORE UPDATE ON evidence_search_representation_memberships
BEGIN SELECT RAISE(ABORT,'search representation membership is immutable'); END;

CREATE TRIGGER search_representation_embeddings_validate_insert
BEFORE INSERT ON search_representation_embeddings
BEGIN
 SELECT CASE WHEN NOT EXISTS (
   SELECT 1 FROM search_representations r
   WHERE r.id=NEW.representation_id AND r.content_hash=NEW.content_hash
 ) THEN RAISE(ABORT,'embedding content hash must match Search Representation') END;
 SELECT CASE WHEN length(NEW.vector) <> 4 * (
   SELECT dimension FROM search_embedding_spaces WHERE id=NEW.space_id
 ) THEN RAISE(ABORT,'embedding vector byte length must match Embedding Space dimension') END;
END;

CREATE TRIGGER search_representation_embeddings_validate_update
BEFORE UPDATE ON search_representation_embeddings
BEGIN
 SELECT RAISE(ABORT,'Search Representation embedding cache is immutable');
END;

-- Read-only compatibility surface for pre-I-01 callers. object_overview is an
-- Object-scoped membership, but remains distinct from object_overall.
CREATE VIEW search_representation_memberships AS
SELECT
 m.id,
 m.version_id,
 m.representation_id,
 m.target_kind,
 CASE
   WHEN m.target_kind IN ('object_overall','object_overview') THEN m.object_id
   WHEN m.target_kind='facet' THEN m.facet_id
   WHEN m.target_kind='statement' THEN m.statement_id
 END AS target_ref,
 m.created_at
FROM knowledge_search_representation_memberships m;

-- Recreate the derived FTS index after the parent-table swap.
CREATE VIRTUAL TABLE search_representation_fts USING fts5(
 representation_id UNINDEXED,
 kind UNINDEXED,
 content,
 tokenize='trigram'
);

INSERT INTO search_representation_fts(representation_id,kind,content)
SELECT id,kind,content FROM search_representations;

CREATE TRIGGER search_representation_fts_insert
AFTER INSERT ON search_representations
BEGIN
 INSERT INTO search_representation_fts(representation_id,kind,content)
 VALUES(NEW.id,NEW.kind,NEW.content);
END;

CREATE TRIGGER search_representation_fts_delete
AFTER DELETE ON search_representations
BEGIN
 DELETE FROM search_representation_fts WHERE representation_id=OLD.id;
END;

CREATE TRIGGER search_representation_fts_update
AFTER UPDATE OF kind,content ON search_representations
BEGIN
 DELETE FROM search_representation_fts WHERE representation_id=OLD.id;
 INSERT INTO search_representation_fts(representation_id,kind,content)
 VALUES(NEW.id,NEW.kind,NEW.content);
END;

-- Knowledge Search generation identity is intentionally separate from both
-- representation builder version and Embedding Space identity.
CREATE TABLE knowledge_search_generations (
 id TEXT PRIMARY KEY,
 contract_key TEXT NOT NULL CHECK(length(trim(contract_key)) > 0),
 contract_version INTEGER NOT NULL CHECK(contract_version > 0),
 state TEXT NOT NULL CHECK(state IN ('building','ready','failed','retired')),
 source_catalog_digest TEXT
   CHECK(source_catalog_digest IS NULL OR length(source_catalog_digest)=64),
 membership_digest TEXT
   CHECK(membership_digest IS NULL OR length(membership_digest)=64),
 created_at TEXT NOT NULL,
 ready_at TEXT,
 retired_at TEXT,
 last_error TEXT,
 CHECK(state <> 'ready' OR (
   source_catalog_digest IS NOT NULL
   AND membership_digest IS NOT NULL
   AND ready_at IS NOT NULL
 )),
 CHECK(state <> 'retired' OR retired_at IS NOT NULL)
);

CREATE TABLE knowledge_search_generation_memberships (
 generation_id TEXT NOT NULL
   REFERENCES knowledge_search_generations(id) ON DELETE CASCADE,
 membership_id TEXT NOT NULL
   REFERENCES knowledge_search_representation_memberships(id) ON DELETE CASCADE,
 created_at TEXT NOT NULL,
 PRIMARY KEY(generation_id,membership_id)
);

CREATE TABLE knowledge_search_active_generation (
 scope TEXT PRIMARY KEY CHECK(scope='knowledge'),
 active_generation_id TEXT NOT NULL REFERENCES knowledge_search_generations(id),
 activation_revision INTEGER NOT NULL CHECK(activation_revision > 0),
 activated_at TEXT NOT NULL
);

CREATE TABLE knowledge_search_generation_switches (
 id TEXT PRIMARY KEY,
 from_generation_id TEXT REFERENCES knowledge_search_generations(id),
 to_generation_id TEXT NOT NULL REFERENCES knowledge_search_generations(id),
 switch_kind TEXT NOT NULL CHECK(switch_kind IN ('bootstrap','cutover','rollback','recovery')),
 reason TEXT NOT NULL DEFAULT '',
 source_catalog_digest TEXT
   CHECK(source_catalog_digest IS NULL OR length(source_catalog_digest)=64),
 switched_at TEXT NOT NULL
);

CREATE TABLE knowledge_search_generation_vector_indexes (
 generation_id TEXT NOT NULL
   REFERENCES knowledge_search_generations(id) ON DELETE CASCADE,
 embedding_space_id TEXT NOT NULL
   REFERENCES search_embedding_spaces(id) ON DELETE CASCADE,
 backend_key TEXT NOT NULL CHECK(length(trim(backend_key)) > 0),
 namespace_key TEXT NOT NULL CHECK(length(trim(namespace_key)) > 0),
 status TEXT NOT NULL CHECK(status IN ('building','ready','failed','retired')),
 membership_digest TEXT
   CHECK(membership_digest IS NULL OR length(membership_digest)=64),
 point_count INTEGER CHECK(point_count IS NULL OR point_count >= 0),
 created_at TEXT NOT NULL,
 updated_at TEXT NOT NULL,
 last_error TEXT,
 PRIMARY KEY(generation_id,embedding_space_id,backend_key),
 UNIQUE(backend_key,namespace_key),
 CHECK(status <> 'ready' OR (membership_digest IS NOT NULL AND point_count IS NOT NULL))
);

CREATE INDEX knowledge_search_generation_memberships_membership
 ON knowledge_search_generation_memberships(membership_id,generation_id);
CREATE INDEX knowledge_search_generations_contract
 ON knowledge_search_generations(contract_key,contract_version,state,created_at);
CREATE INDEX knowledge_search_generation_switches_time
 ON knowledge_search_generation_switches(switched_at,id);

CREATE TRIGGER knowledge_search_generation_memberships_validate_insert
BEFORE INSERT ON knowledge_search_generation_memberships
BEGIN
 SELECT CASE WHEN EXISTS (
   SELECT 1
   FROM knowledge_search_generations g
   JOIN knowledge_search_representation_memberships m ON m.id=NEW.membership_id
   WHERE g.id=NEW.generation_id
     AND (
       (g.contract_key='phase-i-search-v1' AND m.target_kind='object_overview')
       OR
       (g.contract_key='n05d04r2-hierarchical-v2' AND m.target_kind='object_overall')
     )
 ) THEN RAISE(ABORT,'membership kind is incompatible with Knowledge Search generation') END;
END;

CREATE TRIGGER knowledge_search_generation_memberships_immutable
BEFORE UPDATE ON knowledge_search_generation_memberships
BEGIN SELECT RAISE(ABORT,'Knowledge Search generation membership is immutable'); END;

CREATE TRIGGER knowledge_search_active_generation_validate_insert
BEFORE INSERT ON knowledge_search_active_generation
BEGIN
 SELECT CASE WHEN NOT EXISTS (
   SELECT 1 FROM knowledge_search_generations g
   WHERE g.id=NEW.active_generation_id AND g.state='ready'
 ) THEN RAISE(ABORT,'active Knowledge Search generation must be ready') END;
END;

CREATE TRIGGER knowledge_search_active_generation_validate_update
BEFORE UPDATE OF active_generation_id ON knowledge_search_active_generation
BEGIN
 SELECT CASE WHEN NOT EXISTS (
   SELECT 1 FROM knowledge_search_generations g
   WHERE g.id=NEW.active_generation_id AND g.state='ready'
 ) THEN RAISE(ABORT,'active Knowledge Search generation must be ready') END;
END;

CREATE TRIGGER knowledge_search_generation_prevent_active_retire
BEFORE UPDATE OF state ON knowledge_search_generations
WHEN NEW.state <> 'ready'
BEGIN
 SELECT CASE WHEN EXISTS (
   SELECT 1 FROM knowledge_search_active_generation a
   WHERE a.active_generation_id=OLD.id
 ) THEN RAISE(ABORT,'active Knowledge Search generation must remain ready') END;
END;

-- Deterministic legacy identity. It starts in building state because SQL migration
-- cannot prove the runtime/Qdrant state or compute the SHA-256 catalog/member
-- digests. R2-07 owns explicit legacy registration/verification and activation.
INSERT INTO knowledge_search_generations(
 id,contract_key,contract_version,state,created_at
) VALUES(
 'search-generation:phase-i-v1',
 'phase-i-search-v1',
 1,
 'building',
 strftime('%Y-%m-%dT%H:%M:%fZ','now')
);

INSERT INTO knowledge_search_generation_memberships(
 generation_id,membership_id,created_at
)
SELECT
 'search-generation:phase-i-v1',
 id,
 strftime('%Y-%m-%dT%H:%M:%fZ','now')
FROM knowledge_search_representation_memberships
ORDER BY id;
