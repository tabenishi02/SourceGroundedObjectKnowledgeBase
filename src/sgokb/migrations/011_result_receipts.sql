-- Phase G / G-05: immutable Result receipt and validation-trigger metadata.

CREATE TABLE package_result_receipts (
    id TEXT PRIMARY KEY,
    package_id TEXT NOT NULL REFERENCES package_exchange_records(package_id),
    result_sha256 TEXT NOT NULL,
    byte_count INTEGER NOT NULL CHECK(byte_count >= 0),
    storage_ref TEXT NOT NULL,
    intake_state TEXT NOT NULL
        CHECK(intake_state IN ('ready_for_validation','needs_review')),
    intake_findings_json TEXT NOT NULL,
    parsed_schema_version TEXT,
    parsed_result_status TEXT,
    parsed_target_object_id TEXT,
    parsed_binding_package_id TEXT,
    parsed_manifest_sha256 TEXT,
    parsed_base_version_id TEXT,
    validation_state TEXT NOT NULL DEFAULT 'pending'
        CHECK(validation_state IN ('pending','running','valid','invalid','error')),
    validation_requested_at TEXT NOT NULL,
    received_at TEXT NOT NULL,
    UNIQUE(package_id,result_sha256)
);

CREATE INDEX package_result_receipts_package
    ON package_result_receipts(package_id, received_at);
CREATE INDEX package_result_receipts_validation
    ON package_result_receipts(validation_state, validation_requested_at);
