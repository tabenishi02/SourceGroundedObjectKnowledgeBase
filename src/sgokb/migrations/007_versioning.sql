-- Phase E / E-04: Object Knowledge Version lifecycle, immutable accepted snapshots,
-- rollback/current promotion, classification snapshots, and derived-state handoff.
-- Additive only: object_versions remains the stable E-01 identity table.

CREATE TABLE object_version_lifecycle (
 version_id TEXT PRIMARY KEY REFERENCES object_versions(id),
 base_version_id TEXT REFERENCES object_versions(id),
 state TEXT NOT NULL DEFAULT 'candidate' CHECK(state IN ('candidate','accepted','abandoned')),
 snapshot_kind TEXT NOT NULL DEFAULT 'full' CHECK(snapshot_kind='full'),
 accepted_at TEXT,
 abandoned_at TEXT,
 created_at TEXT NOT NULL,
 CHECK((state='accepted' AND accepted_at IS NOT NULL AND abandoned_at IS NULL)
    OR (state='abandoned' AND accepted_at IS NULL AND abandoned_at IS NOT NULL)
    OR (state='candidate' AND accepted_at IS NULL AND abandoned_at IS NULL))
);
CREATE INDEX object_version_lifecycle_base ON object_version_lifecycle(base_version_id);
CREATE INDEX object_version_lifecycle_state ON object_version_lifecycle(state,version_id);

CREATE TABLE object_version_classification_snapshots (
 version_id TEXT PRIMARY KEY REFERENCES object_versions(id),
 primary_class_id TEXT NOT NULL REFERENCES object_classes(id),
 created_at TEXT NOT NULL
);

CREATE TABLE object_version_additional_class_snapshots (
 version_id TEXT NOT NULL REFERENCES object_versions(id),
 class_id TEXT NOT NULL REFERENCES object_classes(id),
 created_at TEXT NOT NULL,
 PRIMARY KEY(version_id,class_id)
);
CREATE INDEX object_version_additional_class_lookup
 ON object_version_additional_class_snapshots(class_id,version_id);

CREATE TABLE object_version_events (
 id TEXT PRIMARY KEY,
 version_id TEXT NOT NULL REFERENCES object_versions(id),
 event_type TEXT NOT NULL CHECK(length(trim(event_type)) > 0),
 payload_json TEXT NOT NULL DEFAULT '{}' CHECK(json_valid(payload_json)),
 created_at TEXT NOT NULL
);
CREATE INDEX object_version_events_version ON object_version_events(version_id,created_at);

-- Mutable coordination metadata only. Canonical acceptance never waits for derived generation.
-- revision is a compare-and-set token so obsolete workers cannot mark a newer target ready.
CREATE TABLE object_derived_states (
 object_id TEXT NOT NULL REFERENCES objects(id),
 kind TEXT NOT NULL CHECK(length(trim(kind)) > 0),
 target_version_id TEXT NOT NULL REFERENCES object_versions(id),
 status TEXT NOT NULL CHECK(status IN ('pending','ready','failed','stale')),
 revision INTEGER NOT NULL DEFAULT 1 CHECK(revision >= 1),
 last_error TEXT,
 updated_at TEXT NOT NULL,
 PRIMARY KEY(object_id,kind)
);
CREATE INDEX object_derived_states_target ON object_derived_states(target_version_id,status);

-- Existing pre-E-04 canonical versions are historical persisted Knowledge, not candidates.
-- Best-effort lineage uses the greatest lower version number for the same Object.
INSERT INTO object_version_lifecycle(
 version_id,base_version_id,state,snapshot_kind,accepted_at,abandoned_at,created_at
)
SELECT v.id,
       (SELECT p.id FROM object_versions p
        WHERE p.object_id=v.object_id AND p.version_number < v.version_number
        ORDER BY p.version_number DESC LIMIT 1),
       'accepted','full',v.created_at,NULL,v.created_at
FROM object_versions v;

INSERT INTO object_version_classification_snapshots(version_id,primary_class_id,created_at)
SELECT v.id,o.primary_class_id,v.created_at
FROM object_versions v JOIN objects o ON o.id=v.object_id;

INSERT INTO object_version_additional_class_snapshots(version_id,class_id,created_at)
SELECT v.id,a.class_id,v.created_at
FROM object_versions v
JOIN object_additional_classes a ON a.object_id=v.object_id;

