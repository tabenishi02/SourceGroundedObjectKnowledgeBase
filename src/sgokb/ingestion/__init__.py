"""Canonical ingestion package for capture import, extraction, and page context."""

from .context import FIELDS, OFFICIAL_HOSTS, VERSION, analyze, effective_context, structured_nodes
from .extraction import (
    ATOMIC,
    CONTAINERS,
    NOISE,
    NORMALIZATION_VERSION,
    ExtractorRegistry,
    GenericExtractor,
    PixivExtractor,
    WikipediaExtractor,
    chunks,
    positions,
    text,
)
from .importer import WebCaptureImporter, classify

__all__ = [
    "ATOMIC",
    "CONTAINERS",
    "FIELDS",
    "NOISE",
    "NORMALIZATION_VERSION",
    "OFFICIAL_HOSTS",
    "VERSION",
    "ExtractorRegistry",
    "GenericExtractor",
    "PixivExtractor",
    "WebCaptureImporter",
    "WikipediaExtractor",
    "analyze",
    "chunks",
    "classify",
    "effective_context",
    "positions",
    "structured_nodes",
    "text",
]
