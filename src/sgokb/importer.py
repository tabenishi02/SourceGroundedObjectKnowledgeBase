"""Compatibility import surface for the canonical ingestion importer."""

from .ingestion.importer import WebCaptureImporter, classify

__all__ = ["WebCaptureImporter", "classify"]
