"""Real provider adapters. Test doubles live exclusively in tests/."""

import json
import os
import time

import httpx

from .domain import json_text, validate_vectors
from .errors import OutputBudgetExceeded


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
        structured_mode=None,
    ):
        self.model, self.revision = model, revision
        self.base_url = base_url.rstrip("/")
        self.max_tokens, self.extra = max_tokens, extra or {}
        mode = structured_mode or (
            "prompt_only"
            if self.extra.get("response_format", {}).get("type") == "text"
            else "api_schema"
        )
        if mode not in {"prompt_only", "api_schema"}:
            raise ValueError("Unknown structured mode")
        if structured_mode and "response_format" in self.extra:
            raise ValueError("Use structured_mode without a response_format override")
        self.configuration = {
            "structured_mode": mode,
            "constraint_method": "unknown",
            "temperature": self.extra.get("temperature", 0),
            "max_tokens": self.extra.get("max_tokens", max_tokens),
            "reasoning_effort": self.extra.get("reasoning_effort"),
            "response_format_override": self.extra.get("response_format"),
            "seed": self.extra.get("seed"),
            "extra_parameters": {
                k: self.extra[k]
                for k in ("top_p", "top_k", "min_p", "repeat_penalty", "chat_template_kwargs")
                if k in self.extra
            },
            "runtime_metadata": json.loads(os.environ.get("CPC_RUNTIME_METADATA_JSON", "{}")),
        }
        self.client = httpx.Client(
            timeout=timeout,
            transport=transport,
            headers={"Authorization": f"Bearer {api_key}"} if api_key else {},
        )

    def complete(self, prompt, payload, *, schema=None):
        started = time.perf_counter()
        self.last_observation = {}
        self.last_output = None
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
                    if schema and self.configuration["structured_mode"] == "api_schema"
                    else {}
                ),
                **self.extra,
            },
        )
        self._check_response(response, started)
        body = response.json()
        usage = body.get("usage", {})
        elapsed = time.perf_counter() - started
        tokens = usage.get("completion_tokens")
        self.last_observation = {
            "duration_seconds": elapsed,
            "usage": usage,
            "tokens_per_second": tokens / elapsed if isinstance(tokens, int) and elapsed else None,
            "actual_model": body.get("model", self.model),
            "runtime_metadata": self.configuration["runtime_metadata"],
            "vram_bytes": None,
            "ram_bytes": None,
            **self._response_metrics(body),
        }
        choice = body["choices"][0]
        self.last_output = choice["message"].get("content")
        if choice.get("finish_reason") == "length":
            raise OutputBudgetExceeded("LLM output truncated; increase CPC_LLM_MAX_TOKENS")
        content = choice["message"].get("content")
        if not isinstance(content, str) or not content.strip():
            raise ValueError("LLM returned no content")
        return content

    def _check_response(self, response, started):
        response.raise_for_status()

    def _response_metrics(self, body):
        return {}


class StrataLLM(CompatibleLLM):
    """Shared Strata server; retain CPC validation and distinguish budget failures."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        template = {"enable_thinking": False, **self.extra.get("chat_template_kwargs", {})}
        self.extra = {**self.extra, "chat_template_kwargs": template}
        self.configuration["extra_parameters"]["chat_template_kwargs"] = template
        self.configuration["adapter"] = "strata-compatible-v1"
        self.configuration["constraint_method"] = "prompt_and_validate"

    def _check_response(self, response, started):
        if response.status_code == 502:
            try:
                error = response.json().get("error", {})
            except ValueError:
                error = {}
            if isinstance(error, dict) and "structured_output_failed" in (
                error.get("code"),
                error.get("type"),
            ):
                message = str(error.get("message", "Strata structured output failed"))
                self.last_observation = {
                    "duration_seconds": time.perf_counter() - started,
                    "http_status": response.status_code,
                    "error_code": "structured_output_failed",
                    "runtime_metadata": self.configuration["runtime_metadata"],
                }
                if "finish_reason=length" in message:
                    raise OutputBudgetExceeded("LLM output reached token budget")
                raise ValueError(message)
        response.raise_for_status()

    def _response_metrics(self, body):
        timings = body.get("timings", {})
        return {
            "engine_tokens_per_second": timings.get("predicted_per_second"),
            "timings": timings,
        }


class LMStudioLLM(CompatibleLLM):
    """Native local adapter with explicit reasoning controls and no chat/tool persistence."""

    def __init__(self, *args, **kwargs):
        kwargs["structured_mode"] = kwargs.get("structured_mode") or "prompt_only"
        super().__init__(*args, **kwargs)
        if self.configuration["structured_mode"] != "prompt_only":
            raise ValueError("Use the compatible adapter for LM Studio API Schema requests")
        permitted = {
            "temperature",
            "top_p",
            "top_k",
            "min_p",
            "repeat_penalty",
            "reasoning",
            "max_tokens",
        }
        if set(self.extra) - permitted:
            raise ValueError("Unsupported LM Studio native inference parameters")
        self.configuration.update(
            adapter="lmstudio-native-v1", reasoning=self.extra.get("reasoning", "off"), store=False
        )

    def complete(self, prompt, payload, *, schema=None):
        started = time.perf_counter()
        self.last_observation = {}
        self.last_output = None
        budget = self.extra.get("max_tokens", self.max_tokens)
        root = self.base_url.removesuffix("/v1")
        response = self.client.post(
            root + "/api/v1/chat",
            json={
                "model": self.model,
                "system_prompt": prompt,
                "input": json_text(payload),
                "temperature": self.extra.get("temperature", 0),
                "reasoning": self.extra.get("reasoning", "off"),
                "max_output_tokens": budget,
                "store": False,
                "integrations": [],
                **{
                    k: v
                    for k, v in self.extra.items()
                    if k in {"top_p", "top_k", "min_p", "repeat_penalty"}
                },
            },
        )
        response.raise_for_status()
        body = response.json()
        stats = body.get("stats", {})
        self.last_observation = {
            "duration_seconds": time.perf_counter() - started,
            "usage": stats,
            "tokens_per_second": stats.get("tokens_per_second"),
            "actual_model": body.get("model_instance_id", self.model),
            "runtime_metadata": self.configuration["runtime_metadata"],
            "vram_bytes": None,
            "ram_bytes": None,
        }
        if any(item.get("type") not in {"message", "reasoning"} for item in body.get("output", [])):
            raise ValueError("Unexpected tool output from knowledge extraction provider")
        content = "\n".join(
            item["content"] for item in body.get("output", []) if item.get("type") == "message"
        )
        self.last_output = content
        if stats.get("total_output_tokens", 0) >= budget:
            raise OutputBudgetExceeded("LLM output reached token budget")
        if not content.strip():
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
    provider = {"compatible": CompatibleLLM, "lmstudio": LMStudioLLM, "strata": StrataLLM}.get(
        os.environ.get("CPC_LLM_PROVIDER", "compatible")
    )
    if provider is None:
        raise ValueError("Unknown LLM provider")
    return provider(
        os.environ.get("CPC_LLM_BASE_URL", "http://127.0.0.1:1234/v1"),
        model,
        os.environ.get("CPC_LLM_REVISION", "unknown"),
        os.environ.get("CPC_LLM_API_KEY"),
        float(os.environ.get("CPC_API_TIMEOUT", "180")),
        int(os.environ.get("CPC_LLM_MAX_TOKENS", "3000")),
        extra,
        structured_mode=os.environ.get("CPC_LLM_STRUCTURED_MODE"),
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
