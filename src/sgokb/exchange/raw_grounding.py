"""Deterministic P-RAW Evidence -> Raw provenance resolution and byte verification."""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from sgokb.ingestion import WebCaptureImporter

RESOLUTION_CONTRACT = "sgokb.evidence-to-raw/1.0"
GROUNDING_CONTRACT = "sgokb.raw-grounding/1.0"


@dataclass(frozen=True, slots=True)
class ResolvedRawArtifact:
    raw_artifact_id: str
    source_id: str
    snapshot_id: str
    artifact_kind: str
    logical_path: str | None
    media_type: str | None
    charset: str | None
    byte_size: int
    sha256: str
    storage_ref: str

    def manifest_dict(self, package_path: str) -> dict[str, Any]:
        value = asdict(self)
        value.pop("storage_ref")
        value["package_path"] = package_path
        return value


@dataclass(frozen=True, slots=True)
class EvidenceRawBinding:
    evidence_id: str
    source_id: str
    snapshot_id: str
    normalization_run_id: str
    raw_artifact_ids: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["raw_artifact_ids"] = list(self.raw_artifact_ids)
        return value


@dataclass(frozen=True, slots=True)
class RawGroundingResolution:
    artifacts: tuple[ResolvedRawArtifact, ...]
    bindings: tuple[EvidenceRawBinding, ...]

    @property
    def included_raw_artifact_ids(self) -> tuple[str, ...]:
        return tuple(item.raw_artifact_id for item in self.artifacts)


class RawArtifactByteReader:
    """Read exact canonical Raw bytes from the current storage_ref contract."""

    def __init__(self) -> None:
        self._bundle_cache: dict[str, object] = {}
        self._importer = WebCaptureImporter()

    def read(self, artifact: ResolvedRawArtifact) -> bytes:
        storage = Path(artifact.storage_ref)
        raw: bytes | None = None

        if artifact.logical_path:
            key = str(storage.resolve())
            bundle = self._bundle_cache.get(key)
            if bundle is None:
                try:
                    bundle = self._importer.read(storage)
                except Exception:
                    bundle = False
                self._bundle_cache[key] = bundle
            if bundle is not False:
                raw = bundle.artifacts.get(artifact.logical_path)

        if raw is None and storage.is_file():
            candidate = storage.read_bytes()
            if len(candidate) == artifact.byte_size and _sha256(candidate) == artifact.sha256:
                raw = candidate

        if raw is None:
            raise ValueError(
                f"Raw Artifact physical bytes cannot be resolved: {artifact.raw_artifact_id}"
            )
        if len(raw) != artifact.byte_size:
            raise ValueError(f"Raw Artifact byte-size mismatch: {artifact.raw_artifact_id}")
        if _sha256(raw) != artifact.sha256:
            raise ValueError(f"Raw Artifact SHA-256 mismatch: {artifact.raw_artifact_id}")
        return raw


class EvidenceRawResolver:
    """Resolve every Evidence through its own Normalization Run input covering set."""

    def __init__(self, repository, *, byte_reader: RawArtifactByteReader | None = None) -> None:
        self.repository = repository
        self.byte_reader = byte_reader or RawArtifactByteReader()

    def resolve(self, evidence_ids) -> RawGroundingResolution:
        store = self.repository.source_store
        ordered_evidence = tuple(dict.fromkeys(str(value) for value in evidence_ids))
        if not ordered_evidence:
            raise ValueError("Raw grounding resolution requires at least one Evidence item")

        artifacts: dict[str, ResolvedRawArtifact] = {}
        bindings: list[EvidenceRawBinding] = []
        for evidence_id in ordered_evidence:
            provenance = store.evidence_provenance(evidence_id)
            evidence = provenance.evidence
            snapshot = provenance.snapshot
            raw_rows = store.normalization_input_raw_artifacts(evidence.run_id)
            raw_ids = tuple(sorted(str(row["id"]) for row in raw_rows))
            if raw_ids != tuple(sorted(provenance.raw_artifact_ids)):
                raise ValueError(
                    f"Evidence Raw covering set differs from canonical provenance: {evidence_id}"
                )

            for row in raw_rows:
                if row["snapshot_id"] != evidence.snapshot_id:
                    raise ValueError(f"Raw Artifact Snapshot mismatch: {row['id']}")
                if snapshot.source_id != evidence.source_id:
                    raise ValueError(f"Evidence Source/Snapshot mismatch: {evidence_id}")
                resolved = ResolvedRawArtifact(
                    raw_artifact_id=str(row["id"]),
                    source_id=evidence.source_id,
                    snapshot_id=evidence.snapshot_id,
                    artifact_kind=str(row["artifact_kind"]),
                    logical_path=row["logical_path"],
                    media_type=row["media_type"],
                    charset=None,
                    byte_size=int(row["bytes"]),
                    sha256=str(row["sha256"]),
                    storage_ref=str(row["storage_ref"]),
                )
                raw = self.byte_reader.read(resolved)
                charset = _verified_charset(resolved.media_type, raw)
                resolved = ResolvedRawArtifact(
                    raw_artifact_id=resolved.raw_artifact_id,
                    source_id=resolved.source_id,
                    snapshot_id=resolved.snapshot_id,
                    artifact_kind=resolved.artifact_kind,
                    logical_path=resolved.logical_path,
                    media_type=resolved.media_type,
                    charset=charset,
                    byte_size=resolved.byte_size,
                    sha256=resolved.sha256,
                    storage_ref=resolved.storage_ref,
                )
                previous = artifacts.get(resolved.raw_artifact_id)
                if previous is not None and previous != resolved:
                    raise ValueError(
                        f"Raw Artifact identity resolved inconsistently: {resolved.raw_artifact_id}"
                    )
                artifacts[resolved.raw_artifact_id] = resolved

            bindings.append(
                EvidenceRawBinding(
                    evidence_id=evidence_id,
                    source_id=evidence.source_id,
                    snapshot_id=evidence.snapshot_id,
                    normalization_run_id=evidence.run_id,
                    raw_artifact_ids=raw_ids,
                )
            )

        return RawGroundingResolution(
            artifacts=tuple(artifacts[key] for key in sorted(artifacts)),
            bindings=tuple(bindings),
        )


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _verified_charset(media_type: str | None, raw: bytes) -> str | None:
    media = (media_type or "").lower()
    if not (media.startswith("text/") or media in {"application/json", "application/xml"}):
        return None
    try:
        raw.decode("utf-8")
    except UnicodeDecodeError:
        return None
    return "utf-8"
