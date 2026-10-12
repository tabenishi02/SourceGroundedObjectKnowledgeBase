"""Compatibility import surface for canonical ingestion extraction."""

from .ingestion.extraction import (
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

__all__ = [
    "ATOMIC",
    "CONTAINERS",
    "NOISE",
    "NORMALIZATION_VERSION",
    "ExtractorRegistry",
    "GenericExtractor",
    "PixivExtractor",
    "WikipediaExtractor",
    "chunks",
    "positions",
    "text",
]
