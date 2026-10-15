"""Persistence-independent value objects and replaceable processing boundaries."""

import hashlib
import json
import math
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone


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
