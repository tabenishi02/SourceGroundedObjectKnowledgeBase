-- Phase E / E-01: canonical Object identity, classification, relation, and version reference skeleton.
-- This migration is additive. Prototype entities/fragments/documents remain untouched until Phase L.

CREATE TABLE object_classes (
 id TEXT PRIMARY KEY,
 key TEXT NOT NULL UNIQUE,
 name TEXT NOT NULL,
 description TEXT NOT NULL DEFAULT '',
 assignment_policy TEXT NOT NULL CHECK(assignment_policy IN ('structural','primary_eligible','additional_only')),
 status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active','archived')),
 created_at TEXT NOT NULL,
 updated_at TEXT NOT NULL
);

CREATE TABLE object_class_parents (
 child_class_id TEXT NOT NULL REFERENCES object_classes(id),
 parent_class_id TEXT NOT NULL REFERENCES object_classes(id),
 created_at TEXT NOT NULL,
 PRIMARY KEY(child_class_id,parent_class_id),
 CHECK(child_class_id <> parent_class_id)
);

CREATE TABLE objects (
 id TEXT PRIMARY KEY,
 name TEXT NOT NULL CHECK(length(trim(name)) > 0),
 primary_class_id TEXT NOT NULL REFERENCES object_classes(id),
 status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active','archived')),
 current_version_id TEXT REFERENCES object_versions(id),
 created_at TEXT NOT NULL,
 updated_at TEXT NOT NULL
);

CREATE TABLE object_versions (
 id TEXT PRIMARY KEY,
 object_id TEXT NOT NULL REFERENCES objects(id),
 version_number INTEGER NOT NULL CHECK(version_number >= 1),
 created_at TEXT NOT NULL,
 UNIQUE(object_id,version_number),
 UNIQUE(id,object_id)
);

CREATE TABLE object_aliases (
 id TEXT PRIMARY KEY,
 object_id TEXT NOT NULL REFERENCES objects(id),
 value TEXT NOT NULL CHECK(length(trim(value)) > 0),
 language TEXT,
 kind TEXT NOT NULL DEFAULT 'alias',
 created_at TEXT NOT NULL
);
CREATE UNIQUE INDEX object_aliases_unique
 ON object_aliases(object_id,value,ifnull(language,''),kind);

CREATE TABLE object_additional_classes (
 object_id TEXT NOT NULL REFERENCES objects(id),
 class_id TEXT NOT NULL REFERENCES object_classes(id),
 created_at TEXT NOT NULL,
 PRIMARY KEY(object_id,class_id)
);

CREATE TABLE relation_types (
 id TEXT PRIMARY KEY,
 key TEXT NOT NULL UNIQUE,
 name TEXT NOT NULL,
 description TEXT NOT NULL DEFAULT '',
 status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active','archived')),
 created_at TEXT NOT NULL,
 updated_at TEXT NOT NULL
);

CREATE TABLE object_relations (
 id TEXT PRIMARY KEY,
 version_id TEXT NOT NULL REFERENCES object_versions(id),
 subject_object_id TEXT NOT NULL REFERENCES objects(id),
 relation_type_id TEXT NOT NULL REFERENCES relation_types(id),
 object_object_id TEXT NOT NULL REFERENCES objects(id),
 created_at TEXT NOT NULL,
 UNIQUE(version_id,subject_object_id,relation_type_id,object_object_id)
);

CREATE TABLE object_registry_events (
 id TEXT PRIMARY KEY,
 object_id TEXT NOT NULL REFERENCES objects(id),
 event_type TEXT NOT NULL,
 payload TEXT NOT NULL,
 created_at TEXT NOT NULL
);

CREATE TABLE object_class_proposals (
 id TEXT PRIMARY KEY,
 proposed_key TEXT NOT NULL,
 display_name TEXT NOT NULL,
 description TEXT NOT NULL DEFAULT '',
 rationale TEXT NOT NULL,
 payload TEXT NOT NULL,
 status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','accepted','rejected')),
 resolved_class_id TEXT REFERENCES object_classes(id),
 created_at TEXT NOT NULL,
 reviewed_at TEXT
);

