"""Persistence-independent value objects and replaceable processing boundaries."""

import hashlib
import json
import math
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Protocol


def now():
    return datetime.now(timezone.utc).isoformat()


def uid():
    return str(uuid.uuid4())


def digest(value):
    raw = value if isinstance(value, bytes) else value.encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def json_text(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


@dataclass
class Bundle:
    path: str
    sha256: str
    manifest: dict
    artifacts: dict[str, bytes]
    metadata: dict


@dataclass
class Block:
    kind: str
    content: str
    section: list[str]
    position: str
    artifact: str = "dom/main.html"
    metadata: dict = field(default_factory=dict)


@dataclass(frozen=True)
class SearchFilter:
    entity: str | None = None
    source: str | None = None
    snapshot: str | None = None
    site: str | None = None
    source_type: str | None = None
    facet: str | None = None


@dataclass(frozen=True)
class EmbeddingSpace:
    model: str
    revision: str
    dimension: int
    configuration: str

    @property
    def key(self):
        return digest(json_text(self.__dict__))


class LLM(Protocol):
    model: str
    revision: str

    def complete(self, prompt: str, payload: dict, *, schema: dict | None = None) -> str: ...


class Embedder(Protocol):
    model: str
    revision: str
    configuration: str

    def embed(self, texts: list[str], *, query: bool = False) -> list[list[float]]: ...


class VectorIndex(Protocol):
    def search(self, vector: list[float], rows: list[dict], limit: int) -> list[dict]: ...


class Reranker(Protocol):
    version: str

    def rank(self, query: str, candidates: list[dict], limit: int) -> list[dict]: ...


def validate_vectors(vectors, count):
    if not isinstance(vectors, list) or len(vectors) != count:
        raise ValueError("Embedding response count mismatch")
    dimension = len(vectors[0]) if vectors else 0
    if not dimension or any(
        len(v) != dimension
        or not all(isinstance(x, (int, float)) and math.isfinite(x) for x in v)
        or sum(x * x for x in v) == 0
        for v in vectors
    ):
        raise ValueError("Invalid embedding vectors")
    return dimension


def validate_fragments(output, allowed_ids):
    if not isinstance(output, dict) or not isinstance(output.get("fragments"), list):
        raise ValueError("Expected fragments array")
    for item in output["fragments"]:
        if not isinstance(item, dict):
            raise ValueError("Fragment must be an object")
        for key in ("content", "facet"):
            if not isinstance(item.get(key), str) or not item[key].strip():
                raise ValueError(f"Fragment {key} required")
        refs = item.get("evidence_ids")
        if (
            not isinstance(refs, list)
            or not refs
            or any(not isinstance(e, str) or e not in allowed_ids for e in refs)
        ):
            raise ValueError("Fragment references unknown or absent evidence")
    return output["fragments"]
