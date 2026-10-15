"""Real provider adapters. Test doubles live exclusively in tests/."""

import os

import httpx

from .domain import json_text, validate_vectors


class CompatibleEmbedder:
    def __init__(
        self,
        base_url,
        model,
        revision="unknown",
        api_key=None,
        timeout=180,
        document_prefix="",
        query_prefix="",
        max_chars=600,
        transport=None,
    ):
        self.base_url, self.model, self.revision = base_url.rstrip("/"), model, revision
        self.document_prefix, self.query_prefix, self.max_chars = (
            document_prefix,
            query_prefix,
            max_chars,
        )
        self.configuration = json_text(
            {
                "document_prefix": document_prefix,
                "query_prefix": query_prefix,
                "max_chars": max_chars,
                "adapter": "compatible-v1",
            }
        )
        self.client = httpx.Client(
            timeout=timeout,
            transport=transport,
            headers={"Authorization": f"Bearer {api_key}"} if api_key else {},
        )

    def embed(self, texts, *, query=False):
        prefix = self.query_prefix if query else self.document_prefix
        response = self.client.post(
            self.base_url + "/embeddings",
            json={
                "model": self.model,
                "input": [prefix + text[: self.max_chars] for text in texts],
            },
        )
        response.raise_for_status()
        data = sorted(response.json()["data"], key=lambda x: x["index"])
        if [x["index"] for x in data] != list(range(len(texts))):
            raise ValueError("Invalid embedding response indexes")
        vectors = [item["embedding"] for item in data]
        validate_vectors(vectors, len(texts))
        return vectors


class SentenceTransformerEmbedder:
    def __init__(self, model, revision, document_prefix="", query_prefix="", max_chars=1000):
        from sentence_transformers import SentenceTransformer

        self.model, self.revision = model, revision
        self.document_prefix, self.query_prefix, self.max_chars = (
            document_prefix,
            query_prefix,
            max_chars,
        )
        self.configuration = json_text(
            {
                "document_prefix": document_prefix,
                "query_prefix": query_prefix,
                "max_chars": max_chars,
                "adapter": "sentence-transformers-v1",
            }
        )
        self.encoder = SentenceTransformer(
            model,
            revision=None if revision == "unknown" else revision,
            cache_folder=".local/models",
            device="cpu",
        )

    def embed(self, texts, *, query=False):
        prefix = self.query_prefix if query else self.document_prefix
        return self.encoder.encode(
            [prefix + t[: self.max_chars] for t in texts], normalize_embeddings=True
        ).tolist()


def embedder_from_env():
    model = os.environ.get("SGOKB_EMBED_MODEL")
    if not model:
        raise ValueError("Set SGOKB_EMBED_MODEL (real embedding provider required)")
    options = {
        "document_prefix": os.environ.get("SGOKB_EMBED_DOCUMENT_PREFIX", ""),
        "query_prefix": os.environ.get("SGOKB_EMBED_QUERY_PREFIX", ""),
        "max_chars": int(os.environ.get("SGOKB_EMBED_MAX_CHARS", "600")),
    }
    revision = os.environ.get("SGOKB_EMBED_REVISION", "unknown")
    if os.environ.get("SGOKB_EMBED_PROVIDER", "compatible") == "sentence-transformers":
        return SentenceTransformerEmbedder(model, revision, **options)
    return CompatibleEmbedder(
        os.environ.get("SGOKB_EMBED_BASE_URL", "http://127.0.0.1:1234/v1"),
        model,
        revision,
        os.environ.get("SGOKB_EMBED_API_KEY"),
        float(os.environ.get("SGOKB_API_TIMEOUT", "180")),
        **options,
    )
