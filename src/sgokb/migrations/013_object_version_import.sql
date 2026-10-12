-- Phase H / H-02: atomic Object Result import provenance and review metadata.

CREATE TABLE object_result_imports (
    id TEXT PRIMARY KEY,
    receipt_id TEXT NOT NULL UNIQUE REFERENCES package_result_receipts(id),
    package_id TEXT NOT NULL REFERENCES package_exchange_records(package_id),
    manifest_sha256 TEXT NOT NULL,
    result_sha256 TEXT NOT NULL,
    result_byte_count INTEGER NOT NULL CHECK(result_byte_count >= 0),
    result_storage_ref TEXT NOT NULL,
    object_id TEXT NOT NULL REFERENCES objects(id),
    base_version_id TEXT REFERENCES object_versions(id),
    version_id TEXT NOT NULL UNIQUE REFERENCES object_versions(id),
    result_status TEXT NOT NULL CHECK(result_status IN ('complete','partial','insufficient_evidence')),
    validation_completed_at TEXT NOT NULL,
    validation_findings_json TEXT NOT NULL CHECK(json_valid(validation_findings_json)),
    review_acknowledged INTEGER NOT NULL CHECK(review_acknowledged IN (0,1)),
    imported_at TEXT NOT NULL,
    UNIQUE(package_id,result_sha256)
);
CREATE INDEX object_result_imports_object ON object_result_imports(object_id,imported_at);

CREATE TABLE object_version_result_metadata (
    version_id TEXT PRIMARY KEY REFERENCES object_versions(id),
    import_id TEXT NOT NULL UNIQUE REFERENCES object_result_imports(id),
    default_language TEXT NOT NULL,
    generation_json TEXT NOT NULL CHECK(json_valid(generation_json)),
    conflicts_json TEXT NOT NULL CHECK(json_valid(conflicts_json)),
    gaps_json TEXT NOT NULL CHECK(json_valid(gaps_json)),
    unresolved_references_json TEXT NOT NULL CHECK(json_valid(unresolved_references_json)),
    registry_proposals_json TEXT NOT NULL CHECK(json_valid(registry_proposals_json)),
    class_extensions_json TEXT NOT NULL CHECK(json_valid(class_extensions_json)),
    created_at TEXT NOT NULL
);

CREATE TABLE knowledge_statement_attributions (
    statement_id TEXT PRIMARY KEY REFERENCES knowledge_statements(id),
    kind TEXT NOT NULL CHECK(kind IN ('source','object','named_actor','community')),
    source_id TEXT REFERENCES source_records(id),
    object_id TEXT REFERENCES objects(id),
    label TEXT,
    created_at TEXT NOT NULL,
    CHECK(
      (kind='source' AND source_id IS NOT NULL)
      OR (kind='object' AND object_id IS NOT NULL)
      OR (kind IN ('named_actor','community')
          AND label IS NOT NULL AND length(trim(label)) > 0)
    )
);

-- Import audit and accepted Result metadata are immutable.
CREATE TRIGGER object_result_imports_immutable_update
BEFORE UPDATE ON object_result_imports
BEGIN SELECT RAISE(ABORT,'Object Result import audit is immutable'); END;
CREATE TRIGGER object_result_imports_immutable_delete
BEFORE DELETE ON object_result_imports
BEGIN SELECT RAISE(ABORT,'Object Result import audit is immutable'); END;

CREATE TRIGGER version_result_metadata_terminal_insert
BEFORE INSERT ON object_version_result_metadata
WHEN EXISTS (SELECT 1 FROM object_version_lifecycle l
             WHERE l.version_id=NEW.version_id AND l.state IN ('accepted','abandoned'))
BEGIN SELECT RAISE(ABORT,'terminal version content is immutable'); END;
CREATE TRIGGER version_result_metadata_terminal_update
BEFORE UPDATE ON object_version_result_metadata
WHEN EXISTS (SELECT 1 FROM object_version_lifecycle l
             WHERE l.version_id=OLD.version_id AND l.state IN ('accepted','abandoned'))
BEGIN SELECT RAISE(ABORT,'terminal version content is immutable'); END;
CREATE TRIGGER version_result_metadata_terminal_delete
BEFORE DELETE ON object_version_result_metadata
WHEN EXISTS (SELECT 1 FROM object_version_lifecycle l
             WHERE l.version_id=OLD.version_id AND l.state IN ('accepted','abandoned'))
BEGIN SELECT RAISE(ABORT,'terminal version content is immutable'); END;

CREATE TRIGGER statement_attributions_terminal_insert
BEFORE INSERT ON knowledge_statement_attributions
WHEN EXISTS (
  SELECT 1 FROM knowledge_statements s JOIN object_version_lifecycle l ON l.version_id=s.version_id
  WHERE s.id=NEW.statement_id AND l.state IN ('accepted','abandoned')
)
BEGIN SELECT RAISE(ABORT,'terminal version content is immutable'); END;
CREATE TRIGGER statement_attributions_terminal_update
BEFORE UPDATE ON knowledge_statement_attributions
WHEN EXISTS (
  SELECT 1 FROM knowledge_statements s JOIN object_version_lifecycle l ON l.version_id=s.version_id
  WHERE s.id=OLD.statement_id AND l.state IN ('accepted','abandoned')
)
BEGIN SELECT RAISE(ABORT,'terminal version content is immutable'); END;
CREATE TRIGGER statement_attributions_terminal_delete
BEFORE DELETE ON knowledge_statement_attributions
WHEN EXISTS (
  SELECT 1 FROM knowledge_statements s JOIN object_version_lifecycle l ON l.version_id=s.version_id
  WHERE s.id=OLD.statement_id AND l.state IN ('accepted','abandoned')
)
BEGIN SELECT RAISE(ABORT,'terminal version content is immutable'); END;

-- WOK-05: attribution is canonical content for reported_view Statements only.
CREATE TRIGGER statement_attributions_reported_view_insert
BEFORE INSERT ON knowledge_statement_attributions
BEGIN
 SELECT CASE WHEN NOT EXISTS (
   SELECT 1 FROM knowledge_statements
   WHERE id=NEW.statement_id AND derivation_kind='reported_view'
 ) THEN RAISE(ABORT,'attribution requires reported_view statement') END;
END;

CREATE TRIGGER reported_view_requires_attribution_accept
BEFORE UPDATE OF state ON object_version_lifecycle
WHEN OLD.state='candidate' AND NEW.state='accepted'
BEGIN
 SELECT CASE WHEN EXISTS (
   SELECT 1 FROM knowledge_statements s
   WHERE s.version_id=OLD.version_id AND s.derivation_kind='reported_view'
     AND NOT EXISTS (
       SELECT 1 FROM knowledge_statement_attributions a WHERE a.statement_id=s.id
     )
 ) THEN RAISE(ABORT,'accepted reported_view requires attribution') END;
END;
