-- Phase H / H-01: deterministic Result validation report persistence.

ALTER TABLE package_result_receipts
 ADD COLUMN validation_started_at TEXT;
ALTER TABLE package_result_receipts
 ADD COLUMN validation_completed_at TEXT;
ALTER TABLE package_result_receipts
 ADD COLUMN validation_findings_json TEXT NOT NULL DEFAULT '[]'
 CHECK(json_valid(validation_findings_json));