-- New low-level object_versions inserts remain compatible with E-01/E-02 callers.
-- They become candidate full snapshots and capture the current accepted base/classification.
CREATE TRIGGER object_versions_lifecycle_insert
AFTER INSERT ON object_versions
BEGIN
 INSERT INTO object_version_lifecycle(
   version_id,base_version_id,state,snapshot_kind,accepted_at,abandoned_at,created_at
 ) VALUES(
   NEW.id,
   (SELECT current_version_id FROM objects WHERE id=NEW.object_id),
   'candidate','full',NULL,NULL,NEW.created_at
 );
 INSERT INTO object_version_classification_snapshots(version_id,primary_class_id,created_at)
 SELECT NEW.id,primary_class_id,NEW.created_at FROM objects WHERE id=NEW.object_id;
 INSERT INTO object_version_additional_class_snapshots(version_id,class_id,created_at)
 SELECT NEW.id,class_id,NEW.created_at
 FROM object_additional_classes WHERE object_id=NEW.object_id;
END;

-- A base Version is lineage, not an arbitrary cross-Object reference.
CREATE TRIGGER object_version_lifecycle_base_insert
BEFORE INSERT ON object_version_lifecycle
WHEN NEW.base_version_id IS NOT NULL
BEGIN
 SELECT CASE WHEN NOT EXISTS (
   SELECT 1 FROM object_versions v
   JOIN object_versions b ON b.id=NEW.base_version_id
   WHERE v.id=NEW.version_id AND v.object_id=b.object_id
 ) THEN RAISE(ABORT,'base version must belong to same object') END;
END;

CREATE TRIGGER object_version_lifecycle_base_update
BEFORE UPDATE OF base_version_id ON object_version_lifecycle
WHEN NEW.base_version_id IS NOT OLD.base_version_id
BEGIN SELECT RAISE(ABORT,'version base is immutable'); END;

-- candidate -> accepted/abandoned are the only lifecycle transitions.
-- Acceptance also performs the stale-base and grounding-completeness gate.
CREATE TRIGGER object_version_lifecycle_transition
BEFORE UPDATE OF state ON object_version_lifecycle
WHEN NEW.state <> OLD.state
BEGIN
 SELECT CASE WHEN OLD.state <> 'candidate' OR NEW.state NOT IN ('accepted','abandoned')
   THEN RAISE(ABORT,'invalid version lifecycle transition') END;

 SELECT CASE WHEN NEW.state='accepted' AND EXISTS (
   SELECT 1 FROM object_versions v
   JOIN objects o ON o.id=v.object_id
   WHERE v.id=OLD.version_id AND o.current_version_id IS NOT OLD.base_version_id
 ) THEN RAISE(ABORT,'stale base version') END;

 SELECT CASE WHEN NEW.state='accepted' AND NOT EXISTS (
   SELECT 1 FROM object_version_classification_snapshots c
   WHERE c.version_id=OLD.version_id
 ) THEN RAISE(ABORT,'accepted version requires classification snapshot') END;

 SELECT CASE WHEN NEW.state='accepted' AND EXISTS (
   SELECT 1 FROM object_versions v
   JOIN objects o ON o.id=v.object_id
   JOIN object_version_classification_snapshots c ON c.version_id=v.id
   WHERE v.id=OLD.version_id AND c.primary_class_id <> o.primary_class_id
 ) THEN RAISE(ABORT,'stale classification snapshot') END;

 SELECT CASE WHEN NEW.state='accepted' AND (
   EXISTS (
     SELECT class_id FROM object_version_additional_class_snapshots WHERE version_id=OLD.version_id
     EXCEPT
     SELECT a.class_id FROM object_versions v
     JOIN object_additional_classes a ON a.object_id=v.object_id
     WHERE v.id=OLD.version_id
   ) OR EXISTS (
     SELECT a.class_id FROM object_versions v
     JOIN object_additional_classes a ON a.object_id=v.object_id
     WHERE v.id=OLD.version_id
     EXCEPT
     SELECT class_id FROM object_version_additional_class_snapshots WHERE version_id=OLD.version_id
   )
 ) THEN RAISE(ABORT,'stale classification snapshot') END;

 SELECT CASE WHEN NEW.state='accepted' AND EXISTS (
   SELECT 1 FROM object_version_facets f
   WHERE f.version_id=OLD.version_id AND f.status='content'
     AND NOT EXISTS (
       SELECT 1 FROM knowledge_statements s
       WHERE s.version_id=f.version_id AND s.facet_id=f.facet_id
     )
 ) THEN RAISE(ABORT,'content facet requires statement') END;

 SELECT CASE WHEN NEW.state='accepted' AND EXISTS (
   SELECT 1 FROM knowledge_statements s
   WHERE s.version_id=OLD.version_id AND NOT EXISTS (
     SELECT 1 FROM evidence_links e
     WHERE e.version_id=s.version_id AND e.target_kind='statement' AND e.target_id=s.id
   )
 ) THEN RAISE(ABORT,'accepted statement requires evidence') END;

 SELECT CASE WHEN NEW.state='accepted' AND EXISTS (
   SELECT 1 FROM object_version_attributes a
   WHERE a.version_id=OLD.version_id AND a.status='known' AND NOT EXISTS (
     SELECT 1 FROM evidence_links e
     WHERE e.version_id=a.version_id AND e.target_kind='attribute' AND e.target_id=a.id
   )
 ) THEN RAISE(ABORT,'accepted known attribute requires evidence') END;

 SELECT CASE WHEN NEW.state='accepted' AND EXISTS (
   SELECT 1 FROM object_relations r
   WHERE r.version_id=OLD.version_id AND NOT EXISTS (
     SELECT 1 FROM evidence_links e
     WHERE e.version_id=r.version_id AND e.target_kind='relation' AND e.target_id=r.id
   )
 ) THEN RAISE(ABORT,'accepted relation requires evidence') END;
