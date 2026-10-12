-- Phase E / E-02: semantic facets, statements, typed attributes, temporal scopes,
-- and rebuildable search-representation metadata.

CREATE TABLE facet_definitions (
 id TEXT PRIMARY KEY,
 key TEXT NOT NULL UNIQUE,
 name TEXT NOT NULL,
 description TEXT NOT NULL DEFAULT '',
 is_common INTEGER NOT NULL DEFAULT 0 CHECK(is_common IN (0,1)),
 status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active','archived')),
 created_at TEXT NOT NULL,
 updated_at TEXT NOT NULL
);

CREATE TABLE class_facet_profiles (
 class_id TEXT NOT NULL REFERENCES object_classes(id),
 facet_id TEXT NOT NULL REFERENCES facet_definitions(id),
 position INTEGER NOT NULL DEFAULT 0 CHECK(position >= 0),
 inherit_to_descendants INTEGER NOT NULL DEFAULT 1 CHECK(inherit_to_descendants IN (0,1)),
 created_at TEXT NOT NULL,
 PRIMARY KEY(class_id,facet_id)
);

CREATE TABLE object_version_facets (
 version_id TEXT NOT NULL REFERENCES object_versions(id),
 facet_id TEXT NOT NULL REFERENCES facet_definitions(id),
 status TEXT NOT NULL CHECK(status IN ('content','insufficient_evidence','not_applicable','not_analyzed')),
 created_at TEXT NOT NULL,
 PRIMARY KEY(version_id,facet_id)
);

CREATE TABLE temporal_scopes (
 id TEXT PRIMARY KEY,
 version_id TEXT NOT NULL REFERENCES object_versions(id),
 as_of TEXT,
 valid_from TEXT,
 valid_to TEXT,
 context_object_id TEXT REFERENCES objects(id),
 label TEXT,
 created_at TEXT NOT NULL,
 UNIQUE(id,version_id),
 CHECK(as_of IS NOT NULL OR valid_from IS NOT NULL OR valid_to IS NOT NULL
       OR context_object_id IS NOT NULL OR label IS NOT NULL)
);

CREATE TABLE knowledge_statements (
 id TEXT PRIMARY KEY,
 version_id TEXT NOT NULL REFERENCES object_versions(id),
 facet_id TEXT REFERENCES facet_definitions(id),
 local_key TEXT NOT NULL,
 text TEXT NOT NULL CHECK(length(trim(text)) > 0),
 derivation_kind TEXT NOT NULL CHECK(derivation_kind IN ('direct_statement','synthesis','interpretation','reported_view')),
 language TEXT,
 temporal_scope_id TEXT,
 created_at TEXT NOT NULL,
 UNIQUE(version_id,local_key),
 UNIQUE(id,version_id),
 FOREIGN KEY(version_id,facet_id) REFERENCES object_version_facets(version_id,facet_id),
 FOREIGN KEY(temporal_scope_id,version_id) REFERENCES temporal_scopes(id,version_id)
);

CREATE TABLE attribute_definitions (
 id TEXT PRIMARY KEY,
 key TEXT NOT NULL UNIQUE,
 name TEXT NOT NULL,
 description TEXT NOT NULL DEFAULT '',
 value_type TEXT NOT NULL CHECK(value_type IN ('text','integer','real','boolean','date','datetime','identifier','enum','json')),
 status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active','archived')),
 created_at TEXT NOT NULL,
 updated_at TEXT NOT NULL
);

CREATE TABLE object_version_attributes (
 id TEXT PRIMARY KEY,
 version_id TEXT NOT NULL REFERENCES object_versions(id),
 attribute_id TEXT NOT NULL REFERENCES attribute_definitions(id),
 ordinal INTEGER NOT NULL DEFAULT 0 CHECK(ordinal >= 0),
 status TEXT NOT NULL DEFAULT 'known' CHECK(status IN ('known','insufficient_evidence','not_applicable','not_analyzed')),
 value_text TEXT,
 value_integer INTEGER,
 value_real REAL,
 value_boolean INTEGER CHECK(value_boolean IN (0,1)),
 value_json TEXT CHECK(value_json IS NULL OR json_valid(value_json)),
 language TEXT,
 temporal_scope_id TEXT,
 created_at TEXT NOT NULL,
 UNIQUE(version_id,attribute_id,ordinal),
 UNIQUE(id,version_id),
 FOREIGN KEY(temporal_scope_id,version_id) REFERENCES temporal_scopes(id,version_id)
);

