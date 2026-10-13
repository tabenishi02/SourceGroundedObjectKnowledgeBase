-- Phase I / I-02: embedding-space identity and representation-vector cache.
-- Legacy prototype embedding_spaces/embeddings remain untouched for Phase L compatibility.

CREATE TABLE search_embedding_spaces (
 id TEXT PRIMARY KEY,
 provider_key TEXT NOT NULL CHECK(length(trim(provider_key)) > 0),
 provider_version TEXT NOT NULL CHECK(length(trim(provider_version)) > 0),
 model TEXT NOT NULL CHECK(length(trim(model)) > 0),
 model_revision TEXT NOT NULL CHECK(length(trim(model_revision)) > 0),
 dimension INTEGER NOT NULL CHECK(dimension > 0),
 native_dimension INTEGER NOT NULL CHECK(native_dimension >= dimension),
 preprocessing_key TEXT NOT NULL CHECK(length(trim(preprocessing_key)) > 0),
 preprocessing_version TEXT NOT NULL CHECK(length(trim(preprocessing_version)) > 0),
 query_instruction TEXT NOT NULL,
 document_instruction TEXT NOT NULL,
 normalize_embeddings INTEGER NOT NULL CHECK(normalize_embeddings IN (0,1)),
 max_sequence_length INTEGER CHECK(max_sequence_length IS NULL OR max_sequence_length > 0),
 overflow_policy TEXT NOT NULL CHECK(overflow_policy IN ('reject','truncate')),
 output_dtype TEXT NOT NULL CHECK(length(trim(output_dtype)) > 0),
 provider_configuration TEXT NOT NULL,
 configuration_hash TEXT NOT NULL UNIQUE CHECK(length(configuration_hash) = 64),
 created_at TEXT NOT NULL,
 CHECK(id = configuration_hash)
);

CREATE TABLE search_representation_embeddings (
 space_id TEXT NOT NULL REFERENCES search_embedding_spaces(id) ON DELETE CASCADE,
 representation_id TEXT NOT NULL REFERENCES search_representations(id) ON DELETE CASCADE,
 content_hash TEXT NOT NULL CHECK(length(content_hash) = 64),
 vector BLOB NOT NULL CHECK(length(vector) > 0),
 created_at TEXT NOT NULL,
 PRIMARY KEY(space_id,representation_id)
);

CREATE INDEX search_representation_embeddings_representation
 ON search_representation_embeddings(representation_id,space_id);

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
