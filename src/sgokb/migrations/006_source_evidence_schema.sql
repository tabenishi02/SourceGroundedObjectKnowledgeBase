-- Phase E / E-03: canonical Source / Evidence / Provenance schema.
-- Additive only. Prototype sources/snapshots/artifacts/normalized_runs/evidence remain untouched
-- until Phase L data migration.

CREATE TABLE source_records (
 id TEXT PRIMARY KEY,
 label TEXT,
 status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active','archived')),
 created_at TEXT NOT NULL,
 updated_at TEXT NOT NULL
);

CREATE TABLE source_locators (
 id TEXT PRIMARY KEY,
 source_id TEXT NOT NULL REFERENCES source_records(id),
 kind TEXT NOT NULL CHECK(length(trim(kind)) > 0),
 value TEXT NOT NULL CHECK(length(trim(value)) > 0),
 is_preferred INTEGER NOT NULL DEFAULT 0 CHECK(is_preferred IN (0,1)),
 status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active','retired')),
 created_at TEXT NOT NULL,
 retired_at TEXT
);
CREATE INDEX source_locators_source ON source_locators(source_id,status,kind);
CREATE INDEX source_locators_value ON source_locators(kind,value);

CREATE TABLE source_snapshots (
 id TEXT PRIMARY KEY,
 source_id TEXT NOT NULL REFERENCES source_records(id),
 observed_locator_id TEXT REFERENCES source_locators(id),
 captured_at TEXT NOT NULL,
 imported_at TEXT NOT NULL,
 capture_method TEXT NOT NULL CHECK(length(trim(capture_method)) > 0),
 capture_tool TEXT,
 capture_version TEXT,
 completeness TEXT NOT NULL CHECK(completeness IN ('complete','partial','failed')),
 title TEXT,
 manifest_json TEXT NOT NULL DEFAULT '{}' CHECK(json_valid(manifest_json)),
 metadata_json TEXT NOT NULL DEFAULT '{}' CHECK(json_valid(metadata_json)),
 warnings_json TEXT NOT NULL DEFAULT '[]' CHECK(json_valid(warnings_json)),
 created_at TEXT NOT NULL
);
CREATE INDEX source_snapshots_source ON source_snapshots(source_id,captured_at);

CREATE TABLE source_classifications (
 id TEXT PRIMARY KEY,
 source_id TEXT NOT NULL REFERENCES source_records(id),
 axis TEXT NOT NULL CHECK(axis IN (
   'resource_type','media_type','document_genre','publisher_kind','site','page_purpose'
 )),
 value TEXT NOT NULL CHECK(length(trim(value)) > 0),
 origin_kind TEXT NOT NULL CHECK(origin_kind IN ('captured','deterministic','inferred','override')),
 snapshot_id TEXT REFERENCES source_snapshots(id),
 created_at TEXT NOT NULL
);
CREATE INDEX source_classifications_lookup ON source_classifications(axis,value,source_id);
CREATE INDEX source_classifications_source ON source_classifications(source_id,axis,created_at);

CREATE TABLE source_metadata_values (
 id TEXT PRIMARY KEY,
 source_id TEXT NOT NULL REFERENCES source_records(id),
 key TEXT NOT NULL CHECK(length(trim(key)) > 0),
 value_json TEXT NOT NULL CHECK(json_valid(value_json)),
 origin_kind TEXT NOT NULL CHECK(origin_kind IN ('captured','deterministic','inferred','override')),
 snapshot_id TEXT REFERENCES source_snapshots(id),
 created_at TEXT NOT NULL
);
CREATE INDEX source_metadata_source ON source_metadata_values(source_id,key,created_at);

CREATE TABLE raw_artifacts (
 id TEXT PRIMARY KEY,
 snapshot_id TEXT NOT NULL REFERENCES source_snapshots(id),
 artifact_kind TEXT NOT NULL CHECK(length(trim(artifact_kind)) > 0),
 logical_path TEXT,
 storage_ref TEXT NOT NULL CHECK(length(trim(storage_ref)) > 0),
 media_type TEXT,
 sha256 TEXT NOT NULL CHECK(length(sha256) > 0),
 bytes INTEGER NOT NULL CHECK(bytes >= 0),
 created_at TEXT NOT NULL
);
CREATE UNIQUE INDEX raw_artifacts_unique
 ON raw_artifacts(snapshot_id,artifact_kind,ifnull(logical_path,''),sha256);
