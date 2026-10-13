"""MCP transport adapter package.

Phase J/J-01 establishes only the dependency boundary. Public MCP Tool/Resource
schemas are defined by later Phase J tasks.
"""

from .adapter import MCPReadAdapter

__all__ = ["MCPReadAdapter"]
