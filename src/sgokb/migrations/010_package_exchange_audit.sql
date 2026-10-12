-- Phase G / G-04: immutable Package staging/export audit metadata.

CREATE TABLE package_exchange_records (
    package_id TEXT PRIMARY KEY,
    schema_version TEXT NOT NULL,
    manifest_sha256 TEXT NOT NULL,
    object_id TEXT NOT NULL,
    base_version_id TEXT,
    package_created_at TEXT NOT NULL,
    extracted_at TEXT NOT NULL,
    included_evidence_ids_json TEXT NOT NULL,
    staged_path TEXT NOT NULL,
    preflight_disposition TEXT NOT NULL
        CHECK(preflight_disposition IN ('allow','review_required','blocked')),
    preflight_json TEXT NOT NULL,
    staged_at TEXT NOT NULL
);

CREATE TABLE package_export_events (
    id TEXT PRIMARY KEY,
    package_id TEXT NOT NULL REFERENCES package_exchange_records(package_id),
    destination_root TEXT NOT NULL,
    exported_path TEXT NOT NULL,
    manifest_sha256 TEXT NOT NULL,
    acknowledged_review INTEGER NOT NULL CHECK(acknowledged_review IN (0,1)),
    already_present INTEGER NOT NULL CHECK(already_present IN (0,1)),
    exported_at TEXT NOT NULL
);

CREATE INDEX package_exchange_object
    ON package_exchange_records(object_id, staged_at);
CREATE INDEX package_export_events_package
    ON package_export_events(package_id, exported_at);
