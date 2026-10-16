-- Phase M / M-01: explicit Registry proposal human-review/apply state.
-- Object Result proposal payload remains immutable in object_version_result_metadata.
-- This table records only the operator decision and explicit apply audit.

CREATE TABLE registry_proposal_reviews (
 proposal_ref TEXT PRIMARY KEY,
 version_id TEXT NOT NULL REFERENCES object_versions(id),
 local_key TEXT NOT NULL,
 proposal_kind TEXT NOT NULL CHECK(proposal_kind IN (
   'object_name','object_alias','primary_class','additional_class',
   'new_class','new_facet','new_attribute','new_relation_type'
 )),
 payload_json TEXT NOT NULL CHECK(json_valid(payload_json)),
 proposal_hash TEXT NOT NULL,
 decision TEXT NOT NULL CHECK(decision IN ('accepted','rejected')),
 review_note TEXT NOT NULL DEFAULT '',
 decided_at TEXT NOT NULL,
 applied_at TEXT,
 applied_result_json TEXT CHECK(applied_result_json IS NULL OR json_valid(applied_result_json)),
 UNIQUE(version_id,local_key),
 CHECK((applied_at IS NULL AND applied_result_json IS NULL)
    OR (applied_at IS NOT NULL AND applied_result_json IS NOT NULL AND decision='accepted'))
);

CREATE INDEX registry_proposal_reviews_version
 ON registry_proposal_reviews(version_id,decision,decided_at);