CREATE INDEX raw_artifacts_snapshot ON raw_artifacts(snapshot_id,artifact_kind);
CREATE INDEX raw_artifacts_hash ON raw_artifacts(sha256);

CREATE TABLE normalization_runs (
 id TEXT PRIMARY KEY,
 snapshot_id TEXT NOT NULL REFERENCES source_snapshots(id),
 extractor_key TEXT NOT NULL CHECK(length(trim(extractor_key)) > 0),
 extractor_version TEXT NOT NULL CHECK(length(trim(extractor_version)) > 0),
 configuration_json TEXT NOT NULL DEFAULT '{}' CHECK(json_valid(configuration_json)),
 output_json TEXT NOT NULL DEFAULT '{}' CHECK(json_valid(output_json)),
 status TEXT NOT NULL CHECK(status IN ('complete','partial','failed')),
 created_at TEXT NOT NULL
);
CREATE INDEX normalization_runs_snapshot ON normalization_runs(snapshot_id,created_at);

CREATE TABLE normalization_run_artifacts (
 run_id TEXT NOT NULL REFERENCES normalization_runs(id),
 artifact_id TEXT NOT NULL REFERENCES raw_artifacts(id),
 role TEXT NOT NULL DEFAULT 'input' CHECK(length(trim(role)) > 0),
 PRIMARY KEY(run_id,artifact_id,role)
);
CREATE INDEX normalization_artifacts_artifact ON normalization_run_artifacts(artifact_id,run_id);

CREATE TABLE evidence_records (
 id TEXT PRIMARY KEY,
 run_id TEXT NOT NULL REFERENCES normalization_runs(id),
 snapshot_id TEXT NOT NULL REFERENCES source_snapshots(id),
 source_id TEXT NOT NULL REFERENCES source_records(id),
 ordinal INTEGER NOT NULL DEFAULT 0 CHECK(ordinal >= 0),
 content TEXT NOT NULL CHECK(length(content) > 0),
 content_hash TEXT NOT NULL CHECK(length(content_hash) > 0),
 extraction_mode TEXT NOT NULL CHECK(extraction_mode IN ('verbatim','normalized','structured','transcribed')),
 language TEXT,
 metadata_json TEXT NOT NULL DEFAULT '{}' CHECK(json_valid(metadata_json)),
 created_at TEXT NOT NULL,
 UNIQUE(run_id,ordinal),
 UNIQUE(id,run_id)
);
CREATE INDEX evidence_records_snapshot ON evidence_records(snapshot_id,run_id,ordinal);
CREATE INDEX evidence_records_source ON evidence_records(source_id,snapshot_id);
CREATE INDEX evidence_records_hash ON evidence_records(content_hash);

CREATE TABLE evidence_locations (
 id TEXT PRIMARY KEY,
 evidence_id TEXT NOT NULL REFERENCES evidence_records(id),
 ordinal INTEGER NOT NULL DEFAULT 0 CHECK(ordinal >= 0),
 kind TEXT NOT NULL CHECK(kind IN (
   'dom_path','heading_path','block_order','page','section','time_range',
   'dataset_record','json_path','image_region','metadata_field','other'
 )),
 value_json TEXT NOT NULL CHECK(json_valid(value_json)),
 created_at TEXT NOT NULL,
 UNIQUE(evidence_id,ordinal)
);
CREATE INDEX evidence_locations_evidence ON evidence_locations(evidence_id,ordinal);

CREATE TABLE source_object_associations (
 source_id TEXT NOT NULL REFERENCES source_records(id),
 object_id TEXT NOT NULL REFERENCES objects(id),
 status TEXT NOT NULL CHECK(status IN ('candidate','confirmed','excluded')),
 subject_relationship TEXT,
 origin_kind TEXT NOT NULL CHECK(origin_kind IN ('manual','deterministic','inferred','migration')),
 note TEXT,
 created_at TEXT NOT NULL,
 updated_at TEXT NOT NULL,
 PRIMARY KEY(source_id,object_id)
);
CREATE INDEX source_object_associations_object ON source_object_associations(object_id,status,source_id);

