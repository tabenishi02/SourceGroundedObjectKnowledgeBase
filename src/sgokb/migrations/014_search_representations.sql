-- Phase I / I-01: derived Search Representation content and membership contract.
-- The E-02 representation tables are derived and intentionally rebuilt here.

DROP TRIGGER IF EXISTS search_memberships_validate_insert;
DROP TRIGGER IF EXISTS search_memberships_validate_update;
DROP TABLE search_representation_memberships;
DROP TABLE search_representations;

CREATE TABLE search_representations (
 id TEXT PRIMARY KEY,
 kind TEXT NOT NULL CHECK(kind IN ('object_overall','facet','statement','evidence')),
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
 target_kind TEXT NOT NULL CHECK(target_kind IN ('object_overall','facet','statement')),
 facet_id TEXT REFERENCES facet_definitions(id),
 statement_id TEXT REFERENCES knowledge_statements(id),
 created_at TEXT NOT NULL,
 FOREIGN KEY(version_id,object_id) REFERENCES object_versions(id,object_id),
 FOREIGN KEY(version_id,facet_id) REFERENCES object_version_facets(version_id,facet_id),
 FOREIGN KEY(statement_id,version_id) REFERENCES knowledge_statements(id,version_id),
 CHECK(
   (target_kind='object_overall' AND facet_id IS NULL AND statement_id IS NULL)
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

CREATE INDEX search_representation_hash
 ON search_representations(kind,builder_key,builder_version,content_hash);
CREATE INDEX knowledge_search_membership_representation
 ON knowledge_search_representation_memberships(representation_id);
CREATE INDEX knowledge_search_membership_scope
 ON knowledge_search_representation_memberships(object_id,version_id,target_kind,facet_id,statement_id);
CREATE INDEX evidence_search_membership_representation
 ON evidence_search_representation_memberships(representation_id);
CREATE INDEX evidence_search_membership_generation
 ON evidence_search_representation_memberships(source_id,snapshot_id,run_id,evidence_id);

CREATE UNIQUE INDEX knowledge_search_object_unique
 ON knowledge_search_representation_memberships(object_id,version_id,representation_id)
 WHERE target_kind='object_overall';
CREATE UNIQUE INDEX knowledge_search_facet_unique
 ON knowledge_search_representation_memberships(object_id,version_id,facet_id,representation_id)
 WHERE target_kind='facet';
CREATE UNIQUE INDEX knowledge_search_statement_unique
 ON knowledge_search_representation_memberships(object_id,version_id,statement_id,representation_id)
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

-- Read-only compatibility surface for pre-I-01 callers. New writes use the
-- explicit Knowledge/Evidence membership tables.
CREATE VIEW search_representation_memberships AS
SELECT
 m.id,
 m.version_id,
 m.representation_id,
 m.target_kind,
 CASE m.target_kind
   WHEN 'object_overall' THEN m.object_id
   WHEN 'facet' THEN m.facet_id
   WHEN 'statement' THEN m.statement_id
 END AS target_ref,
 m.created_at
FROM knowledge_search_representation_memberships m;