CREATE INDEX objects_name ON objects(name);
CREATE INDEX objects_primary_class ON objects(primary_class_id,status);
CREATE INDEX object_aliases_object ON object_aliases(object_id);
CREATE INDEX object_additional_classes_class ON object_additional_classes(class_id,object_id);
CREATE INDEX object_class_parents_parent ON object_class_parents(parent_class_id,child_class_id);
CREATE INDEX object_versions_object ON object_versions(object_id,version_number);
CREATE INDEX object_relations_subject ON object_relations(subject_object_id,relation_type_id);
CREATE INDEX object_relations_object ON object_relations(object_object_id,relation_type_id);
CREATE INDEX object_relations_version ON object_relations(version_id);
CREATE INDEX object_registry_events_object ON object_registry_events(object_id,created_at);
CREATE INDEX object_class_proposals_status ON object_class_proposals(status,created_at);

CREATE TRIGGER object_class_parents_no_cycle_insert
BEFORE INSERT ON object_class_parents
BEGIN
 SELECT CASE WHEN EXISTS (
   WITH RECURSIVE ancestors(class_id) AS (
     SELECT NEW.parent_class_id
     UNION
     SELECT p.parent_class_id
     FROM object_class_parents p
     JOIN ancestors a ON p.child_class_id=a.class_id
   )
   SELECT 1 FROM ancestors WHERE class_id=NEW.child_class_id
 ) THEN RAISE(ABORT,'class hierarchy cycle') END;
END;

CREATE TRIGGER object_class_parents_no_cycle_update
BEFORE UPDATE OF child_class_id,parent_class_id ON object_class_parents
BEGIN
 SELECT CASE WHEN EXISTS (
   WITH RECURSIVE ancestors(class_id) AS (
     SELECT NEW.parent_class_id
     UNION
     SELECT p.parent_class_id
     FROM object_class_parents p
     JOIN ancestors a ON p.child_class_id=a.class_id
     WHERE NOT (p.child_class_id=OLD.child_class_id AND p.parent_class_id=OLD.parent_class_id)
   )
   SELECT 1 FROM ancestors WHERE class_id=NEW.child_class_id
 ) THEN RAISE(ABORT,'class hierarchy cycle') END;
END;

CREATE TRIGGER objects_primary_class_insert
BEFORE INSERT ON objects
BEGIN
 SELECT CASE WHEN NOT EXISTS (
   SELECT 1 FROM object_classes
   WHERE id=NEW.primary_class_id AND status='active' AND assignment_policy='primary_eligible'
 ) THEN RAISE(ABORT,'primary class must be active and primary_eligible') END;
END;

CREATE TRIGGER objects_primary_class_update
BEFORE UPDATE OF primary_class_id ON objects
BEGIN
 SELECT CASE WHEN NOT EXISTS (
   SELECT 1 FROM object_classes
   WHERE id=NEW.primary_class_id AND status='active' AND assignment_policy='primary_eligible'
 ) THEN RAISE(ABORT,'primary class must be active and primary_eligible') END;
 SELECT CASE WHEN EXISTS (
   SELECT 1 FROM object_additional_classes
   WHERE object_id=NEW.id AND class_id=NEW.primary_class_id
 ) THEN RAISE(ABORT,'primary class cannot also be additional') END;
END;

CREATE TRIGGER object_additional_classes_insert
BEFORE INSERT ON object_additional_classes
BEGIN
 SELECT CASE WHEN NOT EXISTS (
   SELECT 1 FROM object_classes
   WHERE id=NEW.class_id AND status='active'
     AND assignment_policy IN ('primary_eligible','additional_only')
 ) THEN RAISE(ABORT,'additional class must be active and assignable') END;
 SELECT CASE WHEN EXISTS (
   SELECT 1 FROM objects
   WHERE id=NEW.object_id AND primary_class_id=NEW.class_id
 ) THEN RAISE(ABORT,'additional class cannot equal primary class') END;
