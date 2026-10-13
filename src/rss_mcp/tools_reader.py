"""Portmanteau reader_ops: inbox/starred/search_text/search_semantic/stats/trigger_sweep/sweep_status."""

from __future__ import annotations

from typing import Annotated, Any, Literal

from fastmcp import FastMCP
from pydantic import Field

from rss_mcp import aiwatcher_bridge, db, discovery, faves, search

ReaderOp = Literal[
    "inbox",
    "starred",
    "search_text",
    "search_semantic",
    "stats",
    "rag_stats",
    "trigger_sweep",
    "sweep_status",
    "list_collections",
    "create_collection",
    "delete_collection",
    "add_to_collection",
    "remove_from_collection",
    "set_item_note",
    "get_item_note",
    "export_starred",
    "discover_feeds",
    "recommended_feeds",
    "aiwatcher_bundles",
    "aiwatcher_import_bundle",
    "aiwatcher_promote",
]

RATIONALE = "One reader_ops tool is the daily reading surface: inbox, stars, collections, notes, discovery, AIWatcher bridge, search, stats, background sweeps."


def _stats_payload() -> dict[str, Any]:
    db.init_db()
    con = db.connect()
    try:
        feeds = con.execute("SELECT COUNT(*) c FROM feeds").fetchone()["c"]
        items = con.execute("SELECT COUNT(*) c FROM items").fetchone()["c"]
        unread = con.execute("SELECT COUNT(*) c FROM items WHERE is_read=0").fetchone()["c"]
        stars = con.execute("SELECT COUNT(*) c FROM items WHERE is_starred=1").fetchone()["c"]
        extracts = con.execute("SELECT COUNT(*) c FROM extracts").fetchone()["c"]
        collections = con.execute("SELECT COUNT(*) c FROM collections").fetchone()["c"]
        return {
            "feeds": feeds,
            "items": items,
            "unread": unread,
            "starred": stars,
            "extracts": extracts,
            "collections": collections,
        }
    finally:
        con.close()


async def reader_ops(
    operation: Annotated[ReaderOp, Field(description="Reader operation to run")],
    query: str = "",
    limit: int = 25,
    offset: int = 0,
    job_id: str = "",
    mode: Annotated[str, Field(description="Sweep mode: incremental or full. Used by: trigger_sweep")] = "incremental",
    hours: Annotated[int, Field(description="Lookback hours for incremental sweep. Used by: trigger_sweep")] = 4,
    feed_id: Annotated[int, Field(description="Scope sweep to one feed id, 0 means all. Used by: trigger_sweep")] = 0,
    item_id: int = 0,
    collection_id: int = 0,
    collection_name: str = "",
    collection_description: str = "",
    collection_color: str = "#3b82f6",
    note: str = "",
    export_format: str = "markdown",
    url: str = "",
    bundle_id: str = "",
    ctx: Any = None,
) -> dict[str, Any]:
    """reader_ops - Daily reading surface: inbox, stars, search, stats, RAG sweeps.

    RATIONALE: single entry point for what a human checks every morning.

    ## Return Format
    {success, message, items/stats/job/job_id/status/chunks}

    ## Examples
    - {"operation": "inbox"} unread items
    - {"operation": "search_text", "query": "vienna"} FTS search
    - {"operation": "search_semantic", "query": "rocket engine"} vector search
    - {"operation": "trigger_sweep", "mode": "incremental", "hours": 4} background index job
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
        items = faves.list_starred_items(
            collection_id=collection_id if collection_id > 0 else None,
            limit=limit,
            offset=offset,
        )
        return {"success": True, "message": f"{len(items)} starred", "items": items}
    if operation == "list_collections":
        colls = faves.list_collections()
        return {"success": True, "message": f"{len(colls)} collections", "collections": colls}
    if operation == "create_collection":
        return faves.create_collection(collection_name, collection_description, collection_color)
    if operation == "delete_collection":
        return faves.delete_collection(collection_id)
    if operation == "add_to_collection":
        return faves.add_item_to_collection(item_id, collection_id)
    if operation == "remove_from_collection":
        return faves.remove_item_from_collection(item_id, collection_id)
    if operation == "set_item_note":
        return faves.set_item_note(item_id, note)
    if operation == "get_item_note":
        return {"success": True, "item_id": item_id, "note": faves.get_item_note(item_id)}
    if operation == "export_starred":
        text = faves.export_starred(
            fmt=export_format,
            collection_id=collection_id if collection_id > 0 else None,
        )
        return {"success": True, "format": export_format, "content": text}
    if operation == "discover_feeds":
        return discovery.discover_feeds_from_url(url)
    if operation == "recommended_feeds":
        return {"success": True, "categories": discovery.get_recommended_catalog()}
    if operation == "aiwatcher_bundles":
        bundles = aiwatcher_bridge.get_aiwatcher_bundles()
        return {"success": True, "bundles": bundles, "count": len(bundles)}
    if operation == "aiwatcher_import_bundle":
        return aiwatcher_bridge.import_bundle_feeds(bundle_id)
    if operation == "aiwatcher_promote":
        return aiwatcher_bridge.promote_item_to_aiwatcher(item_id)
    if operation == "search_text":
        return search.search_text(query, limit=limit)
    if operation == "search_semantic":
        return search.search_semantic(query, limit=limit)
    if operation == "stats":
        return {"success": True, "message": "Reader stats", "stats": _stats_payload()}
    if operation == "rag_stats":
        return search.rag_stats()
    if operation == "trigger_sweep":
        r = search.trigger_sweep(mode=mode, hours=hours, feed_id=feed_id)
        if ctx is not None:
            import contextlib

            with contextlib.suppress(Exception):
                await ctx.report_progress(0, 1)
        return r
    if operation == "sweep_status":
        return search.sweep_status(job_id)
    return {"success": False, "message": f"Unknown operation {operation}"}


def stats_payload() -> dict[str, Any]:
    return _stats_payload()


def register(mcp: FastMCP) -> None:
    mcp.tool(annotations={"mutating": True})(reader_ops)
