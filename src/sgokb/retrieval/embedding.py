"""Local embedding providers and Exact evaluation baseline for Phase I / I-02."""

from __future__ import annotations

import json
import math
from importlib import metadata
from typing import Iterable

from sgokb.domain.embedding import EmbeddingSpaceSpec
from sgokb.domain.primitives import validate_vectors

DEFAULT_RETRIEVAL_INSTRUCTION = (
    "Given a query about an object knowledge base, retrieve semantically relevant "
    "object knowledge statements."
)
PREPROCESSING_KEY = "sgokb-search-representation"
PREPROCESSING_VERSION = "2"

# I-02 frozen common profile after the 2026 model extension.
# Revision is the evaluated Hugging Face snapshot.
DEFAULT_EMBEDDING_MODEL = "microsoft/harrier-oss-v1-0.6b"
DEFAULT_EMBEDDING_REVISION = "f9b9dc8d367d443f2479d27aa5d8d2850c0774ee"
DEFAULT_EMBEDDING_DIMENSION = 1024
DEFAULT_EMBEDDING_MAX_SEQUENCE_LENGTH = 32768

# Faster short-Statement alternative retained for I-07 validation.
STATEMENT_FAST_MODEL = "intfloat/multilingual-e5-large-instruct"
STATEMENT_FAST_REVISION = "274baa43b0e13e37fafa6428dbc7938e62e5c439"
STATEMENT_FAST_DIMENSION = 1024
STATEMENT_FAST_MAX_SEQUENCE_LENGTH = 512


def _normalize_rows(rows: Iterable[Iterable[float]]) -> list[list[float]]:
    output: list[list[float]] = []
    for row in rows:
        values = [float(value) for value in row]
        length = math.sqrt(sum(value * value for value in values))
        if not length:
            raise ValueError("Embedding vector cannot be zero")
        output.append([value / length for value in values])
    validate_vectors(output, len(output))
    return output


def _qwen_query(instruction: str, query: str) -> str:
    return f"Instruct: {instruction}\nQuery: {query}" if instruction else query