END;

CREATE TRIGGER object_additional_classes_update
BEFORE UPDATE OF object_id,class_id ON object_additional_classes
BEGIN
 SELECT CASE WHEN NOT EXISTS (
   SELECT 1 FROM object_classes
   WHERE id=NEW.class_id AND status='active'
     AND assignment_policy IN ('primary_eligible','additional_only')
 ) THEN RAISE(ABORT,'additional class must be active and assignable') END;
 SELECT CASE WHEN EXISTS (
   SELECT 1 FROM objects
   WHERE id=NEW.object_id AND primary_class_id=NEW.class_id
 ) THEN RAISE(ABORT,'additional class cannot equal primary class') END;
END;

CREATE TRIGGER objects_current_version_insert
BEFORE INSERT ON objects
WHEN NEW.current_version_id IS NOT NULL
BEGIN
 SELECT CASE WHEN NOT EXISTS (
   SELECT 1 FROM object_versions
   WHERE id=NEW.current_version_id AND object_id=NEW.id
 ) THEN RAISE(ABORT,'current version must belong to object') END;
END;

CREATE TRIGGER objects_current_version_update
BEFORE UPDATE OF current_version_id ON objects
WHEN NEW.current_version_id IS NOT NULL
BEGIN
 SELECT CASE WHEN NOT EXISTS (
   SELECT 1 FROM object_versions
   WHERE id=NEW.current_version_id AND object_id=NEW.id
 ) THEN RAISE(ABORT,'current version must belong to object') END;
END;

