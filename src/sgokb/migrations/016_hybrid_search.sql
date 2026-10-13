-- Phase I / I-04: rebuildable lexical index over derived Search Representations.
-- Evidence remains a logically separate search family; Object Search joins only Knowledge memberships.

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
