#!/usr/bin/env python3
"""N05D-01 minimal real-Qdrant storage/payload-index diagnosis.

This tool never opens SGOKB canonical SQLite data. It creates only run-specific
Qdrant collections and removes successful collections after each probe. Failed
collections are preserved for server-side inspection.
"""

from __future__ import annotations

import argparse
import json
import math
import platform
import shutil
import subprocess
import sys
import traceback
import urllib.request
import uuid
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
DEFAULT_FIELDS = {
    "membership_id": "keyword",
    "representation_id": "keyword",
    "kind": "keyword",
    "object_id": "keyword",
    "version_id": "keyword",
    "facet_id": "keyword",
    "facet": "keyword",
    "statement_id": "keyword",
    "evidence_id": "keyword",
    "source_id": "keyword",
    "snapshot_id": "keyword",
    "primary_class": "keyword",
    "additional_classes": "keyword",
    "ancestor_classes": "keyword",
    "object_status": "keyword",
    "derivation_kind": "keyword",
    "temporal_scope_id": "keyword",
    "valid_from_ordinal": "integer",
    "valid_to_ordinal": "integer",
    "is_current": "bool",
}


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def server_root(url: str) -> dict[str, Any]:
    with urllib.request.urlopen(url.rstrip("/") + "/", timeout=10) as response:
        value = json.load(response)
    return value if isinstance(value, dict) else {"value": value}


def windows_process_for_port(port: int) -> dict[str, Any]:
    if platform.system() != "Windows":
        return {"platform": platform.system(), "available": False}
    script = f"""
$connection = Get-NetTCPConnection -State Listen -LocalPort {port} -ErrorAction SilentlyContinue |
  Select-Object -First 1
if ($null -eq $connection) {{
  @{{available=$false; reason='no_listener'}} | ConvertTo-Json -Compress
  exit 0
}}
$process = Get-CimInstance Win32_Process -Filter "ProcessId=$($connection.OwningProcess)"
@{{
  available=$true
  pid=[int]$connection.OwningProcess
  executable_path=$process.ExecutablePath
  command_line=$process.CommandLine
  name=$process.Name
}} | ConvertTo-Json -Compress
"""
    try:
        raw = subprocess.check_output(
            ["powershell", "-NoProfile", "-Command", script],
            text=True,
            encoding="utf-8",
            errors="replace",
        ).strip()
        return json.loads(raw)
    except Exception as exc:
        return {"available": False, "reason": "process_inspection_failed", "error": repr(exc)}


def path_evidence(path: Path) -> dict[str, Any]:
    value: dict[str, Any] = {
        "path": str(path),
        "absolute": str(path.resolve()),
        "exists": path.exists(),
    }
    try:
        usage = shutil.disk_usage(path if path.exists() else path.parent)
        value["disk_free_bytes"] = usage.free
        value["disk_total_bytes"] = usage.total
    except OSError as exc:
        value["disk_usage_error"] = repr(exc)
    if path.exists():
        value["is_dir"] = path.is_dir()
        try:
            probe = path / f".n05d01-write-probe-{uuid.uuid4().hex}"
            probe.write_text("probe", encoding="utf-8")
            probe.unlink()
            value["write_probe"] = "PASS"
        except OSError as exc:
            value["write_probe"] = "FAIL"
            value["write_probe_error"] = repr(exc)
    return value


def _payload(index: int) -> dict[str, Any]:
    return {
        "membership_id": f"membership-{index:04d}",
        "representation_id": f"representation-{index:04d}",
        "kind": "object",
        "object_id": f"object-{index % 4}",
        "version_id": "version-current",
        "facet_id": f"facet-{index % 3}",
        "facet": f"facet-{index % 3}",
        "statement_id": f"statement-{index:04d}",
        "evidence_id": f"evidence-{index:04d}",
        "source_id": f"source-{index % 8}",
        "snapshot_id": f"snapshot-{index % 8}",
        "primary_class": "character",
        "additional_classes": ["fictional_entity"],
        "ancestor_classes": ["entity"],
        "object_status": "active",
        "derivation_kind": "direct_statement",
        "temporal_scope_id": "current",
        "valid_from_ordinal": 1,
        "valid_to_ordinal": 999999,
        "is_current": True,
    }


def _vector(index: int, dimension: int = 8) -> list[float]:
    values = [0.0] * dimension
    values[index % dimension] = 1.0
    values[(index + 3) % dimension] = 0.25
    length = math.sqrt(sum(value * value for value in values))
    return [value / length for value in values]


def _error(exc: BaseException) -> dict[str, Any]:
    return {
        "type": type(exc).__name__,
        "message": str(exc),
        "repr": repr(exc),
        "traceback": traceback.format_exc(),
    }