-- B-02D canonical initial Class Registry seed. Fixed IDs make fresh DBs deterministic.
INSERT INTO object_classes(id,key,name,description,assignment_policy,status,created_at,updated_at) VALUES
 ('class:object_class','object_class','ObjectClass','Root classification class','structural','active','2026-10-12T00:00:00Z','2026-10-12T00:00:00Z'),
 ('class:fictional_entity','fictional_entity','FictionalEntity','Cross-cutting fictional entity classification','additional_only','active','2026-10-12T00:00:00Z','2026-10-12T00:00:00Z'),
 ('class:agent','agent','Agent','Actor or agent family','structural','active','2026-10-12T00:00:00Z','2026-10-12T00:00:00Z'),
 ('class:character','character','Character','Fictional character','primary_eligible','active','2026-10-12T00:00:00Z','2026-10-12T00:00:00Z'),
 ('class:person','person','Person','Real or historical person','primary_eligible','active','2026-10-12T00:00:00Z','2026-10-12T00:00:00Z'),
 ('class:organization','organization','Organization','Institutional organization','primary_eligible','active','2026-10-12T00:00:00Z','2026-10-12T00:00:00Z'),
 ('class:group','group','Group','Named group of agents','primary_eligible','active','2026-10-12T00:00:00Z','2026-10-12T00:00:00Z'),
 ('class:team','team','Team','Purpose-oriented group or team','primary_eligible','active','2026-10-12T00:00:00Z','2026-10-12T00:00:00Z'),
 ('class:faction','faction','Faction','Political, military, or ideological faction','primary_eligible','active','2026-10-12T00:00:00Z','2026-10-12T00:00:00Z'),
 ('class:creature','creature','Creature','Individually identifiable non-human creature','primary_eligible','active','2026-10-12T00:00:00Z','2026-10-12T00:00:00Z'),
 ('class:creative_work','creative_work','CreativeWork','Creative work family','structural','active','2026-10-12T00:00:00Z','2026-10-12T00:00:00Z'),
 ('class:work','work','Work','Individual creative work','primary_eligible','active','2026-10-12T00:00:00Z','2026-10-12T00:00:00Z'),
 ('class:adaptation','adaptation','Adaptation','Adaptation of another work','primary_eligible','active','2026-10-12T00:00:00Z','2026-10-12T00:00:00Z'),
 ('class:work_edition','work_edition','WorkEdition','Edition, remake, or revised work','primary_eligible','active','2026-10-12T00:00:00Z','2026-10-12T00:00:00Z'),
 ('class:series','series','Series','Series of works or components','primary_eligible','active','2026-10-12T00:00:00Z','2026-10-12T00:00:00Z'),
 ('class:franchise','franchise','Franchise','Cross-media franchise or IP grouping','primary_eligible','active','2026-10-12T00:00:00Z','2026-10-12T00:00:00Z'),
 ('class:work_component','work_component','WorkComponent','Structural family for work components','structural','active','2026-10-12T00:00:00Z','2026-10-12T00:00:00Z'),
 ('class:episode','episode','Episode','Episode component','primary_eligible','active','2026-10-12T00:00:00Z','2026-10-12T00:00:00Z'),
 ('class:chapter','chapter','Chapter','Chapter component','primary_eligible','active','2026-10-12T00:00:00Z','2026-10-12T00:00:00Z'),
 ('class:volume','volume','Volume','Volume component','primary_eligible','active','2026-10-12T00:00:00Z','2026-10-12T00:00:00Z'),
 ('class:season','season','Season','Season component','primary_eligible','active','2026-10-12T00:00:00Z','2026-10-12T00:00:00Z'),
 ('class:arc','arc','Arc','Narrative arc component','primary_eligible','active','2026-10-12T00:00:00Z','2026-10-12T00:00:00Z'),
 ('class:place','place','Place','Geographic or facility-like place','primary_eligible','active','2026-10-12T00:00:00Z','2026-10-12T00:00:00Z'),
 ('class:world','world','World','World, universe, or world-space','primary_eligible','active','2026-10-12T00:00:00Z','2026-10-12T00:00:00Z'),
 ('class:event','event','Event','Time-identifiable event','primary_eligible','active','2026-10-12T00:00:00Z','2026-10-12T00:00:00Z'),
 ('class:artifact','artifact','Artifact','Individually identifiable artificial object','primary_eligible','active','2026-10-12T00:00:00Z','2026-10-12T00:00:00Z'),
 ('class:product','product','Product','Commercial product or product model','primary_eligible','active','2026-10-12T00:00:00Z','2026-10-12T00:00:00Z'),
 ('class:taxon','taxon','Taxon','Taxonomic knowledge object','primary_eligible','active','2026-10-12T00:00:00Z','2026-10-12T00:00:00Z'),
 ('class:species','species','Species','Biological species','primary_eligible','active','2026-10-12T00:00:00Z','2026-10-12T00:00:00Z'),
 ('class:fictional_race','fictional_race','FictionalRace','Fictional species or race','primary_eligible','active','2026-10-12T00:00:00Z','2026-10-12T00:00:00Z'),
 ('class:concept','concept','Concept','Abstract concept','primary_eligible','active','2026-10-12T00:00:00Z','2026-10-12T00:00:00Z'),
 ('class:theme','theme','Theme','Theme or motif concept','primary_eligible','active','2026-10-12T00:00:00Z','2026-10-12T00:00:00Z'),
 ('class:ideology','ideology','Ideology','Ideology, doctrine, or philosophy','primary_eligible','active','2026-10-12T00:00:00Z','2026-10-12T00:00:00Z'),
 ('class:trait','trait','Trait','Trait concept','primary_eligible','active','2026-10-12T00:00:00Z','2026-10-12T00:00:00Z'),
 ('class:emotion','emotion','Emotion','Emotion concept','primary_eligible','active','2026-10-12T00:00:00Z','2026-10-12T00:00:00Z'),
 ('class:motivation','motivation','Motivation','Motivation concept','primary_eligible','active','2026-10-12T00:00:00Z','2026-10-12T00:00:00Z'),
 ('class:state_concept','state_concept','StateConcept','State concept with independent knowledge','primary_eligible','active','2026-10-12T00:00:00Z','2026-10-12T00:00:00Z'),
 ('class:role_concept','role_concept','RoleConcept','Role, occupation, or title concept','primary_eligible','active','2026-10-12T00:00:00Z','2026-10-12T00:00:00Z'),
 ('class:artifact_type_concept','artifact_type_concept','ArtifactTypeConcept','Generic artifact type concept','primary_eligible','active','2026-10-12T00:00:00Z','2026-10-12T00:00:00Z'),
 ('class:capability','capability','Capability','Capability family','structural','active','2026-10-12T00:00:00Z','2026-10-12T00:00:00Z'),
 ('class:ability','ability','Ability','Named ability or capability','primary_eligible','active','2026-10-12T00:00:00Z','2026-10-12T00:00:00Z'),
 ('class:skill','skill','Skill','Learnable skill or technique','primary_eligible','active','2026-10-12T00:00:00Z','2026-10-12T00:00:00Z'),
 ('class:process','process','Process','Process with stages, inputs, or outputs','primary_eligible','active','2026-10-12T00:00:00Z','2026-10-12T00:00:00Z'),
 ('class:action','action','Action','Action type','primary_eligible','active','2026-10-12T00:00:00Z','2026-10-12T00:00:00Z'),
 ('class:activity','activity','Activity','Continuing activity type','primary_eligible','active','2026-10-12T00:00:00Z','2026-10-12T00:00:00Z'),
 ('class:temporal_entity','temporal_entity','TemporalEntity','Temporal knowledge family','structural','active','2026-10-12T00:00:00Z','2026-10-12T00:00:00Z'),
 ('class:period','period','Period','Named period','primary_eligible','active','2026-10-12T00:00:00Z','2026-10-12T00:00:00Z'),
 ('class:era','era','Era','Historical or fictional era','primary_eligible','active','2026-10-12T00:00:00Z','2026-10-12T00:00:00Z'),
 ('class:timeline','timeline','Timeline','Timeline or time-series context','primary_eligible','active','2026-10-12T00:00:00Z','2026-10-12T00:00:00Z'),
 ('class:continuity','continuity','Continuity','Continuity or world-line context','primary_eligible','active','2026-10-12T00:00:00Z','2026-10-12T00:00:00Z'),
 ('class:system','system','System','Rule- or component-bearing system','primary_eligible','active','2026-10-12T00:00:00Z','2026-10-12T00:00:00Z'),
 ('class:software','software','Software','Software system or application','primary_eligible','active','2026-10-12T00:00:00Z','2026-10-12T00:00:00Z'),
 ('class:service','service','Service','Continuously provided service','primary_eligible','active','2026-10-12T00:00:00Z','2026-10-12T00:00:00Z'),
 ('class:rule_system','rule_system','RuleSystem','Rule-governed system','primary_eligible','active','2026-10-12T00:00:00Z','2026-10-12T00:00:00Z'),
 ('class:material','material','Material','Material knowledge object','primary_eligible','active','2026-10-12T00:00:00Z','2026-10-12T00:00:00Z'),
 ('class:substance','substance','Substance','Chemically or physically identified substance','primary_eligible','active','2026-10-12T00:00:00Z','2026-10-12T00:00:00Z'),
 ('class:phenomenon','phenomenon','Phenomenon','Repeatable phenomenon type','primary_eligible','active','2026-10-12T00:00:00Z','2026-10-12T00:00:00Z'),
 ('class:natural_phenomenon','natural_phenomenon','NaturalPhenomenon','Natural phenomenon','primary_eligible','active','2026-10-12T00:00:00Z','2026-10-12T00:00:00Z'),
 ('class:social_phenomenon','social_phenomenon','SocialPhenomenon','Social phenomenon','primary_eligible','active','2026-10-12T00:00:00Z','2026-10-12T00:00:00Z'),
 ('class:symbolic_system','symbolic_system','SymbolicSystem','Symbolic system family','structural','active','2026-10-12T00:00:00Z','2026-10-12T00:00:00Z'),
 ('class:language','language','Language','Natural, artificial, or fictional language','primary_eligible','active','2026-10-12T00:00:00Z','2026-10-12T00:00:00Z'),
 ('class:writing_system','writing_system','WritingSystem','Writing system','primary_eligible','active','2026-10-12T00:00:00Z','2026-10-12T00:00:00Z');

