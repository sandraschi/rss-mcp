"""Faves & Collections system: collection CRUD, item notes, tags, and export."""

from __future__ import annotations

import json
from typing import Any

from rss_mcp.db import connect, now


def list_collections() -> list[dict[str, Any]]:
    con = connect()
    try:
        cur = con.execute("""
            SELECT c.id, c.name, c.description, c.color, c.created_at,
                   COUNT(ic.item_id) AS item_count
            FROM collections c
            LEFT JOIN item_collections ic ON ic.collection_id = c.id
            GROUP BY c.id
            ORDER BY c.name COLLATE NOCASE ASC
        """)
        return [dict(r) for r in cur.fetchall()]
    finally:
        con.close()


def create_collection(name: str, description: str = "", color: str = "#3b82f6") -> dict[str, Any]:
    name = name.strip()
    if not name:
        return {"success": False, "message": "Collection name cannot be empty"}
    con = connect()
    try:
        cur = con.execute(
            "INSERT INTO collections (name, description, color, created_at) VALUES (?, ?, ?, ?)",
            (name, description, color, now()),
        )
        con.commit()
        coll_id = cur.lastrowid
        return {
            "success": True,
            "collection": {
                "id": coll_id,
                "name": name,
                "description": description,
                "color": color,
                "item_count": 0,
            },
        }
    except Exception as exc:
        return {"success": False, "message": f"Failed to create collection: {exc}"}
    finally:
        con.close()


def delete_collection(collection_id: int) -> dict[str, Any]:
    con = connect()
    try:
        con.execute("DELETE FROM collections WHERE id = ?", (collection_id,))
        con.commit()
        return {"success": True, "collection_id": collection_id}
    finally:
        con.close()


def add_item_to_collection(item_id: int, collection_id: int) -> dict[str, Any]:
    con = connect()
    try:
        con.execute(
            "INSERT OR IGNORE INTO item_collections (item_id, collection_id) VALUES (?, ?)",
            (item_id, collection_id),
        )
        con.commit()
        return {"success": True, "item_id": item_id, "collection_id": collection_id}
    finally:
        con.close()


def remove_item_from_collection(item_id: int, collection_id: int) -> dict[str, Any]:
    con = connect()
    try:
        con.execute(
            "DELETE FROM item_collections WHERE item_id = ? AND collection_id = ?",
            (item_id, collection_id),
        )
        con.commit()
        return {"success": True, "item_id": item_id, "collection_id": collection_id}
    finally:
        con.close()


def set_item_note(item_id: int, note: str) -> dict[str, Any]:
    con = connect()
    try:
        con.execute(
            """
            INSERT INTO item_notes (item_id, note, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(item_id) DO UPDATE SET note = excluded.note, updated_at = excluded.updated_at
            """,
            (item_id, note, now()),
        )
        con.commit()
        return {"success": True, "item_id": item_id, "note": note}
    finally:
        con.close()


def get_item_note(item_id: int) -> str:
    con = connect()
    try:
        cur = con.execute("SELECT note FROM item_notes WHERE item_id = ?", (item_id,))
        row = cur.fetchone()
        return row["note"] if row else ""
    finally:
        con.close()


def list_starred_items(
    collection_id: int | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[dict[str, Any]]:
    con = connect()
    try:
        if collection_id is not None:
            cur = con.execute(
                """
                SELECT i.id, i.feed_id, i.guid, i.title, i.link, i.published, i.summary,
                       i.is_read, i.is_starred, f.title AS feed_title, n.note
                FROM items i
                JOIN feeds f ON f.id = i.feed_id
                JOIN item_collections ic ON ic.collection_id = ? AND ic.item_id = i.id
                LEFT JOIN item_notes n ON n.item_id = i.id
                WHERE i.is_starred = 1
                ORDER BY i.published DESC, i.id DESC
                LIMIT ? OFFSET ?
                """,
                (collection_id, limit, offset),
            )
        else:
            cur = con.execute(
                """
                SELECT i.id, i.feed_id, i.guid, i.title, i.link, i.published, i.summary,
                       i.is_read, i.is_starred, f.title AS feed_title, n.note
                FROM items i
                JOIN feeds f ON f.id = i.feed_id
                LEFT JOIN item_notes n ON n.item_id = i.id
                WHERE i.is_starred = 1
                ORDER BY i.published DESC, i.id DESC
                LIMIT ? OFFSET ?
                """,
                (limit, offset),
            )
        rows = [dict(r) for r in cur.fetchall()]

        # Attach collections for each item
        for item in rows:
            c_cur = con.execute(
                """
                SELECT c.id, c.name, c.color
                FROM collections c
                JOIN item_collections ic ON ic.collection_id = c.id
                WHERE ic.item_id = ?
                ORDER BY c.name ASC
                """,
                (item["id"],),
            )
            item["collections"] = [dict(cr) for cr in c_cur.fetchall()]
        return rows
    finally:
        con.close()


def export_starred(fmt: str = "markdown", collection_id: int | None = None) -> str:
    items = list_starred_items(collection_id=collection_id, limit=5000, offset=0)
    if fmt == "json":
        return json.dumps(items, indent=2)

    # Markdown export
    lines = ["# Starred RSS Items", "", f"Total items: {len(items)}", ""]
    for it in items:
        feed_title = it.get("feed_title") or "Unknown Feed"
        lines.append(f"## [{it['title'] or 'Untitled'}]({it['link']})")
        lines.append(f"*Source*: **{feed_title}** | *Published*: {it['published']}")
        if it.get("collections"):
            coll_names = ", ".join(f"`{c['name']}`" for c in it["collections"])
            lines.append(f"*Collections*: {coll_names}")
        if it.get("note"):
            lines.append(f"\n> **Note**: {it['note']}\n")
        if it.get("summary"):
            lines.append(f"\n{it['summary']}\n")
        lines.append("---\n")

    return "\n".join(lines)