CREATE TABLE source_relation_types (
 id TEXT PRIMARY KEY,
 key TEXT NOT NULL UNIQUE,
 name TEXT NOT NULL,
 description TEXT NOT NULL DEFAULT '',
 status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active','archived')),
 created_at TEXT NOT NULL,
 updated_at TEXT NOT NULL
);

CREATE TABLE source_relations (
 id TEXT PRIMARY KEY,
 subject_source_id TEXT NOT NULL REFERENCES source_records(id),
 relation_type_id TEXT NOT NULL REFERENCES source_relation_types(id),
 object_source_id TEXT NOT NULL REFERENCES source_records(id),
 origin_kind TEXT NOT NULL CHECK(origin_kind IN ('captured','deterministic','inferred','override','manual')),
 note TEXT,
 created_at TEXT NOT NULL,
 UNIQUE(subject_source_id,relation_type_id,object_source_id),
 CHECK(subject_source_id <> object_source_id)
);
CREATE INDEX source_relations_subject ON source_relations(subject_source_id,relation_type_id);
CREATE INDEX source_relations_object ON source_relations(object_source_id,relation_type_id);

CREATE TABLE evidence_roles (
 id TEXT PRIMARY KEY,
 key TEXT NOT NULL UNIQUE,
 name TEXT NOT NULL,
 description TEXT NOT NULL DEFAULT '',
 status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active','archived')),
 created_at TEXT NOT NULL,
 updated_at TEXT NOT NULL
);

CREATE TABLE evidence_links (
 id TEXT PRIMARY KEY,
 version_id TEXT NOT NULL REFERENCES object_versions(id),
 target_kind TEXT NOT NULL CHECK(target_kind IN ('statement','attribute','relation')),
 target_id TEXT NOT NULL,
 evidence_id TEXT NOT NULL REFERENCES evidence_records(id),
 role_id TEXT NOT NULL REFERENCES evidence_roles(id),
 origin_kind TEXT NOT NULL CHECK(origin_kind IN ('result_import','manual','migration','system')),
 origin_ref TEXT,
 created_at TEXT NOT NULL,
 UNIQUE(version_id,target_kind,target_id,evidence_id,role_id)
);
CREATE INDEX evidence_links_evidence ON evidence_links(evidence_id,version_id);
CREATE INDEX evidence_links_target ON evidence_links(target_kind,target_id,version_id);

-- A Snapshot locator is contextual and must belong to the same Source.
CREATE TRIGGER source_snapshots_locator_insert
BEFORE INSERT ON source_snapshots
WHEN NEW.observed_locator_id IS NOT NULL
BEGIN
 SELECT CASE WHEN NOT EXISTS (
   SELECT 1 FROM source_locators
   WHERE id=NEW.observed_locator_id AND source_id=NEW.source_id
 ) THEN RAISE(ABORT,'snapshot locator must belong to source') END;
END;

CREATE TRIGGER source_snapshots_locator_update
BEFORE UPDATE OF source_id,observed_locator_id ON source_snapshots
WHEN NEW.observed_locator_id IS NOT NULL
BEGIN
 SELECT CASE WHEN NOT EXISTS (
   SELECT 1 FROM source_locators
   WHERE id=NEW.observed_locator_id AND source_id=NEW.source_id
 ) THEN RAISE(ABORT,'snapshot locator must belong to source') END;
END;

-- Snapshot-scoped metadata/classification observations cannot cite another Source's Snapshot.
CREATE TRIGGER source_classifications_snapshot_insert
BEFORE INSERT ON source_classifications
WHEN NEW.snapshot_id IS NOT NULL
BEGIN
 SELECT CASE WHEN NOT EXISTS (
   SELECT 1 FROM source_snapshots WHERE id=NEW.snapshot_id AND source_id=NEW.source_id
 ) THEN RAISE(ABORT,'classification snapshot must belong to source') END;
END;

CREATE TRIGGER source_metadata_snapshot_insert
BEFORE INSERT ON source_metadata_values
WHEN NEW.snapshot_id IS NOT NULL
BEGIN
 SELECT CASE WHEN NOT EXISTS (
   SELECT 1 FROM source_snapshots WHERE id=NEW.snapshot_id AND source_id=NEW.source_id
 ) THEN RAISE(ABORT,'metadata snapshot must belong to source') END;
END;

