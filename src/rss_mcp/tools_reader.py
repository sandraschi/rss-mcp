"""Portmanteau reader_ops: inbox/starred/search_text/search_semantic/stats/trigger_sweep/sweep_status."""

from __future__ import annotations

from typing import Annotated, Any, Literal

from fastmcp import FastMCP
from pydantic import Field

from rss_mcp import db, search

ReaderOp = Literal["inbox", "starred", "search_text", "search_semantic", "stats", "trigger_sweep", "sweep_status"]

RATIONALE = "One reader_ops tool is the daily reading surface: inbox, stars, search, stats, background sweeps."


def _stats_payload() -> dict[str, Any]:
    db.init_db()
    con = db.connect()
    try:
        feeds = con.execute("SELECT COUNT(*) c FROM feeds").fetchone()["c"]
        items = con.execute("SELECT COUNT(*) c FROM items").fetchone()["c"]
        unread = con.execute("SELECT COUNT(*) c FROM items WHERE is_read=0").fetchone()["c"]
        stars = con.execute("SELECT COUNT(*) c FROM items WHERE is_starred=1").fetchone()["c"]
        extracts = con.execute("SELECT COUNT(*) c FROM extracts").fetchone()["c"]
        return {"feeds": feeds, "items": items, "unread": unread, "starred": stars, "extracts": extracts}
    finally:
        con.close()


async def reader_ops(
    operation: Annotated[ReaderOp, Field(description="Reader operation to run")],
    query: str = "",
    limit: int = 25,
    job_id: str = "",
) -> dict[str, Any]:
    """reader_ops - Daily reading surface: inbox, stars, search, stats, sweeps.

    RATIONALE: single entry point for what a human checks every morning.

    Return Format: {success, message, items/stats/job/job_id}
    Examples: {operation: inbox} unread items; {operation: search_text, query: vienna} FTS; {operation: stats} counts.
    """
    db.init_db()
    if operation == "inbox":
        con = db.connect()
        try:
            rows = con.execute(
                "SELECT * FROM items WHERE is_read=0 ORDER BY published DESC, id DESC LIMIT ?", (limit,)
            ).fetchall()
            items = [dict(r) for r in rows]
            return {"success": True, "message": f"{len(items)} unread", "items": items}
        finally:
            con.close()
    if operation == "starred":
        con = db.connect()
        try:
            rows = con.execute(
                "SELECT * FROM items WHERE is_starred=1 ORDER BY published DESC, id DESC LIMIT ?", (limit,)
            ).fetchall()
            items = [dict(r) for r in rows]
            return {"success": True, "message": f"{len(items)} starred", "items": items}
        finally:
            con.close()
    if operation == "search_text":
        return search.search_text(query, limit=limit)
    if operation == "search_semantic":
        return search.search_semantic(query, limit=limit)
    if operation == "stats":
        return {"success": True, "message": "Reader stats", "stats": _stats_payload()}
    if operation == "trigger_sweep":
        return search.trigger_sweep()
    if operation == "sweep_status":
        return search.sweep_status(job_id)
    return {"success": False, "message": f"Unknown operation {operation}"}


def stats_payload() -> dict[str, Any]:
    return _stats_payload()


def register(mcp: FastMCP) -> None:
    mcp.tool()(reader_ops)
