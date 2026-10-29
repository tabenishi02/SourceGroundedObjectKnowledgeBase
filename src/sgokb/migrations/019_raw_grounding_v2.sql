-- Phase P / P-RAW-05: additive Raw-grounded Package/Result v2 persistence.
-- v1 Evidence-grounded rows remain authoritative for v1 artifacts.

CREATE TABLE package_raw_grounding_metadata (
    package_id TEXT PRIMARY KEY REFERENCES package_exchange_records(package_id),
    grounding_contract TEXT NOT NULL,
    resolution_contract TEXT NOT NULL,
    grounding_set_sha256 TEXT NOT NULL CHECK(length(grounding_set_sha256)=64),
    created_at TEXT NOT NULL
);

CREATE TABLE package_raw_artifacts (
    package_id TEXT NOT NULL REFERENCES package_exchange_records(package_id),
    ordinal INTEGER NOT NULL CHECK(ordinal >= 0),
    raw_artifact_id TEXT NOT NULL REFERENCES raw_artifacts(id),
    source_id TEXT NOT NULL REFERENCES source_records(id),
    snapshot_id TEXT NOT NULL REFERENCES source_snapshots(id),
    artifact_kind TEXT NOT NULL,
    package_path TEXT NOT NULL,
    logical_path TEXT,
    media_type TEXT,
    charset TEXT,
    byte_size INTEGER NOT NULL CHECK(byte_size >= 0),
    sha256 TEXT NOT NULL CHECK(length(sha256)=64),
    PRIMARY KEY(package_id, raw_artifact_id),
    UNIQUE(package_id, ordinal),
    UNIQUE(package_id, package_path)
);
CREATE INDEX package_raw_artifacts_raw
    ON package_raw_artifacts(raw_artifact_id, package_id);
CREATE INDEX package_raw_artifacts_snapshot
    ON package_raw_artifacts(snapshot_id, package_id);

CREATE TABLE package_evidence_raw_bindings (
    package_id TEXT NOT NULL REFERENCES package_exchange_records(package_id),
    ordinal INTEGER NOT NULL CHECK(ordinal >= 0),
    evidence_id TEXT NOT NULL REFERENCES evidence_records(id),
    source_id TEXT NOT NULL REFERENCES source_records(id),
    snapshot_id TEXT NOT NULL REFERENCES source_snapshots(id),
    normalization_run_id TEXT NOT NULL REFERENCES normalization_runs(id),
    raw_artifact_ids_json TEXT NOT NULL CHECK(json_valid(raw_artifact_ids_json)),
    PRIMARY KEY(package_id, evidence_id),
    UNIQUE(package_id, ordinal)
);
CREATE INDEX package_evidence_raw_bindings_evidence
    ON package_evidence_raw_bindings(evidence_id, package_id);

CREATE TABLE raw_grounding_links (
    id TEXT PRIMARY KEY,
    version_id TEXT NOT NULL REFERENCES object_versions(id),
    target_kind TEXT NOT NULL CHECK(target_kind IN ('statement','attribute','relation')),
    target_id TEXT NOT NULL,
    package_id TEXT NOT NULL REFERENCES package_exchange_records(package_id),
    raw_artifact_id TEXT NOT NULL REFERENCES raw_artifacts(id),
    role TEXT NOT NULL CHECK(role IN ('supports','contradicts','contextualizes')),
    locator_json TEXT CHECK(locator_json IS NULL OR json_valid(locator_json)),
    origin_kind TEXT NOT NULL CHECK(origin_kind IN ('result_import','manual','migration','system')),
    origin_ref TEXT,
    created_at TEXT NOT NULL
);
CREATE UNIQUE INDEX raw_grounding_links_unique
    ON raw_grounding_links(
        version_id,target_kind,target_id,package_id,raw_artifact_id,role,ifnull(locator_json,'')
    );
CREATE INDEX raw_grounding_links_raw
    ON raw_grounding_links(raw_artifact_id,version_id);
CREATE INDEX raw_grounding_links_target
    ON raw_grounding_links(target_kind,target_id,version_id);
CREATE INDEX raw_grounding_links_package
    ON raw_grounding_links(package_id,version_id);