def direct_probe(*, url: str, grpc_port: int, collection: str, indexed: bool, point_count: int) -> dict[str, Any]:
    from qdrant_client import QdrantClient, models

    client = QdrantClient(url=url, grpc_port=grpc_port, prefer_grpc=True, timeout=120)
    result: dict[str, Any] = {
        "kind": "direct_qdrant_client",
        "collection": collection,
        "indexed": indexed,
        "point_count": point_count,
        "status": "FAIL",
        "stages": [],
    }
    success = False
    try:
        if client.collection_exists(collection):
            raise RuntimeError(f"Diagnostic collection already exists: {collection}")
        client.create_collection(
            collection,
            vectors_config=models.VectorParams(size=8, distance=models.Distance.COSINE),
            optimizers_config=models.OptimizersConfigDiff(indexing_threshold=1000, default_segment_number=2),
        )
        result["stages"].append({"stage": "collection_create", "status": "PASS"})
        if indexed:
            schema_types = {
                "keyword": models.PayloadSchemaType.KEYWORD,
                "integer": models.PayloadSchemaType.INTEGER,
                "bool": models.PayloadSchemaType.BOOL,
            }
            for field_name, field_type in DEFAULT_FIELDS.items():
                client.create_payload_index(
                    collection,
                    field_name=field_name,
                    field_schema=schema_types[field_type],
                    wait=True,
                )
                result["stages"].append(
                    {"stage": "payload_index_create", "field": field_name, "status": "PASS"}
                )
        points = [
            models.PointStruct(id=index, vector=_vector(index), payload=_payload(index))
            for index in range(point_count)
        ]
        client.upload_points(collection, points=points, batch_size=64, parallel=1, wait=True)
        result["stages"].append({"stage": "point_upload", "status": "PASS"})
        response = client.query_points(
            collection,
            query=_vector(0),
            query_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="object_id",
                        match=models.MatchValue(value="object-0"),
                    )
                ]
            ),
            limit=5,
            with_payload=True,
            with_vectors=False,
        )
        if not response.points:
            raise RuntimeError("Diagnostic query returned no points")
        info = client.get_collection(collection)
        result.update(
            query_hit_count=len(response.points),
            collection_status=str(info.status),
            points_count=int(info.points_count or 0),
            payload_schema_fields=sorted((info.payload_schema or {}).keys()),
            status="PASS",
        )
        result["stages"].append({"stage": "query", "status": "PASS"})
        success = True
    except BaseException as exc:
        result["error"] = _error(exc)
    finally:
        if success:
            try:
                client.delete_collection(collection)
                result["cleanup"] = "PASS"
            except BaseException as exc:
                result["cleanup"] = "FAIL"
                result["cleanup_error"] = _error(exc)
        else:
            result["cleanup"] = "PRESERVED_FOR_INSPECTION"
    return result


def adapter_probe(*, url: str, grpc_port: int, prefix: str, indexed: bool, point_count: int) -> dict[str, Any]:
    from sgokb.domain.embedding import EmbeddingSpaceSpec
    from sgokb.domain.vector_index import VectorIndexPoint, VectorMatch, VectorSearchFilter
    from sgokb.retrieval.vector_index import QdrantVectorIndexAdapter

    space = EmbeddingSpaceSpec(
        provider_key="n05d01",
        provider_version="1",
        model="deterministic-diagnostic",
        model_revision="1",
        dimension=8,
        native_dimension=8,
        preprocessing_key="n05d01",
        preprocessing_version="1",
    )
    result: dict[str, Any] = {
        "kind": "sgokb_adapter",
        "prefix": prefix,
        "indexed": indexed,
        "point_count": point_count,
        "space_id": space.space_id,
        "status": "FAIL",
    }
    adapter = QdrantVectorIndexAdapter(
        url=url,
        grpc_port=grpc_port,
        prefer_grpc=True,
        collection_prefix=prefix,
        filter_schema=DEFAULT_FIELDS if indexed else {},
    )
    success = False
    try:
        points = [
            VectorIndexPoint(
                point_id=f"point-{index:04d}",
                vector=tuple(_vector(index)),
                metadata=_payload(index),
            )
            for index in range(point_count)
        ]
        inserted = adapter.upsert(space, points)
        if inserted != point_count:
            raise RuntimeError(f"Adapter inserted {inserted}, expected {point_count}")
        hits = adapter.search(
            space,
            _vector(0),
            limit=5,
            filters=VectorSearchFilter(matches=(VectorMatch("object_id", ("object-0",)),)),
        )
        if not hits:
            raise RuntimeError("Adapter diagnostic search returned no hits")
        metadata = adapter.metadata(space)
        result.update(
            points_count=metadata.points_count,
            collection_status=metadata.status,
            hit_count=len(hits),
            status="PASS",
        )
        success = True
    except BaseException as exc:
        result["error"] = _error(exc)
    finally:
        if success:
            try:
                adapter.drop(space)
                result["cleanup"] = "PASS"
            except BaseException as exc:
                result["cleanup"] = "FAIL"
                result["cleanup_error"] = _error(exc)
        else:
            result["cleanup"] = "PRESERVED_FOR_INSPECTION"
    return result


