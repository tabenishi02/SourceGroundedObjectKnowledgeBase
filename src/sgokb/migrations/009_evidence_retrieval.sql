-- Phase F / F-03: canonical Evidence lexical retrieval index.
-- The index is derived from evidence_records and can be rebuilt from canonical Evidence.

CREATE VIRTUAL TABLE evidence_retrieval_fts USING fts5(
 content,
 content='evidence_records',
 content_rowid='rowid',
 tokenize='trigram'
);

INSERT INTO evidence_retrieval_fts(rowid,content)
SELECT rowid,content FROM evidence_records;

CREATE TRIGGER evidence_retrieval_fts_insert
AFTER INSERT ON evidence_records
BEGIN
 INSERT INTO evidence_retrieval_fts(rowid,content) VALUES(new.rowid,new.content);
END;

CREATE TRIGGER evidence_retrieval_fts_delete
AFTER DELETE ON evidence_records
BEGIN
 INSERT INTO evidence_retrieval_fts(evidence_retrieval_fts,rowid,content)
 VALUES('delete',old.rowid,old.content);
END;

CREATE TRIGGER evidence_retrieval_fts_update
AFTER UPDATE OF content ON evidence_records
BEGIN
 INSERT INTO evidence_retrieval_fts(evidence_retrieval_fts,rowid,content)
 VALUES('delete',old.rowid,old.content);
 INSERT INTO evidence_retrieval_fts(rowid,content) VALUES(new.rowid,new.content);
END;