END;

CREATE TRIGGER object_version_lifecycle_terminal_update
BEFORE UPDATE ON object_version_lifecycle
WHEN OLD.state IN ('accepted','abandoned')
BEGIN SELECT RAISE(ABORT,'terminal version lifecycle is immutable'); END;

CREATE TRIGGER object_version_lifecycle_terminal_delete
BEFORE DELETE ON object_version_lifecycle
WHEN OLD.state IN ('accepted','abandoned')
BEGIN SELECT RAISE(ABORT,'terminal version lifecycle is immutable'); END;

-- Version identity/ordinal cannot be edited once its lifecycle row exists.
CREATE TRIGGER object_versions_identity_immutable_e04
BEFORE UPDATE OF version_number,created_at ON object_versions
BEGIN SELECT RAISE(ABORT,'version identity is immutable'); END;

CREATE TRIGGER object_versions_accepted_delete
BEFORE DELETE ON object_versions
WHEN EXISTS (
 SELECT 1 FROM object_version_lifecycle l
 WHERE l.version_id=OLD.id AND l.state IN ('accepted','abandoned')
)
BEGIN SELECT RAISE(ABORT,'terminal version cannot be deleted'); END;

-- Replace E-01 current-pointer guards: current may reference accepted Versions only.
DROP TRIGGER objects_current_version_insert;
DROP TRIGGER objects_current_version_update;

CREATE TRIGGER objects_current_version_insert
BEFORE INSERT ON objects
WHEN NEW.current_version_id IS NOT NULL
BEGIN
 SELECT CASE WHEN NOT EXISTS (
   SELECT 1 FROM object_versions v
   JOIN object_version_lifecycle l ON l.version_id=v.id
   WHERE v.id=NEW.current_version_id AND v.object_id=NEW.id AND l.state='accepted'
 ) THEN RAISE(ABORT,'current version must belong to object and be accepted') END;
END;

CREATE TRIGGER objects_current_version_update
BEFORE UPDATE OF current_version_id ON objects
WHEN NEW.current_version_id IS NOT NULL
BEGIN
 SELECT CASE WHEN NOT EXISTS (
   SELECT 1 FROM object_versions v
   JOIN object_version_lifecycle l ON l.version_id=v.id
   WHERE v.id=NEW.current_version_id AND v.object_id=NEW.id AND l.state='accepted'
 ) THEN RAISE(ABORT,'current version must belong to object and be accepted') END;
END;