class SentenceTransformerEmbeddingProvider:
    """GPU-capable local provider; no external-provider fallback is performed."""

    provider_key = "sentence-transformers"

    def __init__(
        self,
        model: str,
        *,
        revision: str | None = None,
        device: str | None = None,
        batch_size: int = 64,
        query_instruction: str = DEFAULT_RETRIEVAL_INSTRUCTION,
        document_instruction: str = "",
        normalize_embeddings: bool = True,
        truncate_dim: int | None = None,
        dtype: str | None = None,
        cache_folder: str | None = None,
        local_files_only: bool = False,
        max_sequence_length: int | None = None,
        overflow_policy: str = "reject",
    ):
        try:
            import torch
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise RuntimeError(
                "SentenceTransformer provider requires the local-embedding dependency"
            ) from exc

        self.model = model
        self.requested_revision = revision
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.batch_size = batch_size
        self.query_instruction = query_instruction
        self.document_instruction = document_instruction
        self.normalize_embeddings = normalize_embeddings
        self.truncate_dim = truncate_dim
        self.dtype = dtype
        if overflow_policy not in {"reject", "truncate"}:
            raise ValueError("overflow_policy must be reject or truncate")
        self.overflow_policy = overflow_policy
        model_kwargs: dict[str, object] = {"local_files_only": local_files_only}
        if revision:
            model_kwargs["revision"] = revision
        if dtype:
            torch_dtype = getattr(torch, dtype, None)
            if torch_dtype is None:
                raise ValueError(f"Unknown torch dtype: {dtype}")
            model_kwargs["torch_dtype"] = torch_dtype
        self._encoder = SentenceTransformer(
            model,
            device=self.device,
            cache_folder=cache_folder,
            revision=revision,
            local_files_only=local_files_only,
            truncate_dim=truncate_dim,
            model_kwargs=model_kwargs,
        )
        transformer = self._encoder[0]
        get_dimension = getattr(transformer, "get_embedding_dimension", None)
        if get_dimension is None:
            get_dimension = transformer.get_word_embedding_dimension
        native_dimension = int(get_dimension())
        output_dimension = int(truncate_dim or native_dimension)
        provider_limit = int(self._encoder.max_seq_length)
        self.max_sequence_length = min(max_sequence_length or provider_limit, provider_limit)
        self._encoder.max_seq_length = self.max_sequence_length
        config = getattr(getattr(transformer, "auto_model", None), "config", None)
        actual_revision = getattr(config, "_commit_hash", None) or revision or "main"
        provider_version = metadata.version("sentence-transformers")
        provider_configuration = json.dumps(
            {
                "dtype": dtype or "provider_default",
                "truncate_dim": truncate_dim,
                "local_files_only": bool(local_files_only),
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        self._space = EmbeddingSpaceSpec(
            provider_key=self.provider_key,
            provider_version=provider_version,
            model=model,
            model_revision=str(actual_revision),
            dimension=output_dimension,
            native_dimension=native_dimension,
            preprocessing_key=PREPROCESSING_KEY,
            preprocessing_version=PREPROCESSING_VERSION,
            query_instruction=query_instruction,
            document_instruction=document_instruction,
            normalize_embeddings=normalize_embeddings,
            max_sequence_length=self.max_sequence_length,
            overflow_policy=overflow_policy,
            output_dtype="float32",
            provider_configuration=provider_configuration,
        )

    @property
    def space(self) -> EmbeddingSpaceSpec:
        return self._space

    @property
    def revision(self) -> str:
        return self.space.model_revision

    @property
    def configuration(self) -> str:
        return self.space.provider_configuration

    def _encode(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        if self.overflow_policy == "reject":
            encoded = self._encoder.tokenizer(
                texts, add_special_tokens=True, padding=False, truncation=False
            )["input_ids"]
            oversized = [
                index for index, ids in enumerate(encoded) if len(ids) > self.max_sequence_length
            ]
            if oversized:
                raise ValueError(
                    "Embedding input exceeds configured max_sequence_length; "
                    "silent truncation is disabled"
                )
        values = self._encoder.encode(
            texts,
            batch_size=self.batch_size,
            normalize_embeddings=self.normalize_embeddings,
            convert_to_numpy=True,
            show_progress_bar=False,
        )
        rows = [[float(value) for value in row] for row in values]
        validate_vectors(rows, len(texts))
        return rows

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        values = [
            f"{self.document_instruction}{text}" if self.document_instruction else text
            for text in texts
        ]
        return self._encode(values)

    def embed_queries(self, texts: list[str]) -> list[list[float]]:
        return self._encode([_qwen_query(self.query_instruction, text) for text in texts])

    def embed(self, texts: list[str], *, query: bool = False) -> list[list[float]]:
        """Adapt document/query embedding for canonical Evidence retrieval."""
        return self.embed_queries(texts) if query else self.embed_documents(texts)


class FastEmbedEmbeddingProvider:
    """ONNX local provider for supported models; useful as a CPU/portable profile."""

    provider_key = "fastembed"

    def __init__(
        self,
        model: str,
        *,
        cache_dir: str | None = None,
        query_instruction: str = DEFAULT_RETRIEVAL_INSTRUCTION,
        document_instruction: str = "",
        batch_size: int = 256,
        cuda: bool = False,
    ):
        try:
            from fastembed import TextEmbedding
        except ImportError as exc:
            raise RuntimeError("FastEmbed provider requires the fastembed dependency") from exc
        descriptions = {item["model"]: item for item in TextEmbedding.list_supported_models()}
        if model not in descriptions:
            raise ValueError(f"FastEmbed does not support model {model!r}")
        description = descriptions[model]
        self.model = model
        self.batch_size = batch_size
        self.query_instruction = query_instruction
        self.document_instruction = document_instruction
        self._encoder = TextEmbedding(
            model_name=model,
            cache_dir=cache_dir,
            cuda=cuda,
        )
        dimension = int(description["dim"])
        provider_configuration = json.dumps(
            {"cuda": bool(cuda), "runtime": "onnxruntime"},
            sort_keys=True,
            separators=(",", ":"),
        )
        self._space = EmbeddingSpaceSpec(
            provider_key=self.provider_key,
            provider_version=metadata.version("fastembed"),
            model=model,
            model_revision=str(description.get("sources", {}).get("hf") or "fastembed-registry"),
            dimension=dimension,
            native_dimension=dimension,
            preprocessing_key=PREPROCESSING_KEY,
            preprocessing_version=PREPROCESSING_VERSION,
            query_instruction=query_instruction,
            document_instruction=document_instruction,
            normalize_embeddings=True,
            max_sequence_length=None,
            overflow_policy="reject",
            output_dtype="float32",
            provider_configuration=provider_configuration,
        )

    @property
    def space(self) -> EmbeddingSpaceSpec:
        return self._space

    @property
    def revision(self) -> str:
        return self.space.model_revision

    @property
    def configuration(self) -> str:
        return self.space.provider_configuration

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        values = [
            f"{self.document_instruction}{text}" if self.document_instruction else text
            for text in texts
        ]
        return _normalize_rows(self._encoder.embed(values, batch_size=self.batch_size))

    def embed_queries(self, texts: list[str]) -> list[list[float]]:
        values = [_qwen_query(self.query_instruction, text) for text in texts]
        return _normalize_rows(self._encoder.embed(values, batch_size=self.batch_size))

    def embed(self, texts: list[str], *, query: bool = False) -> list[list[float]]:
        return self.embed_queries(texts) if query else self.embed_documents(texts)


def default_sentence_transformer_provider(
    *, cache_folder: str | None = None, local_files_only: bool = False
) -> SentenceTransformerEmbeddingProvider:
    """Build the I-02 frozen common SGOKB embedding profile."""

    return SentenceTransformerEmbeddingProvider(
        DEFAULT_EMBEDDING_MODEL,
        revision=DEFAULT_EMBEDDING_REVISION,
        query_instruction=DEFAULT_RETRIEVAL_INSTRUCTION,
        normalize_embeddings=True,
        truncate_dim=None,
        dtype="bfloat16",
        cache_folder=cache_folder,
        local_files_only=local_files_only,
        max_sequence_length=DEFAULT_EMBEDDING_MAX_SEQUENCE_LENGTH,
        overflow_policy="reject",
    )


def exact_cosine_scores(query: list[float], documents: list[list[float]]) -> list[float]:
    """Small-scale Float32 Exact baseline; I-03 may replace only the index backend."""
    validate_vectors([query], 1)
    validate_vectors(documents, len(documents))
    if documents and len(query) != len(documents[0]):
        raise ValueError("Query and document embedding dimensions differ")
    query_length = math.sqrt(sum(value * value for value in query))
    output = []
    for document in documents:
        doc_length = math.sqrt(sum(value * value for value in document))
        output.append(
            sum(left * right for left, right in zip(query, document)) / (query_length * doc_length)
        )
    return output