INSERT INTO object_class_parents(child_class_id,parent_class_id,created_at) VALUES
 ('class:fictional_entity','class:object_class','2026-10-12T00:00:00Z'),
 ('class:agent','class:object_class','2026-10-12T00:00:00Z'),
 ('class:character','class:agent','2026-10-12T00:00:00Z'),
 ('class:character','class:fictional_entity','2026-10-12T00:00:00Z'),
 ('class:person','class:agent','2026-10-12T00:00:00Z'),
 ('class:organization','class:agent','2026-10-12T00:00:00Z'),
 ('class:group','class:agent','2026-10-12T00:00:00Z'),
 ('class:team','class:group','2026-10-12T00:00:00Z'),
 ('class:faction','class:group','2026-10-12T00:00:00Z'),
 ('class:creature','class:agent','2026-10-12T00:00:00Z'),
 ('class:creative_work','class:object_class','2026-10-12T00:00:00Z'),
 ('class:work','class:creative_work','2026-10-12T00:00:00Z'),
 ('class:adaptation','class:work','2026-10-12T00:00:00Z'),
 ('class:work_edition','class:work','2026-10-12T00:00:00Z'),
 ('class:series','class:creative_work','2026-10-12T00:00:00Z'),
 ('class:franchise','class:creative_work','2026-10-12T00:00:00Z'),
 ('class:work_component','class:creative_work','2026-10-12T00:00:00Z'),
 ('class:episode','class:work_component','2026-10-12T00:00:00Z'),
 ('class:chapter','class:work_component','2026-10-12T00:00:00Z'),
 ('class:volume','class:work_component','2026-10-12T00:00:00Z'),
 ('class:season','class:work_component','2026-10-12T00:00:00Z'),
 ('class:arc','class:work_component','2026-10-12T00:00:00Z'),
 ('class:place','class:object_class','2026-10-12T00:00:00Z'),
 ('class:world','class:place','2026-10-12T00:00:00Z'),
 ('class:event','class:object_class','2026-10-12T00:00:00Z'),
 ('class:artifact','class:object_class','2026-10-12T00:00:00Z'),
 ('class:product','class:artifact','2026-10-12T00:00:00Z'),
 ('class:taxon','class:object_class','2026-10-12T00:00:00Z'),
 ('class:species','class:taxon','2026-10-12T00:00:00Z'),
 ('class:fictional_race','class:taxon','2026-10-12T00:00:00Z'),
 ('class:fictional_race','class:fictional_entity','2026-10-12T00:00:00Z'),
 ('class:concept','class:object_class','2026-10-12T00:00:00Z'),
 ('class:theme','class:concept','2026-10-12T00:00:00Z'),
 ('class:ideology','class:concept','2026-10-12T00:00:00Z'),
 ('class:trait','class:concept','2026-10-12T00:00:00Z'),
 ('class:emotion','class:concept','2026-10-12T00:00:00Z'),
 ('class:motivation','class:concept','2026-10-12T00:00:00Z'),
 ('class:state_concept','class:concept','2026-10-12T00:00:00Z'),
 ('class:role_concept','class:concept','2026-10-12T00:00:00Z'),
 ('class:artifact_type_concept','class:concept','2026-10-12T00:00:00Z'),
 ('class:capability','class:object_class','2026-10-12T00:00:00Z'),
 ('class:ability','class:capability','2026-10-12T00:00:00Z'),
 ('class:skill','class:capability','2026-10-12T00:00:00Z'),
 ('class:process','class:object_class','2026-10-12T00:00:00Z'),
 ('class:action','class:process','2026-10-12T00:00:00Z'),
 ('class:activity','class:process','2026-10-12T00:00:00Z'),
 ('class:temporal_entity','class:object_class','2026-10-12T00:00:00Z'),
 ('class:period','class:temporal_entity','2026-10-12T00:00:00Z'),
 ('class:era','class:period','2026-10-12T00:00:00Z'),
 ('class:timeline','class:temporal_entity','2026-10-12T00:00:00Z'),
 ('class:continuity','class:temporal_entity','2026-10-12T00:00:00Z'),
 ('class:system','class:object_class','2026-10-12T00:00:00Z'),
 ('class:software','class:system','2026-10-12T00:00:00Z'),
 ('class:service','class:system','2026-10-12T00:00:00Z'),
 ('class:rule_system','class:system','2026-10-12T00:00:00Z'),
 ('class:material','class:object_class','2026-10-12T00:00:00Z'),
 ('class:substance','class:material','2026-10-12T00:00:00Z'),
 ('class:phenomenon','class:object_class','2026-10-12T00:00:00Z'),
 ('class:natural_phenomenon','class:phenomenon','2026-10-12T00:00:00Z'),
 ('class:social_phenomenon','class:phenomenon','2026-10-12T00:00:00Z'),
 ('class:symbolic_system','class:object_class','2026-10-12T00:00:00Z'),
 ('class:language','class:symbolic_system','2026-10-12T00:00:00Z'),
 ('class:writing_system','class:symbolic_system','2026-10-12T00:00:00Z');

