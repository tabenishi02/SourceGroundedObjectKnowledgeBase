"""Real provider adapters. Test doubles live exclusively in tests/."""

import json
import os

import httpx

from .domain import json_text, validate_vectors


class CompatibleLLM:
    def __init__(
        self,
        base_url,
        model,
        revision="unknown",
        api_key=None,
        timeout=180,
        max_tokens=3000,
        extra=None,
        transport=None,
    ):
        self.model, self.revision = model, revision
        self.base_url = base_url.rstrip("/")
        self.max_tokens, self.extra = max_tokens, extra or {}
        self.configuration = {
            "temperature": self.extra.get("temperature", 0),
            "max_tokens": self.extra.get("max_tokens", max_tokens),
            "reasoning_effort": self.extra.get("reasoning_effort"),
            "response_format_override": self.extra.get("response_format"),
        }
        self.client = httpx.Client(
            timeout=timeout,
            transport=transport,
            headers={"Authorization": f"Bearer {api_key}"} if api_key else {},
        )

    def complete(self, prompt, payload, *, schema=None):
        response = self.client.post(
            self.base_url + "/chat/completions",
            json={
                "model": self.model,
                "temperature": 0,
                "max_tokens": self.max_tokens,
                "messages": [
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": json_text(payload)},
                ],
                **(
                    {
                        "response_format": {
                            "type": "json_schema",
                            "json_schema": {
                                "name": "cpc_response",
                                "strict": True,
                                "schema": schema,
                            },
                        }
                    }
                    if schema
                    else {}
                ),
                **self.extra,
            },
        )
        response.raise_for_status()
        choice = response.json()["choices"][0]
        if choice.get("finish_reason") == "length":
            raise ValueError("LLM output truncated; increase CPC_LLM_MAX_TOKENS")
        content = choice["message"].get("content")
        if not isinstance(content, str) or not content.strip():
            raise ValueError("LLM returned no content")
        return content


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


def llm_from_env(task_type=None):
    model = os.environ.get("CPC_LLM_MODEL")
    if not model:
        raise ValueError("Set CPC_LLM_MODEL (real provider required)")
    extra = json.loads(os.environ.get("CPC_LLM_EXTRA_JSON", "{}"))
    if task_type in {"fragment", "final"}:
        extra.update(
            json.loads(os.environ.get("CPC_LLM_" + task_type.upper() + "_EXTRA_JSON", "{}"))
        )
    return CompatibleLLM(
        os.environ.get("CPC_LLM_BASE_URL", "http://127.0.0.1:1234/v1"),
        model,
        os.environ.get("CPC_LLM_REVISION", "unknown"),
        os.environ.get("CPC_LLM_API_KEY"),
        float(os.environ.get("CPC_API_TIMEOUT", "180")),
        int(os.environ.get("CPC_LLM_MAX_TOKENS", "3000")),
        extra,
    )


def embedder_from_env():
    model = os.environ.get("CPC_EMBED_MODEL")
    if not model:
        raise ValueError("Set CPC_EMBED_MODEL (real embedding provider required)")
    options = {
        "document_prefix": os.environ.get("CPC_EMBED_DOCUMENT_PREFIX", ""),
        "query_prefix": os.environ.get("CPC_EMBED_QUERY_PREFIX", ""),
        "max_chars": int(os.environ.get("CPC_EMBED_MAX_CHARS", "600")),
    }
    revision = os.environ.get("CPC_EMBED_REVISION", "unknown")
    if os.environ.get("CPC_EMBED_PROVIDER", "compatible") == "sentence-transformers":
        return SentenceTransformerEmbedder(model, revision, **options)
    return CompatibleEmbedder(
        os.environ.get("CPC_EMBED_BASE_URL", "http://127.0.0.1:1234/v1"),
        model,
        revision,
        os.environ.get("CPC_EMBED_API_KEY"),
        float(os.environ.get("CPC_API_TIMEOUT", "180")),
        **options,
    )
