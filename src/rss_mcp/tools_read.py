"""Portmanteau readability_ops: extract/get_cached/clear_cache/list_extractors."""

from __future__ import annotations

from typing import Annotated, Any, Literal

from fastmcp import FastMCP
from pydantic import Field

from rss_mcp import readability

ReadOp = Literal["extract", "get_cached", "clear_cache", "list_extractors"]

RATIONALE = "One readability_ops tool covers clean-text extraction end to end: download, extract, cache, inspect."


async def readability_ops(
    operation: Annotated[ReadOp, Field(description="Readability operation to run")],
    item_id: int = 0,
    force: bool = False,
) -> dict[str, Any]:
    """readability_ops - Clean article text without ad sites.

    RATIONALE: trafilatura primary plus readability-lxml fallback, cached in SQLite.
    No paywall bypass: if the page needs login, extraction reports failure honestly.

    Return Format: {success, message, title/author/text/html/extractor/cached}
    Examples: {operation: extract, item_id: 3} downloads and cleans; {operation: list_extractors} shows engines.
    """
    if operation == "extract":
        return readability.extract(item_id, force=force)
    if operation == "get_cached":
        return readability.get_cached(item_id)
    if operation == "clear_cache":
        return readability.clear_cache(item_id or None)
    if operation == "list_extractors":
        return readability.list_extractors()
    return {"success": False, "message": f"Unknown operation {operation}"}


def register(mcp: FastMCP) -> None:
    mcp.tool()(readability_ops)