-- Registry / version integrity guards that remain valid before E-04 lifecycle details.
CREATE TRIGGER object_versions_owner_immutable
BEFORE UPDATE OF object_id ON object_versions
WHEN NEW.object_id <> OLD.object_id
BEGIN
 SELECT RAISE(ABORT,'version owner is immutable');
END;

CREATE TRIGGER object_classes_assignment_policy_update
BEFORE UPDATE OF assignment_policy ON object_classes
WHEN NEW.assignment_policy <> OLD.assignment_policy
BEGIN
 SELECT CASE WHEN NEW.assignment_policy <> 'primary_eligible' AND EXISTS (
   SELECT 1 FROM objects WHERE primary_class_id=OLD.id
 ) THEN RAISE(ABORT,'class is assigned as primary') END;
 SELECT CASE WHEN NEW.assignment_policy='structural' AND EXISTS (
   SELECT 1 FROM object_additional_classes WHERE class_id=OLD.id
 ) THEN RAISE(ABORT,'class is assigned as additional') END;
END;

CREATE TRIGGER object_classes_archive_in_use
BEFORE UPDATE OF status ON object_classes
WHEN NEW.status='archived' AND OLD.status <> 'archived'
BEGIN
 SELECT CASE WHEN EXISTS (
   SELECT 1 FROM objects WHERE primary_class_id=OLD.id
 ) OR EXISTS (
   SELECT 1 FROM object_additional_classes WHERE class_id=OLD.id
 ) THEN RAISE(ABORT,'cannot archive class while assigned') END;