CREATE TABLE relation_temporal_scopes (
 relation_id TEXT PRIMARY KEY REFERENCES object_relations(id),
 temporal_scope_id TEXT NOT NULL REFERENCES temporal_scopes(id),
 created_at TEXT NOT NULL
);

CREATE TABLE search_representations (
 id TEXT PRIMARY KEY,
 kind TEXT NOT NULL CHECK(kind IN ('object','facet','statement')),
 builder_key TEXT NOT NULL,
 builder_version TEXT NOT NULL,
 content TEXT NOT NULL,
 content_hash TEXT NOT NULL,
 created_at TEXT NOT NULL,
 UNIQUE(kind,builder_key,builder_version,content_hash)
);

CREATE TABLE search_representation_memberships (
 id TEXT PRIMARY KEY,
 version_id TEXT NOT NULL REFERENCES object_versions(id),
 representation_id TEXT NOT NULL REFERENCES search_representations(id),
 target_kind TEXT NOT NULL CHECK(target_kind IN ('object','facet','statement')),
 target_ref TEXT NOT NULL,
 created_at TEXT NOT NULL,
 UNIQUE(version_id,representation_id,target_kind,target_ref)
);

CREATE INDEX facet_profiles_facet ON class_facet_profiles(facet_id,class_id);
CREATE INDEX version_facets_facet ON object_version_facets(facet_id,version_id);
CREATE INDEX statements_version_facet ON knowledge_statements(version_id,facet_id);
CREATE INDEX statements_temporal ON knowledge_statements(temporal_scope_id);
CREATE INDEX attributes_version_key ON object_version_attributes(version_id,attribute_id);
CREATE INDEX attributes_temporal ON object_version_attributes(temporal_scope_id);
CREATE INDEX temporal_scopes_version ON temporal_scopes(version_id);
CREATE INDEX search_representation_hash ON search_representations(content_hash);
CREATE INDEX search_membership_target ON search_representation_memberships(target_kind,target_ref,version_id);
CREATE INDEX search_membership_version ON search_representation_memberships(version_id,representation_id);

CREATE TRIGGER knowledge_statements_facet_content_insert
BEFORE INSERT ON knowledge_statements
WHEN NEW.facet_id IS NOT NULL
BEGIN
 SELECT CASE WHEN NOT EXISTS (
   SELECT 1 FROM object_version_facets
   WHERE version_id=NEW.version_id AND facet_id=NEW.facet_id AND status='content'
 ) THEN RAISE(ABORT,'facet statement requires content facet') END;
END;

CREATE TRIGGER knowledge_statements_facet_content_update
BEFORE UPDATE OF version_id,facet_id ON knowledge_statements
WHEN NEW.facet_id IS NOT NULL
BEGIN
 SELECT CASE WHEN NOT EXISTS (
   SELECT 1 FROM object_version_facets
   WHERE version_id=NEW.version_id AND facet_id=NEW.facet_id AND status='content'
 ) THEN RAISE(ABORT,'facet statement requires content facet') END;
END;

CREATE TRIGGER object_version_facets_noncontent_guard
BEFORE UPDATE OF status ON object_version_facets
WHEN NEW.status <> 'content'
BEGIN
 SELECT CASE WHEN EXISTS (
   SELECT 1 FROM knowledge_statements
   WHERE version_id=OLD.version_id AND facet_id=OLD.facet_id
 ) THEN RAISE(ABORT,'facet with statements must remain content') END;
END;