-- Accepted/abandoned classification snapshots are terminal content.
CREATE TRIGGER object_version_classification_terminal_insert
BEFORE INSERT ON object_version_classification_snapshots
WHEN EXISTS (
 SELECT 1 FROM object_version_lifecycle l
 WHERE l.version_id=NEW.version_id AND l.state IN ('accepted','abandoned')
)
BEGIN SELECT RAISE(ABORT,'terminal version content is immutable'); END;

CREATE TRIGGER object_version_classification_terminal_update
BEFORE UPDATE ON object_version_classification_snapshots
WHEN EXISTS (
 SELECT 1 FROM object_version_lifecycle l
 WHERE l.version_id=OLD.version_id AND l.state IN ('accepted','abandoned')
)
BEGIN SELECT RAISE(ABORT,'terminal version content is immutable'); END;

CREATE TRIGGER object_version_classification_terminal_delete
BEFORE DELETE ON object_version_classification_snapshots
WHEN EXISTS (
 SELECT 1 FROM object_version_lifecycle l
 WHERE l.version_id=OLD.version_id AND l.state IN ('accepted','abandoned')
)
BEGIN SELECT RAISE(ABORT,'terminal version content is immutable'); END;

CREATE TRIGGER object_version_additional_class_terminal_insert
BEFORE INSERT ON object_version_additional_class_snapshots
WHEN EXISTS (
 SELECT 1 FROM object_version_lifecycle l
 WHERE l.version_id=NEW.version_id AND l.state IN ('accepted','abandoned')
)
BEGIN SELECT RAISE(ABORT,'terminal version content is immutable'); END;

CREATE TRIGGER object_version_additional_class_terminal_update
BEFORE UPDATE ON object_version_additional_class_snapshots
WHEN EXISTS (
 SELECT 1 FROM object_version_lifecycle l
 WHERE l.version_id=OLD.version_id AND l.state IN ('accepted','abandoned')
)
BEGIN SELECT RAISE(ABORT,'terminal version content is immutable'); END;

CREATE TRIGGER object_version_additional_class_terminal_delete
BEFORE DELETE ON object_version_additional_class_snapshots
WHEN EXISTS (
 SELECT 1 FROM object_version_lifecycle l
 WHERE l.version_id=OLD.version_id AND l.state IN ('accepted','abandoned')
)
BEGIN SELECT RAISE(ABORT,'terminal version content is immutable'); END;

-- Direct version-scoped canonical tables: no insert/update/delete after terminalization.
CREATE TRIGGER version_facets_terminal_insert
BEFORE INSERT ON object_version_facets
WHEN EXISTS (SELECT 1 FROM object_version_lifecycle l WHERE l.version_id=NEW.version_id AND l.state IN ('accepted','abandoned'))
BEGIN SELECT RAISE(ABORT,'terminal version content is immutable'); END;
CREATE TRIGGER version_facets_terminal_update
BEFORE UPDATE ON object_version_facets
WHEN EXISTS (SELECT 1 FROM object_version_lifecycle l WHERE l.version_id=OLD.version_id AND l.state IN ('accepted','abandoned'))
BEGIN SELECT RAISE(ABORT,'terminal version content is immutable'); END;
CREATE TRIGGER version_facets_terminal_delete
BEFORE DELETE ON object_version_facets
WHEN EXISTS (SELECT 1 FROM object_version_lifecycle l WHERE l.version_id=OLD.version_id AND l.state IN ('accepted','abandoned'))
BEGIN SELECT RAISE(ABORT,'terminal version content is immutable'); END;

CREATE TRIGGER temporal_scopes_terminal_insert
BEFORE INSERT ON temporal_scopes
WHEN EXISTS (SELECT 1 FROM object_version_lifecycle l WHERE l.version_id=NEW.version_id AND l.state IN ('accepted','abandoned'))
BEGIN SELECT RAISE(ABORT,'terminal version content is immutable'); END;
CREATE TRIGGER temporal_scopes_terminal_update
BEFORE UPDATE ON temporal_scopes
WHEN EXISTS (SELECT 1 FROM object_version_lifecycle l WHERE l.version_id=OLD.version_id AND l.state IN ('accepted','abandoned'))
BEGIN SELECT RAISE(ABORT,'terminal version content is immutable'); END;
CREATE TRIGGER temporal_scopes_terminal_delete
BEFORE DELETE ON temporal_scopes
WHEN EXISTS (SELECT 1 FROM object_version_lifecycle l WHERE l.version_id=OLD.version_id AND l.state IN ('accepted','abandoned'))
BEGIN SELECT RAISE(ABORT,'terminal version content is immutable'); END;