-- Package audit lineage must agree with canonical Source/Snapshot/Raw identity.
CREATE TRIGGER package_raw_artifacts_validate_insert
BEFORE INSERT ON package_raw_artifacts
BEGIN
 SELECT CASE WHEN NOT EXISTS (
   SELECT 1 FROM raw_artifacts a
   JOIN source_snapshots s ON s.id=a.snapshot_id
   WHERE a.id=NEW.raw_artifact_id
     AND a.snapshot_id=NEW.snapshot_id
     AND s.source_id=NEW.source_id
     AND a.sha256=NEW.sha256
     AND a.bytes=NEW.byte_size
 ) THEN RAISE(ABORT,'package raw artifact canonical lineage mismatch') END;
END;

CREATE TRIGGER package_evidence_raw_bindings_validate_insert
BEFORE INSERT ON package_evidence_raw_bindings
BEGIN
 SELECT CASE WHEN NOT EXISTS (
   SELECT 1 FROM evidence_records e
   WHERE e.id=NEW.evidence_id
     AND e.source_id=NEW.source_id
     AND e.snapshot_id=NEW.snapshot_id
     AND e.run_id=NEW.normalization_run_id
 ) THEN RAISE(ABORT,'package Evidence-to-Raw binding lineage mismatch') END;
END;

-- Raw claim grounding may cite only material audited in the originating Package.
CREATE TRIGGER raw_grounding_links_validate_insert
BEFORE INSERT ON raw_grounding_links
BEGIN
 SELECT CASE WHEN NOT EXISTS (
   SELECT 1 FROM package_raw_artifacts p
   WHERE p.package_id=NEW.package_id AND p.raw_artifact_id=NEW.raw_artifact_id
 ) THEN RAISE(ABORT,'raw grounding artifact must belong to package') END;
 SELECT CASE WHEN NEW.target_kind='statement' AND NOT EXISTS (
   SELECT 1 FROM knowledge_statements WHERE id=NEW.target_id AND version_id=NEW.version_id
 ) THEN RAISE(ABORT,'statement raw grounding target must belong to version') END;
 SELECT CASE WHEN NEW.target_kind='attribute' AND NOT EXISTS (
   SELECT 1 FROM object_version_attributes WHERE id=NEW.target_id AND version_id=NEW.version_id
 ) THEN RAISE(ABORT,'attribute raw grounding target must belong to version') END;
 SELECT CASE WHEN NEW.target_kind='relation' AND NOT EXISTS (
   SELECT 1 FROM object_relations WHERE id=NEW.target_id AND version_id=NEW.version_id
 ) THEN RAISE(ABORT,'relation raw grounding target must belong to version') END;
 SELECT CASE WHEN NEW.origin_kind='result_import' AND NOT EXISTS (
   SELECT 1 FROM object_result_imports i
   WHERE i.id=NEW.origin_ref AND i.version_id=NEW.version_id AND i.package_id=NEW.package_id
 ) THEN RAISE(ABORT,'result-import raw grounding origin mismatch') END;
END;

CREATE TRIGGER raw_grounding_links_terminal_insert
BEFORE INSERT ON raw_grounding_links
WHEN EXISTS (
  SELECT 1 FROM object_version_lifecycle l
  WHERE l.version_id=NEW.version_id AND l.state IN ('accepted','abandoned')
)
BEGIN SELECT RAISE(ABORT,'terminal version content is immutable'); END;

CREATE TRIGGER raw_grounding_links_terminal_update
BEFORE UPDATE ON raw_grounding_links
WHEN EXISTS (
  SELECT 1 FROM object_version_lifecycle l
  WHERE l.version_id=OLD.version_id AND l.state IN ('accepted','abandoned')
)
BEGIN SELECT RAISE(ABORT,'terminal version content is immutable'); END;

CREATE TRIGGER raw_grounding_links_terminal_delete
BEFORE DELETE ON raw_grounding_links
WHEN EXISTS (
  SELECT 1 FROM object_version_lifecycle l
  WHERE l.version_id=OLD.version_id AND l.state IN ('accepted','abandoned')
)
BEGIN SELECT RAISE(ABORT,'terminal version content is immutable'); END;
