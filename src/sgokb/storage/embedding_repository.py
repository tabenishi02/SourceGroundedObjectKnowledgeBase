"""Embedding Space and Search Representation vector cache persistence for I-02."""

from __future__ import annotations

import sqlite3
import struct
from datetime import datetime, timezone
from typing import Iterable

from sgokb.domain._prototype import validate_vectors
from sgokb.domain.embedding import EmbeddingSpaceRecord, EmbeddingSpaceSpec


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _pack(vector: list[float]) -> bytes:
    return struct.pack(f"<{len(vector)}f", *vector)


def _unpack(raw: bytes, dimension: int) -> list[float]:
    if len(raw) != 4 * dimension:
        raise ValueError("Stored embedding byte length does not match dimension")
    return list(struct.unpack(f"<{dimension}f", raw))


class EmbeddingRepository:
    """SQLite cache for vectors; canonical Knowledge remains outside this failure domain."""

    def __init__(self, db: sqlite3.Connection):
        self.db = db

    def ensure_space(self, spec: EmbeddingSpaceSpec) -> str:
        existing = self.db.execute(
            "SELECT id FROM search_embedding_spaces WHERE configuration_hash=?",
            (spec.configuration_hash,),
        ).fetchone()
        if existing:
            return existing["id"]
        with self.db:
            self.db.execute(
                """INSERT INTO search_embedding_spaces
                   (id,provider_key,provider_version,model,model_revision,dimension,
                    native_dimension,preprocessing_key,preprocessing_version,
                    query_instruction,document_instruction,normalize_embeddings,
                    max_sequence_length,overflow_policy,output_dtype,provider_configuration,
                    configuration_hash,created_at)
                   VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    spec.space_id,
                    spec.provider_key,
                    spec.provider_version,
                    spec.model,
                    spec.model_revision,
                    spec.dimension,
                    spec.native_dimension,
                    spec.preprocessing_key,
                    spec.preprocessing_version,
                    spec.query_instruction,
                    spec.document_instruction,
                    int(spec.normalize_embeddings),
                    spec.max_sequence_length,
                    spec.overflow_policy,
                    spec.output_dtype,
                    spec.provider_configuration,
                    spec.configuration_hash,
                    _now(),
                ),
            )
        return spec.space_id

    def space_by_id(self, space_id: str) -> EmbeddingSpaceRecord:
        row = self.db.execute(
            "SELECT * FROM search_embedding_spaces WHERE id=?", (space_id,)
        ).fetchone()
        if not row:
            raise ValueError("Unknown Embedding Space ID")
        spec = EmbeddingSpaceSpec(
            provider_key=row["provider_key"],
            provider_version=row["provider_version"],
            model=row["model"],
            model_revision=row["model_revision"],
            dimension=row["dimension"],
            native_dimension=row["native_dimension"],
            preprocessing_key=row["preprocessing_key"],
            preprocessing_version=row["preprocessing_version"],
            query_instruction=row["query_instruction"],
            document_instruction=row["document_instruction"],
            normalize_embeddings=bool(row["normalize_embeddings"]),
            max_sequence_length=row["max_sequence_length"],
            overflow_policy=row["overflow_policy"],
            output_dtype=row["output_dtype"],
            provider_configuration=row["provider_configuration"],
        )
        if spec.space_id != row["id"]:
            raise ValueError("Stored Embedding Space identity does not match metadata")
        return EmbeddingSpaceRecord(spec=spec, created_at=row["created_at"])

    def save_representation_embedding(
        self,
        spec: EmbeddingSpaceSpec,
        representation_id: str,
        vector: list[float],
    ) -> bool:
        validate_vectors([vector], 1)
        if len(vector) != spec.dimension:
            raise ValueError("Embedding vector dimension does not match Embedding Space")
        representation = self.db.execute(
            "SELECT content_hash FROM search_representations WHERE id=?", (representation_id,)
        ).fetchone()
        if not representation:
            raise ValueError("Unknown Search Representation ID")
        self.ensure_space(spec)
        existing = self.db.execute(
            """SELECT content_hash FROM search_representation_embeddings
               WHERE space_id=? AND representation_id=?""",
            (spec.space_id, representation_id),
        ).fetchone()
        if existing:
            if existing["content_hash"] != representation["content_hash"]:
                raise ValueError("Stored embedding belongs to different representation content")
            return False
        with self.db:
            self.db.execute(
                """INSERT INTO search_representation_embeddings
                   (space_id,representation_id,content_hash,vector,created_at)
                   VALUES(?,?,?,?,?)""",
                (
                    spec.space_id,
                    representation_id,
                    representation["content_hash"],
                    sqlite3.Binary(_pack(vector)),
                    _now(),
                ),
            )
        return True

    def representation_embedding(self, space_id: str, representation_id: str) -> list[float]:
        space = self.space_by_id(space_id).spec
        row = self.db.execute(
            """SELECT e.vector,e.content_hash,r.content_hash AS current_content_hash
               FROM search_representation_embeddings e
               JOIN search_representations r ON r.id=e.representation_id
               WHERE e.space_id=? AND e.representation_id=?""",
            (space_id, representation_id),
        ).fetchone()
        if not row:
            raise ValueError("Search Representation has no embedding in this space")
        if row["content_hash"] != row["current_content_hash"]:
            raise ValueError("Stored embedding is stale for Search Representation content")
        return _unpack(row["vector"], space.dimension)

    def embedding_rows(
        self, space_id: str, representation_ids: Iterable[str] | None = None
    ) -> tuple[dict, ...]:
        space = self.space_by_id(space_id).spec
        requested = tuple(dict.fromkeys(representation_ids or ()))
        parameters: list[str] = [space_id]
        condition = ""
        if requested:
            placeholders = ",".join("?" for _ in requested)
            condition = f" AND e.representation_id IN ({placeholders})"
            parameters.extend(requested)
        rows = self.db.execute(
            """SELECT e.representation_id,e.content_hash,e.vector,r.kind,r.content
               FROM search_representation_embeddings e
               JOIN search_representations r ON r.id=e.representation_id
               WHERE e.space_id=? AND e.content_hash=r.content_hash"""
            + condition
            + " ORDER BY e.representation_id",
            parameters,
        ).fetchall()
        return tuple(
            {
                "representation_id": row["representation_id"],
                "content_hash": row["content_hash"],
                "kind": row["kind"],
                "content": row["content"],
                "vector": _unpack(row["vector"], space.dimension),
            }
            for row in rows
        )