CREATE TRIGGER object_version_attributes_validate_insert
BEFORE INSERT ON object_version_attributes
BEGIN
 SELECT CASE WHEN NOT EXISTS (
   SELECT 1 FROM attribute_definitions
   WHERE id=NEW.attribute_id AND status='active'
 ) THEN RAISE(ABORT,'attribute definition must be active') END;
 SELECT CASE WHEN NEW.status <> 'known' AND (
   NEW.value_text IS NOT NULL OR NEW.value_integer IS NOT NULL OR NEW.value_real IS NOT NULL
   OR NEW.value_boolean IS NOT NULL OR NEW.value_json IS NOT NULL
 ) THEN RAISE(ABORT,'non-known attribute cannot carry value') END;
 SELECT CASE WHEN NEW.status='known' AND NOT EXISTS (
   SELECT 1 FROM attribute_definitions a WHERE a.id=NEW.attribute_id AND (
     (a.value_type IN ('text','date','datetime','identifier','enum') AND NEW.value_text IS NOT NULL
      AND NEW.value_integer IS NULL AND NEW.value_real IS NULL AND NEW.value_boolean IS NULL AND NEW.value_json IS NULL)
     OR (a.value_type='integer' AND NEW.value_text IS NULL AND NEW.value_integer IS NOT NULL
      AND NEW.value_real IS NULL AND NEW.value_boolean IS NULL AND NEW.value_json IS NULL)
     OR (a.value_type='real' AND NEW.value_text IS NULL AND NEW.value_integer IS NULL
      AND NEW.value_real IS NOT NULL AND NEW.value_boolean IS NULL AND NEW.value_json IS NULL)
     OR (a.value_type='boolean' AND NEW.value_text IS NULL AND NEW.value_integer IS NULL
      AND NEW.value_real IS NULL AND NEW.value_boolean IS NOT NULL AND NEW.value_json IS NULL)
     OR (a.value_type='json' AND NEW.value_text IS NULL AND NEW.value_integer IS NULL
      AND NEW.value_real IS NULL AND NEW.value_boolean IS NULL AND NEW.value_json IS NOT NULL)
   )
 ) THEN RAISE(ABORT,'attribute value does not match declared type') END;
END;

CREATE TRIGGER object_version_attributes_validate_update
BEFORE UPDATE OF attribute_id,status,value_text,value_integer,value_real,value_boolean,value_json
ON object_version_attributes
BEGIN
 SELECT CASE WHEN NOT EXISTS (
   SELECT 1 FROM attribute_definitions
   WHERE id=NEW.attribute_id AND status='active'
 ) THEN RAISE(ABORT,'attribute definition must be active') END;
 SELECT CASE WHEN NEW.status <> 'known' AND (
   NEW.value_text IS NOT NULL OR NEW.value_integer IS NOT NULL OR NEW.value_real IS NOT NULL
   OR NEW.value_boolean IS NOT NULL OR NEW.value_json IS NOT NULL
 ) THEN RAISE(ABORT,'non-known attribute cannot carry value') END;
 SELECT CASE WHEN NEW.status='known' AND NOT EXISTS (
   SELECT 1 FROM attribute_definitions a WHERE a.id=NEW.attribute_id AND (
     (a.value_type IN ('text','date','datetime','identifier','enum') AND NEW.value_text IS NOT NULL
      AND NEW.value_integer IS NULL AND NEW.value_real IS NULL AND NEW.value_boolean IS NULL AND NEW.value_json IS NULL)
     OR (a.value_type='integer' AND NEW.value_text IS NULL AND NEW.value_integer IS NOT NULL
      AND NEW.value_real IS NULL AND NEW.value_boolean IS NULL AND NEW.value_json IS NULL)
     OR (a.value_type='real' AND NEW.value_text IS NULL AND NEW.value_integer IS NULL
      AND NEW.value_real IS NOT NULL AND NEW.value_boolean IS NULL AND NEW.value_json IS NULL)
     OR (a.value_type='boolean' AND NEW.value_text IS NULL AND NEW.value_integer IS NULL
      AND NEW.value_real IS NULL AND NEW.value_boolean IS NOT NULL AND NEW.value_json IS NULL)
     OR (a.value_type='json' AND NEW.value_text IS NULL AND NEW.value_integer IS NULL
      AND NEW.value_real IS NULL AND NEW.value_boolean IS NULL AND NEW.value_json IS NOT NULL)
   )
 ) THEN RAISE(ABORT,'attribute value does not match declared type') END;
END;

CREATE TRIGGER relation_temporal_scopes_validate_insert
BEFORE INSERT ON relation_temporal_scopes
BEGIN
 SELECT CASE WHEN NOT EXISTS (
   SELECT 1 FROM object_relations r
   JOIN temporal_scopes t ON t.id=NEW.temporal_scope_id
   WHERE r.id=NEW.relation_id AND r.version_id=t.version_id
 ) THEN RAISE(ABORT,'relation temporal scope must belong to relation version') END;
END;

