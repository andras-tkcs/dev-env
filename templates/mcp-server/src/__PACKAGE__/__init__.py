"""__DISPLAY_NAME__: an MCP server."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("__DIST_NAME__")
except PackageNotFoundError:  # pragma: no cover - only in a checkout that was never pip-installed
    __version__ = "0.0.0.dev0"
