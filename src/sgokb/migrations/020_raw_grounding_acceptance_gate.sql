-- Phase P / P-RAW-05 verification remediation.
-- Migration 019 introduced Raw claim grounding, but the E-04 lifecycle trigger still
-- required legacy evidence_links for every accepted claim. Replace that trigger so
-- accepted Knowledge requires at least one canonical grounding family: Evidence v1
-- or Raw v2. Existing v1 behavior and error messages remain compatible.

DROP TRIGGER object_version_lifecycle_transition;

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
   WHERE s.version_id=OLD.version_id
     AND NOT EXISTS (
       SELECT 1 FROM evidence_links e
       WHERE e.version_id=s.version_id AND e.target_kind='statement' AND e.target_id=s.id
     )
     AND NOT EXISTS (
       SELECT 1 FROM raw_grounding_links g
       WHERE g.version_id=s.version_id AND g.target_kind='statement' AND g.target_id=s.id
     )
 ) THEN RAISE(ABORT,'accepted statement requires evidence') END;

 SELECT CASE WHEN NEW.state='accepted' AND EXISTS (
   SELECT 1 FROM object_version_attributes a
   WHERE a.version_id=OLD.version_id AND a.status='known'
     AND NOT EXISTS (
       SELECT 1 FROM evidence_links e
       WHERE e.version_id=a.version_id AND e.target_kind='attribute' AND e.target_id=a.id
     )
     AND NOT EXISTS (
       SELECT 1 FROM raw_grounding_links g
       WHERE g.version_id=a.version_id AND g.target_kind='attribute' AND g.target_id=a.id
     )
 ) THEN RAISE(ABORT,'accepted known attribute requires evidence') END;

 SELECT CASE WHEN NEW.state='accepted' AND EXISTS (
   SELECT 1 FROM object_relations r
   WHERE r.version_id=OLD.version_id
     AND NOT EXISTS (
       SELECT 1 FROM evidence_links e
       WHERE e.version_id=r.version_id AND e.target_kind='relation' AND e.target_id=r.id
     )
     AND NOT EXISTS (
       SELECT 1 FROM raw_grounding_links g
       WHERE g.version_id=r.version_id AND g.target_kind='relation' AND g.target_id=r.id
     )
 ) THEN RAISE(ABORT,'accepted relation requires evidence') END;
END;