CREATE TRIGGER relation_temporal_scopes_validate_update
BEFORE UPDATE OF relation_id,temporal_scope_id ON relation_temporal_scopes
BEGIN
 SELECT CASE WHEN NOT EXISTS (
   SELECT 1 FROM object_relations r
   JOIN temporal_scopes t ON t.id=NEW.temporal_scope_id
   WHERE r.id=NEW.relation_id AND r.version_id=t.version_id
 ) THEN RAISE(ABORT,'relation temporal scope must belong to relation version') END;
END;

CREATE TRIGGER search_memberships_validate_insert
BEFORE INSERT ON search_representation_memberships
BEGIN
 SELECT CASE WHEN NOT EXISTS (
   SELECT 1 FROM search_representations
   WHERE id=NEW.representation_id AND kind=NEW.target_kind
 ) THEN RAISE(ABORT,'representation kind must match target kind') END;
 SELECT CASE WHEN NEW.target_kind='object' AND NOT EXISTS (
   SELECT 1 FROM object_versions WHERE id=NEW.version_id AND object_id=NEW.target_ref
 ) THEN RAISE(ABORT,'object representation target must own version') END;
 SELECT CASE WHEN NEW.target_kind='facet' AND NOT EXISTS (
   SELECT 1 FROM object_version_facets
   WHERE version_id=NEW.version_id AND facet_id=NEW.target_ref
 ) THEN RAISE(ABORT,'facet representation target must belong to version') END;
 SELECT CASE WHEN NEW.target_kind='statement' AND NOT EXISTS (
   SELECT 1 FROM knowledge_statements
   WHERE version_id=NEW.version_id AND id=NEW.target_ref
 ) THEN RAISE(ABORT,'statement representation target must belong to version') END;
END;

CREATE TRIGGER search_memberships_validate_update
BEFORE UPDATE OF version_id,representation_id,target_kind,target_ref
ON search_representation_memberships
BEGIN
 SELECT CASE WHEN NOT EXISTS (
   SELECT 1 FROM search_representations
   WHERE id=NEW.representation_id AND kind=NEW.target_kind
 ) THEN RAISE(ABORT,'representation kind must match target kind') END;
 SELECT CASE WHEN NEW.target_kind='object' AND NOT EXISTS (
   SELECT 1 FROM object_versions WHERE id=NEW.version_id AND object_id=NEW.target_ref
 ) THEN RAISE(ABORT,'object representation target must own version') END;
 SELECT CASE WHEN NEW.target_kind='facet' AND NOT EXISTS (
   SELECT 1 FROM object_version_facets
   WHERE version_id=NEW.version_id AND facet_id=NEW.target_ref
 ) THEN RAISE(ABORT,'facet representation target must belong to version') END;
 SELECT CASE WHEN NEW.target_kind='statement' AND NOT EXISTS (
   SELECT 1 FROM knowledge_statements
   WHERE version_id=NEW.version_id AND id=NEW.target_ref
 ) THEN RAISE(ABORT,'statement representation target must belong to version') END;
END;

