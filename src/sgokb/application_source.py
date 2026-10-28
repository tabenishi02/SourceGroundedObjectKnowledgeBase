"""Transport-neutral Source operator application used by CLI and GUI."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

from .application import Application


@dataclass(frozen=True, slots=True)
class SourceBatchResult:
    items: tuple[object, ...]
    partial: bool


class SourceOperatorApplication:
    def __init__(self, repository, *, embedder=None) -> None:
        self.repository = repository
        self._application = Application(repository, embedder=embedder)

    def status(self):
        return self.repository.source_store.status()

    def snapshots(self) -> list[dict]:
        store = self.repository.source_store
        result = []
        for snapshot in store.snapshots():
            effective = store.effective_snapshot(snapshot.source_id)
            effective_run = store.effective_run(snapshot.snapshot_id)
            run_rows = self.repository.db.execute(
                """SELECT * FROM normalization_runs
                   WHERE snapshot_id=? ORDER BY created_at,id""",
                (snapshot.snapshot_id,),
            ).fetchall()
            runs = []
            for row in run_rows:
                item = dict(row)
                item["effective"] = bool(effective_run and effective_run["id"] == item["id"])
                runs.append(item)
            raw_artifacts = []
            for row in store.raw_artifacts(snapshot.snapshot_id):
                item = dict(row)
                item["byte_count"] = item.pop("bytes")
                raw_artifacts.append(item)
            source = store.source_by_id(snapshot.source_id)
            result.append(
                {
                    "id": snapshot.snapshot_id,
                    "source_id": snapshot.source_id,
                    "source_label": source.label,
                    "title": snapshot.title,
                    "captured_at": snapshot.captured_at,
                    "completeness": snapshot.completeness.value,
                    "effective": bool(
                        effective and effective.snapshot_id == snapshot.snapshot_id
                    ),
                    "effective_run_id": effective_run["id"] if effective_run else None,
                    "locators": [asdict(item) for item in store.locators(snapshot.source_id)],
                    "metadata": store.snapshot_metadata(snapshot.snapshot_id),
                    "raw_artifacts": raw_artifacts,
                    "normalization_runs": runs,
                }
            )
        return result

    def select_snapshot(self, source_id: str, snapshot_id: str, reason: str) -> dict:
        store = self.repository.source_store
        selection_id = store.select_effective_snapshot(source_id, snapshot_id, reason=reason)
        effective = store.effective_snapshot(source_id)
        return {
            "selection_id": selection_id,
            "source_id": source_id,
            "snapshot_id": snapshot_id,
            "effective": bool(effective and effective.snapshot_id == snapshot_id),
        }

    def select_run(self, snapshot_id: str, run_id: str, reason: str) -> dict:
        store = self.repository.source_store
        snapshot = store.snapshot_by_id(snapshot_id)
        selection_id = store.select_effective_run(snapshot_id, run_id, reason=reason)
        effective = store.effective_run(snapshot_id)
        return {
            "selection_id": selection_id,
            "source_id": snapshot.source_id,
            "snapshot_id": snapshot_id,
            "run_id": run_id,
            "effective": bool(effective and effective["id"] == run_id),
        }

    def import_path(self, path: str | Path) -> SourceBatchResult:
        source = Path(path)
        targets = [source] if source.is_file() else sorted(source.rglob("*.webcapture.zip"))
        if not targets:
            raise ValueError("No input bundles or snapshots found")
        items: list[object] = []
        failed = False
        for target in targets:
            try:
                items.append(self._application.import_source_path(target))
            except Exception as exc:
                failed = True
                items.append(
                    {"input": str(target), "error": type(exc).__name__, "reason": str(exc)}
                )
        return SourceBatchResult(tuple(items), failed)

    def process(
        self,
        snapshot_id: str | None = None,
        *,
        size: int = 1000,
        overlap: int = 100,
        include_auxiliary: bool = False,
    ) -> SourceBatchResult:
        targets = (
            [snapshot_id]
            if snapshot_id
            else [item.snapshot_id for item in self.repository.source_store.snapshots()]
        )
        if not targets:
            raise ValueError("No input bundles or snapshots found")
        items: list[object] = []
        failed = False
        for target in targets:
            try:
                items.append(
                    self._application.process_source_snapshot(
                        target, size, overlap, include_auxiliary
                    )
                )
            except Exception as exc:
                failed = True
                items.append(
                    {"input": str(target), "error": type(exc).__name__, "reason": str(exc)}
                )
        return SourceBatchResult(tuple(items), failed)