-- A Normalization Run may only consume Raw Artifacts from its own Snapshot.
CREATE TRIGGER normalization_run_artifacts_validate_insert
BEFORE INSERT ON normalization_run_artifacts
BEGIN
 SELECT CASE WHEN NOT EXISTS (
   SELECT 1 FROM normalization_runs n
   JOIN raw_artifacts a ON a.id=NEW.artifact_id
   WHERE n.id=NEW.run_id AND n.snapshot_id=a.snapshot_id
 ) THEN RAISE(ABORT,'normalization artifact must belong to run snapshot') END;
END;

-- Evidence carries redundant run/snapshot/source IDs for efficient provenance filtering;
-- they must resolve to one consistent chain.
CREATE TRIGGER evidence_records_chain_insert
BEFORE INSERT ON evidence_records
BEGIN
 SELECT CASE WHEN NOT EXISTS (
   SELECT 1 FROM normalization_runs n
   JOIN source_snapshots s ON s.id=n.snapshot_id
   WHERE n.id=NEW.run_id
     AND n.snapshot_id=NEW.snapshot_id
     AND s.source_id=NEW.source_id
 ) THEN RAISE(ABORT,'evidence provenance chain mismatch') END;
 SELECT CASE WHEN NOT EXISTS (
   SELECT 1 FROM normalization_run_artifacts WHERE run_id=NEW.run_id
 ) THEN RAISE(ABORT,'evidence provenance requires raw artifact') END;
END;

CREATE TRIGGER evidence_records_chain_update
BEFORE UPDATE OF run_id,snapshot_id,source_id ON evidence_records
BEGIN
 SELECT CASE WHEN NOT EXISTS (
   SELECT 1 FROM normalization_runs n
   JOIN source_snapshots s ON s.id=n.snapshot_id
   WHERE n.id=NEW.run_id
     AND n.snapshot_id=NEW.snapshot_id
     AND s.source_id=NEW.source_id
 ) THEN RAISE(ABORT,'evidence provenance chain mismatch') END;
 SELECT CASE WHEN NOT EXISTS (
   SELECT 1 FROM normalization_run_artifacts WHERE run_id=NEW.run_id
 ) THEN RAISE(ABORT,'evidence provenance requires raw artifact') END;
END;

CREATE TRIGGER source_relations_type_insert
BEFORE INSERT ON source_relations
BEGIN
 SELECT CASE WHEN NOT EXISTS (
   SELECT 1 FROM source_relation_types WHERE id=NEW.relation_type_id AND status='active'
 ) THEN RAISE(ABORT,'source relation type must be active') END;
END;

-- Evidence Link target must exist in exactly the stated Knowledge Version.
CREATE TRIGGER evidence_links_validate_insert
BEFORE INSERT ON evidence_links
BEGIN
 SELECT CASE WHEN NOT EXISTS (
   SELECT 1 FROM evidence_roles WHERE id=NEW.role_id AND status='active'
 ) THEN RAISE(ABORT,'evidence role must be active') END;
 SELECT CASE WHEN NEW.target_kind='statement' AND NOT EXISTS (
   SELECT 1 FROM knowledge_statements WHERE id=NEW.target_id AND version_id=NEW.version_id
 ) THEN RAISE(ABORT,'statement evidence target must belong to version') END;
 SELECT CASE WHEN NEW.target_kind='attribute' AND NOT EXISTS (
   SELECT 1 FROM object_version_attributes WHERE id=NEW.target_id AND version_id=NEW.version_id
 ) THEN RAISE(ABORT,'attribute evidence target must belong to version') END;
 SELECT CASE WHEN NEW.target_kind='relation' AND NOT EXISTS (
   SELECT 1 FROM object_relations WHERE id=NEW.target_id AND version_id=NEW.version_id
 ) THEN RAISE(ABORT,'relation evidence target must belong to version') END;
END;

CREATE TRIGGER evidence_links_validate_update
BEFORE UPDATE OF version_id,target_kind,target_id,evidence_id,role_id ON evidence_links
BEGIN
 SELECT CASE WHEN NOT EXISTS (
   SELECT 1 FROM evidence_roles WHERE id=NEW.role_id AND status='active'
 ) THEN RAISE(ABORT,'evidence role must be active') END;
 SELECT CASE WHEN NEW.target_kind='statement' AND NOT EXISTS (
   SELECT 1 FROM knowledge_statements WHERE id=NEW.target_id AND version_id=NEW.version_id
 ) THEN RAISE(ABORT,'statement evidence target must belong to version') END;
 SELECT CASE WHEN NEW.target_kind='attribute' AND NOT EXISTS (
   SELECT 1 FROM object_version_attributes WHERE id=NEW.target_id AND version_id=NEW.version_id
 ) THEN RAISE(ABORT,'attribute evidence target must belong to version') END;
 SELECT CASE WHEN NEW.target_kind='relation' AND NOT EXISTS (
   SELECT 1 FROM object_relations WHERE id=NEW.target_id AND version_id=NEW.version_id
 ) THEN RAISE(ABORT,'relation evidence target must belong to version') END;