-- Initial Facet Registry. `overall` is common; specialized profiles are seeded
-- only for Character / Work / Concept and inherited by their subclasses.
INSERT INTO facet_definitions(id,key,name,description,is_common,status,created_at,updated_at) VALUES
 ('facet:overall','overall','Overall','General semantic knowledge not limited to a specialized facet',1,'active','2026-10-12T00:00:00Z','2026-10-12T00:00:00Z'),
 ('facet:personality','personality','Personality','Personality and characteristic behavioral disposition',0,'active','2026-10-12T00:00:00Z','2026-10-12T00:00:00Z'),
 ('facet:values','values','Values','Values, priorities, and principles',0,'active','2026-10-12T00:00:00Z','2026-10-12T00:00:00Z'),
 ('facet:motivation','motivation','Motivation','Motives and driving reasons',0,'active','2026-10-12T00:00:00Z','2026-10-12T00:00:00Z'),
 ('facet:behavior','behavior','Behavior','Observed or described behavior patterns',0,'active','2026-10-12T00:00:00Z','2026-10-12T00:00:00Z'),
 ('facet:relationships','relationships','Relationships','Relationship-oriented semantic knowledge',0,'active','2026-10-12T00:00:00Z','2026-10-12T00:00:00Z'),
 ('facet:role','role','Role','Narrative, social, or functional role',0,'active','2026-10-12T00:00:00Z','2026-10-12T00:00:00Z'),
 ('facet:themes','themes','Themes','Themes and motifs',0,'active','2026-10-12T00:00:00Z','2026-10-12T00:00:00Z'),
 ('facet:abilities','abilities','Abilities','Abilities, skills, and capability-related knowledge',0,'active','2026-10-12T00:00:00Z','2026-10-12T00:00:00Z'),
 ('facet:worldview','worldview','Worldview','Worldview and value framework represented by a work',0,'active','2026-10-12T00:00:00Z','2026-10-12T00:00:00Z'),
 ('facet:narrative','narrative','Narrative','Narrative structure and development',0,'active','2026-10-12T00:00:00Z','2026-10-12T00:00:00Z'),
 ('facet:tone','tone','Tone','Tone, mood, and presentation character',0,'active','2026-10-12T00:00:00Z','2026-10-12T00:00:00Z'),
 ('facet:characters','characters','Characters','Character ensemble and characterization within a work',0,'active','2026-10-12T00:00:00Z','2026-10-12T00:00:00Z'),
 ('facet:definition','definition','Definition','Definition and conceptual boundary',0,'active','2026-10-12T00:00:00Z','2026-10-12T00:00:00Z'),
 ('facet:properties','properties','Properties','Properties and characteristics of a concept',0,'active','2026-10-12T00:00:00Z','2026-10-12T00:00:00Z'),
 ('facet:implications','implications','Implications','Consequences and implications',0,'active','2026-10-12T00:00:00Z','2026-10-12T00:00:00Z'),
 ('facet:related_concepts','related_concepts','Related Concepts','Connections to related concepts',0,'active','2026-10-12T00:00:00Z','2026-10-12T00:00:00Z'),
 ('facet:examples','examples','Examples','Representative examples and applications',0,'active','2026-10-12T00:00:00Z','2026-10-12T00:00:00Z');

INSERT INTO class_facet_profiles(class_id,facet_id,position,inherit_to_descendants,created_at) VALUES
 ('class:character','facet:personality',10,1,'2026-10-12T00:00:00Z'),
 ('class:character','facet:values',20,1,'2026-10-12T00:00:00Z'),
 ('class:character','facet:motivation',30,1,'2026-10-12T00:00:00Z'),
 ('class:character','facet:behavior',40,1,'2026-10-12T00:00:00Z'),
 ('class:character','facet:relationships',50,1,'2026-10-12T00:00:00Z'),
 ('class:character','facet:role',60,1,'2026-10-12T00:00:00Z'),
 ('class:character','facet:themes',70,1,'2026-10-12T00:00:00Z'),
 ('class:character','facet:abilities',80,1,'2026-10-12T00:00:00Z'),
 ('class:work','facet:themes',10,1,'2026-10-12T00:00:00Z'),
 ('class:work','facet:worldview',20,1,'2026-10-12T00:00:00Z'),
 ('class:work','facet:narrative',30,1,'2026-10-12T00:00:00Z'),
 ('class:work','facet:tone',40,1,'2026-10-12T00:00:00Z'),
 ('class:work','facet:characters',50,1,'2026-10-12T00:00:00Z'),
 ('class:work','facet:relationships',60,1,'2026-10-12T00:00:00Z'),
 ('class:concept','facet:definition',10,1,'2026-10-12T00:00:00Z'),
 ('class:concept','facet:properties',20,1,'2026-10-12T00:00:00Z'),
 ('class:concept','facet:implications',30,1,'2026-10-12T00:00:00Z'),
 ('class:concept','facet:related_concepts',40,1,'2026-10-12T00:00:00Z'),
 ('class:concept','facet:examples',50,1,'2026-10-12T00:00:00Z');

CREATE TRIGGER object_version_facets_validate_insert
BEFORE INSERT ON object_version_facets
BEGIN
 SELECT CASE WHEN NOT EXISTS (
   SELECT 1 FROM facet_definitions WHERE id=NEW.facet_id AND status='active'
 ) THEN RAISE(ABORT,'facet definition must be active') END;
END;

CREATE TRIGGER object_version_facets_validate_update
BEFORE UPDATE OF facet_id ON object_version_facets
BEGIN
 SELECT CASE WHEN NOT EXISTS (
   SELECT 1 FROM facet_definitions WHERE id=NEW.facet_id AND status='active'
 ) THEN RAISE(ABORT,'facet definition must be active') END;
END;
