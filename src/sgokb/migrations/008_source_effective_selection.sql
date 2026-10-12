-- Phase F / F-01: explicit effective Snapshot / Normalization Run selection.
-- Selection is append-only so changing the effective generation never destroys history.

CREATE TABLE source_selection_events (
 id TEXT PRIMARY KEY,
 source_id TEXT NOT NULL REFERENCES source_records(id),
 selection_kind TEXT NOT NULL CHECK(selection_kind IN ('snapshot','run')),
 snapshot_id TEXT NOT NULL REFERENCES source_snapshots(id),
 run_id TEXT REFERENCES normalization_runs(id),
 origin_kind TEXT NOT NULL CHECK(origin_kind IN ('automatic_initial','manual','migration','system')),
 reason TEXT NOT NULL CHECK(length(trim(reason)) > 0),
 created_at TEXT NOT NULL,
 CHECK(
   (selection_kind='snapshot' AND run_id IS NULL) OR
   (selection_kind='run' AND run_id IS NOT NULL)
 )
);
CREATE INDEX source_selection_events_source
 ON source_selection_events(source_id,selection_kind,created_at);
CREATE INDEX source_selection_events_snapshot
 ON source_selection_events(snapshot_id,selection_kind,created_at);
CREATE INDEX source_selection_events_run
 ON source_selection_events(run_id) WHERE run_id IS NOT NULL;

CREATE TRIGGER source_selection_events_validate_insert
BEFORE INSERT ON source_selection_events
BEGIN
 SELECT CASE WHEN NOT EXISTS (
   SELECT 1 FROM source_snapshots
   WHERE id=NEW.snapshot_id AND source_id=NEW.source_id
 ) THEN RAISE(ABORT,'selection snapshot must belong to source') END;
 SELECT CASE WHEN NEW.selection_kind='run' AND NOT EXISTS (
   SELECT 1 FROM normalization_runs
   WHERE id=NEW.run_id AND snapshot_id=NEW.snapshot_id
 ) THEN RAISE(ABORT,'selection run must belong to snapshot') END;
END;

CREATE TRIGGER source_selection_events_immutable
BEFORE UPDATE ON source_selection_events
BEGIN SELECT RAISE(ABORT,'source selection event is immutable'); END;