END;

CREATE TRIGGER object_relations_validate_insert
BEFORE INSERT ON object_relations
BEGIN
 SELECT CASE WHEN NOT EXISTS (
   SELECT 1 FROM relation_types WHERE id=NEW.relation_type_id AND status='active'
 ) THEN RAISE(ABORT,'relation type must be active') END;
 SELECT CASE WHEN NOT EXISTS (
   SELECT 1 FROM object_versions v
   WHERE v.id=NEW.version_id
     AND v.object_id IN (NEW.subject_object_id,NEW.object_object_id)
 ) THEN RAISE(ABORT,'relation version owner must participate') END;
END;

CREATE TRIGGER object_relations_validate_update
BEFORE UPDATE OF version_id,subject_object_id,relation_type_id,object_object_id ON object_relations
BEGIN
 SELECT CASE WHEN NOT EXISTS (
   SELECT 1 FROM relation_types WHERE id=NEW.relation_type_id AND status='active'
 ) THEN RAISE(ABORT,'relation type must be active') END;
 SELECT CASE WHEN NOT EXISTS (
   SELECT 1 FROM object_versions v
   WHERE v.id=NEW.version_id
     AND v.object_id IN (NEW.subject_object_id,NEW.object_object_id)
 ) THEN RAISE(ABORT,'relation version owner must participate') END;
END;
