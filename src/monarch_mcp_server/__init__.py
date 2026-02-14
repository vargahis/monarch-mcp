"""Monarch Money MCP Server."""

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("monarch-mcp-server")
except PackageNotFoundError:
    __version__ = "0.0.0"
