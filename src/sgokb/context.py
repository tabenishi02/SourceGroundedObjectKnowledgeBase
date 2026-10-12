"""Compatibility import surface for canonical ingestion page context helpers."""

from .ingestion.context import (
    FIELDS,
    OFFICIAL_HOSTS,
    VERSION,
    analyze,
    effective_context,
    structured_nodes,
)

__all__ = [
    "FIELDS",
    "OFFICIAL_HOSTS",
    "VERSION",
    "analyze",
    "effective_context",
    "structured_nodes",
]
