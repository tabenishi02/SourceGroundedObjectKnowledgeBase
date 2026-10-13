"""Persistence-independent embedding contracts for Phase I / I-02."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Protocol


def _canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


@dataclass(frozen=True, slots=True)
class EmbeddingSpaceSpec:
    """Identity of one mutually compatible embedding vector space."""

    provider_key: str
    provider_version: str
    model: str
    model_revision: str
    dimension: int
    native_dimension: int
    preprocessing_key: str
    preprocessing_version: str
    query_instruction: str = ""
    document_instruction: str = ""
    normalize_embeddings: bool = True
    max_sequence_length: int | None = None
    overflow_policy: str = "reject"
    output_dtype: str = "float32"
    provider_configuration: str = "{}"

    def __post_init__(self) -> None:
        required = (
            self.provider_key,
            self.provider_version,
            self.model,
            self.model_revision,
            self.preprocessing_key,
            self.preprocessing_version,
            self.output_dtype,
        )
        if any(not value.strip() for value in required):
            raise ValueError("Embedding Space string identity fields must be non-empty")
        if self.dimension <= 0 or self.native_dimension <= 0:
            raise ValueError("Embedding dimensions must be positive")
        if self.dimension > self.native_dimension:
            raise ValueError("Embedding output dimension cannot exceed native dimension")
        if self.max_sequence_length is not None and self.max_sequence_length <= 0:
            raise ValueError("Embedding max sequence length must be positive")
        if self.overflow_policy not in {"reject", "truncate"}:
            raise ValueError("Embedding overflow policy must be reject or truncate")
        try:
            parsed = json.loads(self.provider_configuration)
        except json.JSONDecodeError as exc:
            raise ValueError("provider_configuration must be JSON") from exc
        object.__setattr__(self, "provider_configuration", _canonical_json(parsed))

    @property
    def configuration_payload(self) -> dict:
        return {
            "provider_key": self.provider_key,
            "provider_version": self.provider_version,
            "model": self.model,
            "model_revision": self.model_revision,
            "dimension": self.dimension,
            "native_dimension": self.native_dimension,
            "preprocessing_key": self.preprocessing_key,
            "preprocessing_version": self.preprocessing_version,
            "query_instruction": self.query_instruction,
            "document_instruction": self.document_instruction,
            "normalize_embeddings": self.normalize_embeddings,
            "max_sequence_length": self.max_sequence_length,
            "overflow_policy": self.overflow_policy,
            "output_dtype": self.output_dtype,
            "provider_configuration": json.loads(self.provider_configuration),
        }

    @property
    def configuration_hash(self) -> str:
        raw = _canonical_json(self.configuration_payload).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    @property
    def space_id(self) -> str:
        return self.configuration_hash


@dataclass(frozen=True, slots=True)
class EmbeddingSpaceRecord:
    spec: EmbeddingSpaceSpec
    created_at: str


class EmbeddingProvider(Protocol):
    """Local embedding provider boundary used before VectorIndexAdapter exists."""

    @property
    def space(self) -> EmbeddingSpaceSpec: ...

    def embed_documents(self, texts: list[str]) -> list[list[float]]: ...

    def embed_queries(self, texts: list[str]) -> list[list[float]]: ...
