"""Portmanteau feeds_ops: subscribe/unsubscribe/list/refresh/fetch/get/mark/star/remove/opml/health."""

from __future__ import annotations

from typing import Annotated, Any, Literal

from fastmcp import FastMCP
from pydantic import Field

from rss_mcp import db, feeds

FeedsOp = Literal[
    "subscribe",
    "unsubscribe",
    "list_feeds",
    "refresh_feed",
    "refresh_all",
    "fetch_items",
    "get_item",
    "mark_read",
    "mark_star",
    "remove_item",
    "opml_import",
    "opml_export",
    "feed_health",
]

RATIONALE = (
    "One feeds_ops tool groups the full subscription lifecycle so agents learn one "
    "entry point instead of thirteen. glance-mcp is a lightweight holdall with a "
    "single-shot fetch; rss-mcp is a stateful reader with subscriptions, polling, "
    "read/star state, OPML, and health. No overlap in purpose."
)


def _items(feed_id: int | None, unread_only: bool, limit: int) -> list[dict[str, Any]]:
    db.init_db()
    con = db.connect()
    try:
        if feed_id is None:
            q = "SELECT * FROM items ORDER BY published DESC, id DESC LIMIT ?"
            rows = con.execute(q, (limit,)).fetchall()
        elif unread_only:
            rows = con.execute(
                "SELECT * FROM items WHERE feed_id=? AND is_read=0 ORDER BY published DESC, id DESC LIMIT ?",
                (feed_id, limit),
            ).fetchall()
        else:
            rows = con.execute(
                "SELECT * FROM items WHERE feed_id=? ORDER BY published DESC, id DESC LIMIT ?", (feed_id, limit)
            ).fetchall()
        return [dict(r) for r in rows]
    finally:
        con.close()


async def feeds_ops(
    operation: Annotated[FeedsOp, Field(description="Feed operation to run")],
    url: str = "",
    title: str = "",
    feed_id: int = 0,
    item_id: int = 0,
    limit: int = 25,
    unread_only: bool = False,
    is_read: bool = True,
    is_starred: bool = True,
    opml_text: str = "",
) -> dict[str, Any]:
    """feeds_ops - Full feed subscription lifecycle.

    RATIONALE: groups subscribe/unsubscribe/list/refresh/fetch/get/mark/star/remove/opml/health
    into one discoverable tool. Stateful reader, unlike glance-mcp single-shot fetch.

    ## Return Format
    Dictionary with `success` (bool), `message` (str), and operation-specific payload (e.g. `feeds`, `items`, `feed`, `opml`).

    ## Examples
    - {"operation": "list_feeds"} -> lists all subscribed feeds.
    - {"operation": "subscribe", "url": "https://news.ycombinator.com/rss"} -> subscribes to RSS feed.
    - {"operation": "refresh_all"} -> polls all feeds for new articles.
    - {"operation": "fetch_items", "limit": 20, "unread_only": true} -> retrieves unread articles.
    """
    if operation == "subscribe":
        if not url:
            return {"success": False, "message": "url is required"}
        return feeds.subscribe(url, title)
    if operation == "unsubscribe":
        return feeds.unsubscribe(feed_id)
    if operation == "list_feeds":
        return feeds.list_feeds()
    if operation == "refresh_feed":
        return feeds.refresh_feed(feed_id)
    if operation == "refresh_all":
        return feeds.refresh_all()
    if operation == "fetch_items":
        items = _items(feed_id or None, unread_only, limit)
        return {"success": True, "message": f"{len(items)} items", "items": items}
    if operation == "get_item":
        db.init_db()
        con = db.connect()
        try:
            row = con.execute("SELECT * FROM items WHERE id=?", (item_id,)).fetchone()
            if row is None:
                return {"success": False, "message": f"No item {item_id}"}
            return {"success": True, "message": f"Item {item_id}", "item": dict(row)}
        finally:
            con.close()
    if operation == "mark_read":
        db.init_db()
        con = db.connect()
        try:
            con.execute("UPDATE items SET is_read=? WHERE id=?", (1 if is_read else 0, item_id))
            con.commit()
            return {"success": True, "message": f"Item {item_id} read={is_read}"}
        finally:
            con.close()
    if operation == "mark_star":
        db.init_db()
        con = db.connect()
        try:
            con.execute("UPDATE items SET is_starred=? WHERE id=?", (1 if is_starred else 0, item_id))
            con.commit()
            return {"success": True, "message": f"Item {item_id} starred={is_starred}"}
        finally:
            con.close()
    if operation == "remove_item":
        db.init_db()
        con = db.connect()
        try:
            con.execute("DELETE FROM items WHERE id=?", (item_id,))
            con.commit()
            return {"success": True, "message": f"Removed item {item_id}"}
        finally:
            con.close()
    if operation == "opml_import":
        if not opml_text:
            return {"success": False, "message": "opml_text is required"}
        return feeds.opml_import(opml_text)
    if operation == "opml_export":
        return feeds.opml_export()
    if operation == "feed_health":
        return feeds.feed_health(feed_id)
    return {"success": False, "message": f"Unknown operation {operation}"}


def register(mcp: FastMCP) -> None:
    mcp.tool(annotations={"mutating": True})(feeds_ops)