CREATE TRIGGER statements_terminal_insert
BEFORE INSERT ON knowledge_statements
WHEN EXISTS (SELECT 1 FROM object_version_lifecycle l WHERE l.version_id=NEW.version_id AND l.state IN ('accepted','abandoned'))
BEGIN SELECT RAISE(ABORT,'terminal version content is immutable'); END;
CREATE TRIGGER statements_terminal_update
BEFORE UPDATE ON knowledge_statements
WHEN EXISTS (SELECT 1 FROM object_version_lifecycle l WHERE l.version_id=OLD.version_id AND l.state IN ('accepted','abandoned'))
BEGIN SELECT RAISE(ABORT,'terminal version content is immutable'); END;
CREATE TRIGGER statements_terminal_delete
BEFORE DELETE ON knowledge_statements
WHEN EXISTS (SELECT 1 FROM object_version_lifecycle l WHERE l.version_id=OLD.version_id AND l.state IN ('accepted','abandoned'))
BEGIN SELECT RAISE(ABORT,'terminal version content is immutable'); END;

CREATE TRIGGER attributes_terminal_insert
BEFORE INSERT ON object_version_attributes
WHEN EXISTS (SELECT 1 FROM object_version_lifecycle l WHERE l.version_id=NEW.version_id AND l.state IN ('accepted','abandoned'))
BEGIN SELECT RAISE(ABORT,'terminal version content is immutable'); END;
CREATE TRIGGER attributes_terminal_update
BEFORE UPDATE ON object_version_attributes
WHEN EXISTS (SELECT 1 FROM object_version_lifecycle l WHERE l.version_id=OLD.version_id AND l.state IN ('accepted','abandoned'))
BEGIN SELECT RAISE(ABORT,'terminal version content is immutable'); END;
CREATE TRIGGER attributes_terminal_delete
BEFORE DELETE ON object_version_attributes
WHEN EXISTS (SELECT 1 FROM object_version_lifecycle l WHERE l.version_id=OLD.version_id AND l.state IN ('accepted','abandoned'))
BEGIN SELECT RAISE(ABORT,'terminal version content is immutable'); END;

CREATE TRIGGER relations_terminal_insert
BEFORE INSERT ON object_relations
WHEN EXISTS (SELECT 1 FROM object_version_lifecycle l WHERE l.version_id=NEW.version_id AND l.state IN ('accepted','abandoned'))
BEGIN SELECT RAISE(ABORT,'terminal version content is immutable'); END;
CREATE TRIGGER relations_terminal_update
BEFORE UPDATE ON object_relations
WHEN EXISTS (SELECT 1 FROM object_version_lifecycle l WHERE l.version_id=OLD.version_id AND l.state IN ('accepted','abandoned'))
BEGIN SELECT RAISE(ABORT,'terminal version content is immutable'); END;
CREATE TRIGGER relations_terminal_delete
BEFORE DELETE ON object_relations
WHEN EXISTS (SELECT 1 FROM object_version_lifecycle l WHERE l.version_id=OLD.version_id AND l.state IN ('accepted','abandoned'))
BEGIN SELECT RAISE(ABORT,'terminal version content is immutable'); END;

CREATE TRIGGER evidence_links_terminal_insert
BEFORE INSERT ON evidence_links
WHEN EXISTS (SELECT 1 FROM object_version_lifecycle l WHERE l.version_id=NEW.version_id AND l.state IN ('accepted','abandoned'))
BEGIN SELECT RAISE(ABORT,'terminal version content is immutable'); END;
CREATE TRIGGER evidence_links_terminal_update
BEFORE UPDATE ON evidence_links
WHEN EXISTS (SELECT 1 FROM object_version_lifecycle l WHERE l.version_id=OLD.version_id AND l.state IN ('accepted','abandoned'))
BEGIN SELECT RAISE(ABORT,'terminal version content is immutable'); END;
CREATE TRIGGER evidence_links_terminal_delete
BEFORE DELETE ON evidence_links
WHEN EXISTS (SELECT 1 FROM object_version_lifecycle l WHERE l.version_id=OLD.version_id AND l.state IN ('accepted','abandoned'))
BEGIN SELECT RAISE(ABORT,'terminal version content is immutable'); END;