END;

-- Provenance-bearing records are append-oriented. Critical parent/content identity is immutable.
CREATE TRIGGER source_locators_identity_immutable
BEFORE UPDATE OF source_id,kind,value ON source_locators
BEGIN SELECT RAISE(ABORT,'source locator identity is immutable'); END;

CREATE TRIGGER source_snapshots_immutable
BEFORE UPDATE ON source_snapshots
BEGIN SELECT RAISE(ABORT,'source snapshot is immutable'); END;

CREATE TRIGGER source_classifications_immutable
BEFORE UPDATE ON source_classifications
BEGIN SELECT RAISE(ABORT,'source classification observation is immutable'); END;

CREATE TRIGGER source_metadata_values_immutable
BEFORE UPDATE ON source_metadata_values
BEGIN SELECT RAISE(ABORT,'source metadata observation is immutable'); END;

CREATE TRIGGER raw_artifacts_content_immutable
BEFORE UPDATE OF snapshot_id,artifact_kind,logical_path,media_type,sha256,bytes ON raw_artifacts
BEGIN SELECT RAISE(ABORT,'raw artifact content identity is immutable'); END;

CREATE TRIGGER normalization_runs_identity_immutable
BEFORE UPDATE OF snapshot_id,extractor_key,extractor_version,configuration_json ON normalization_runs
BEGIN SELECT RAISE(ABORT,'normalization run identity is immutable'); END;

CREATE TRIGGER evidence_records_immutable
BEFORE UPDATE ON evidence_records
BEGIN SELECT RAISE(ABORT,'evidence record is immutable'); END;

CREATE TRIGGER evidence_locations_immutable
BEFORE UPDATE ON evidence_locations
BEGIN SELECT RAISE(ABORT,'evidence location is immutable'); END;

INSERT INTO source_relation_types(id,key,name,description,status,created_at,updated_at) VALUES
 ('source-relation:cites','cites','cites','Source explicitly cites another Source','active','2026-10-12T00:00:00Z','2026-10-12T00:00:00Z'),
 ('source-relation:quotes','quotes','quotes','Source quotes another Source','active','2026-10-12T00:00:00Z','2026-10-12T00:00:00Z'),
 ('source-relation:derived_from','derived_from','derived from','Source is derived from another Source','active','2026-10-12T00:00:00Z','2026-10-12T00:00:00Z'),
 ('source-relation:mirror_of','mirror_of','mirror of','Source mirrors another Source','active','2026-10-12T00:00:00Z','2026-10-12T00:00:00Z'),
 ('source-relation:syndicated_from','syndicated_from','syndicated from','Source syndicates content from another Source','active','2026-10-12T00:00:00Z','2026-10-12T00:00:00Z'),
 ('source-relation:transcript_of','transcript_of','transcript of','Source is a transcript of another Source','active','2026-10-12T00:00:00Z','2026-10-12T00:00:00Z'),
 ('source-relation:reproduction_of','reproduction_of','reproduction of','Source reproduces another Source','active','2026-10-12T00:00:00Z','2026-10-12T00:00:00Z');

INSERT INTO evidence_roles(id,key,name,description,status,created_at,updated_at) VALUES
 ('evidence-role:supports','supports','supports','Evidence supports the linked Knowledge element','active','2026-10-12T00:00:00Z','2026-10-12T00:00:00Z'),
 ('evidence-role:contradicts','contradicts','contradicts','Evidence contradicts the linked Knowledge element','active','2026-10-12T00:00:00Z','2026-10-12T00:00:00Z'),
 ('evidence-role:contextualizes','contextualizes','contextualizes','Evidence supplies context without directly supporting or contradicting','active','2026-10-12T00:00:00Z','2026-10-12T00:00:00Z');