def classify(report: dict[str, Any]) -> dict[str, Any]:
    if report.get("server", {}).get("status") != "PASS":
        return {
            "classification": "QDRANT_ENVIRONMENT_DEFECT",
            "reason": "Qdrant server is unreachable or server metadata cannot be read.",
        }
    probes = report.get("probes", {})
    plain = probes.get("direct_plain", {})
    indexed = probes.get("direct_indexed", {})
    adapter_plain = probes.get("adapter_plain", {})
    adapter_indexed = probes.get("adapter_indexed", {})
    if plain.get("status") != "PASS":
        return {
            "classification": "QDRANT_ENVIRONMENT_DEFECT",
            "reason": "Direct Qdrant operations fail even without payload indexes.",
        }
    if indexed.get("status") != "PASS":
        return {
            "classification": "OTHER_IDENTIFIED_CAUSE",
            "subtype": "QDRANT_PAYLOAD_INDEX_STORAGE_PATH_REPRODUCED",
            "reason": (
                "Direct client succeeds without payload indexes but fails when the SGOKB "
                "payload-index schema is created. The SGOKB adapter is not the primary trigger; "
                "use server/storage evidence to distinguish backend product behavior from the local environment."
            ),
        }
    if adapter_plain.get("status") != "PASS" or adapter_indexed.get("status") != "PASS":
        return {
            "classification": "SGOKB_ADAPTER_DEFECT",
            "reason": "Direct Qdrant probes pass but an equivalent SGOKB adapter probe fails.",
        }
    return {
        "classification": "NOT_REPRODUCED",
        "reason": (
            "Direct and adapter paths pass. Repeat against an isolated fresh Qdrant server and compare "
            "process/config/storage evidence with the failed N-05 server."
        ),
    }


def run(args: argparse.Namespace) -> dict[str, Any]:
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    prefix = args.prefix or f"n05d01_{uuid.uuid4().hex[:10]}"
    report: dict[str, Any] = {
        "schema_version": "sgokb.n05d01.qdrant-diagnosis.v1",
        "url": args.url,
        "grpc_port": args.grpc_port,
        "http_port": args.http_port,
        "prefix": prefix,
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "python": platform.python_version(),
        },
        "server_process": windows_process_for_port(args.http_port),
        "storage_candidates": [
            path_evidence(path)
            for path in (
                ROOT / ".local" / "n04p06" / "qdrant",
                ROOT / ".local" / "qdrant-1.19.2",
                *(Path(value) for value in args.storage_path),
            )
        ],
        "server": {"status": "FAIL"},
        "probes": {},
    }
    try:
        report["server"] = {"status": "PASS", "root": server_root(args.url)}
    except BaseException as exc:
        report["server"] = {"status": "FAIL", "error": _error(exc)}
        report["diagnosis"] = classify(report)
        write_json(output, report)
        return report

    report["probes"]["direct_plain"] = direct_probe(
        url=args.url,
        grpc_port=args.grpc_port,
        collection=f"{prefix}_direct_plain",
        indexed=False,
        point_count=args.point_count,
    )
    report["probes"]["direct_indexed"] = direct_probe(
        url=args.url,
        grpc_port=args.grpc_port,
        collection=f"{prefix}_direct_indexed",
        indexed=True,
        point_count=args.point_count,
    )
    report["probes"]["adapter_plain"] = adapter_probe(
        url=args.url,
        grpc_port=args.grpc_port,
        prefix=f"{prefix}_adapter_plain",
        indexed=False,
        point_count=args.point_count,
    )
    report["probes"]["adapter_indexed"] = adapter_probe(
        url=args.url,
        grpc_port=args.grpc_port,
        prefix=f"{prefix}_adapter_indexed",
        indexed=True,
        point_count=args.point_count,
    )
    repeated = []
    for index in range(args.repeat_indexed):
        probe = direct_probe(
            url=args.url,
            grpc_port=args.grpc_port,
            collection=f"{prefix}_repeat_{index:02d}",
            indexed=True,
            point_count=args.point_count,
        )
        repeated.append(probe)
        if probe.get("status") != "PASS":
            break
    report["probes"]["direct_indexed_repeated"] = repeated
    report["diagnosis"] = classify(report)
    write_json(output, report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://localhost:6333")
    parser.add_argument("--http-port", type=int, default=6333)
    parser.add_argument("--grpc-port", type=int, default=6334)
    parser.add_argument("--point-count", type=int, default=256)
    parser.add_argument("--repeat-indexed", type=int, default=5)
    parser.add_argument("--prefix")
    parser.add_argument("--storage-path", action="append", default=[])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        report = run(args)
    except BaseException as exc:
        write_json(
            args.output,
            {
                "schema_version": "sgokb.n05d01.qdrant-diagnosis.v1",
                "fatal_error": _error(exc),
            },
        )
        raise
    classification = report.get("diagnosis", {}).get("classification")
    return 0 if classification == "NOT_REPRODUCED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