-- Relation temporal scope is indirect version content.
CREATE TRIGGER relation_temporal_terminal_insert
BEFORE INSERT ON relation_temporal_scopes
WHEN EXISTS (
 SELECT 1 FROM object_relations r JOIN object_version_lifecycle l ON l.version_id=r.version_id
 WHERE r.id=NEW.relation_id AND l.state IN ('accepted','abandoned')
)
BEGIN SELECT RAISE(ABORT,'terminal version content is immutable'); END;
CREATE TRIGGER relation_temporal_terminal_update
BEFORE UPDATE ON relation_temporal_scopes
WHEN EXISTS (
 SELECT 1 FROM object_relations r JOIN object_version_lifecycle l ON l.version_id=r.version_id
 WHERE r.id=OLD.relation_id AND l.state IN ('accepted','abandoned')
)
BEGIN SELECT RAISE(ABORT,'terminal version content is immutable'); END;
CREATE TRIGGER relation_temporal_terminal_delete
BEFORE DELETE ON relation_temporal_scopes
WHEN EXISTS (
 SELECT 1 FROM object_relations r JOIN object_version_lifecycle l ON l.version_id=r.version_id
 WHERE r.id=OLD.relation_id AND l.state IN ('accepted','abandoned')
)
BEGIN SELECT RAISE(ABORT,'terminal version content is immutable'); END;

-- Classification snapshot rows must remain valid and belong to assignable Classes.
CREATE TRIGGER object_version_classification_validate_insert
BEFORE INSERT ON object_version_classification_snapshots
BEGIN
 SELECT CASE WHEN NOT EXISTS (
   SELECT 1 FROM object_classes c
   WHERE c.id=NEW.primary_class_id AND c.assignment_policy='primary_eligible'
 ) THEN RAISE(ABORT,'version primary class snapshot must be primary_eligible') END;
END;

CREATE TRIGGER object_version_classification_validate_update
BEFORE UPDATE OF primary_class_id ON object_version_classification_snapshots
BEGIN
 SELECT CASE WHEN NOT EXISTS (
   SELECT 1 FROM object_classes c
   WHERE c.id=NEW.primary_class_id AND c.assignment_policy='primary_eligible'
 ) THEN RAISE(ABORT,'version primary class snapshot must be primary_eligible') END;
END;

CREATE TRIGGER object_version_additional_class_validate_insert
BEFORE INSERT ON object_version_additional_class_snapshots
BEGIN
 SELECT CASE WHEN NOT EXISTS (
   SELECT 1 FROM object_classes c
   WHERE c.id=NEW.class_id AND c.assignment_policy IN ('primary_eligible','additional_only')
 ) THEN RAISE(ABORT,'version additional class snapshot must be assignable') END;
 SELECT CASE WHEN EXISTS (
   SELECT 1 FROM object_version_classification_snapshots p
   WHERE p.version_id=NEW.version_id AND p.primary_class_id=NEW.class_id
 ) THEN RAISE(ABORT,'version additional class cannot equal primary class') END;
END;

CREATE TRIGGER object_version_additional_class_validate_update
BEFORE UPDATE OF class_id ON object_version_additional_class_snapshots
BEGIN
 SELECT CASE WHEN NOT EXISTS (
   SELECT 1 FROM object_classes c
   WHERE c.id=NEW.class_id AND c.assignment_policy IN ('primary_eligible','additional_only')
 ) THEN RAISE(ABORT,'version additional class snapshot must be assignable') END;
 SELECT CASE WHEN EXISTS (
   SELECT 1 FROM object_version_classification_snapshots p
   WHERE p.version_id=NEW.version_id AND p.primary_class_id=NEW.class_id
 ) THEN RAISE(ABORT,'version additional class cannot equal primary class') END;
END;

CREATE TRIGGER object_version_events_immutable_update
BEFORE UPDATE ON object_version_events
BEGIN SELECT RAISE(ABORT,'version event is immutable'); END;

CREATE TRIGGER object_version_events_immutable_delete
BEFORE DELETE ON object_version_events
BEGIN SELECT RAISE(ABORT,'version event is immutable'); END;
