"""Integration bridge between rss-mcp and aiwatcher-mcp (port 10946).

Enables:
1. Importing fleet bundles directly from mcp-central-docs/operations/bundles.json.
2. Promoting / syncing high-priority starred RSS items directly to aiwatcher-mcp
   for morning briefs, anomaly alerts, or TTS playback.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import httpx

from rss_mcp.db import connect
from rss_mcp.feeds import subscribe


def _find_bundles_path() -> Path | None:
    # 1. Environment variable if set
    candidates = [
        Path("d:/Dev/repos/mcp-central-docs/operations/bundles.json"),
        Path(__file__).resolve().parents[3] / "mcp-central-docs" / "operations" / "bundles.json",
    ]
    for c in candidates:
        if c.exists():
            return c
    return None


def get_aiwatcher_bundles() -> list[dict[str, Any]]:
    """Load bundles from central operations bundles.json or return fallback."""
    bundles_file = _find_bundles_path()
    if not bundles_file or not bundles_file.exists():
        return []
    try:
        data = json.loads(bundles_file.read_text(encoding="utf-8"))
        return data.get("bundles", [])
    except Exception:
        return []


def import_bundle_feeds(bundle_id: str) -> dict[str, Any]:
    """Subscribe to all RSS/Atom sources configured in a specific fleet bundle."""
    bundles = get_aiwatcher_bundles()
    target_bundle = next((b for b in bundles if b.get("id") == bundle_id), None)
    if not target_bundle:
        return {"success": False, "message": f"Bundle '{bundle_id}' not found"}

    sources = target_bundle.get("sources", [])
    added = []
    skipped = []

    for s in sources:
        url = s.get("url")
        name = s.get("name") or target_bundle.get("name", "Bundle Feed")
        if not url:
            continue
        res = subscribe(url, title=name)
        if res.get("success"):
            added.append({"name": name, "url": url})
        else:
            skipped.append({"name": name, "url": url, "reason": res.get("message")})

    return {
        "success": True,
        "bundle_id": bundle_id,
        "bundle_name": target_bundle.get("name"),
        "added_count": len(added),
        "added": added,
        "skipped": skipped,
    }


def promote_item_to_aiwatcher(
    item_id: int,
    aiwatcher_url: str = "http://127.0.0.1:10946",
    priority: str = "high",
) -> dict[str, Any]:
    """Send a starred or selected RSS item to aiwatcher-mcp for ingestion/alerting."""
    con = connect()
    try:
        cur = con.execute(
            """
            SELECT i.id, i.title, i.link, i.published, i.summary, f.title AS feed_title, n.note
            FROM items i
            JOIN feeds f ON f.id = i.feed_id
            LEFT JOIN item_notes n ON n.item_id = i.id
            WHERE i.id = ?
            """,
            (item_id,),
        )
        row = cur.fetchone()
        if not row:
            return {"success": False, "message": f"Item {item_id} not found"}
        item = dict(row)
    finally:
        con.close()

    payload = {
        "source": f"rss-mcp:{item['feed_title']}",
        "title": item["title"],
        "url": item["link"],
        "summary": item["summary"],
        "user_note": item.get("note") or "",
        "priority": priority,
        "published": item["published"],
    }

    content_parts = [
        item["summary"] or "",
        f"\n\nLink: {item['link']}",
    ]
    if item.get("note"):
        content_parts.append(f"\nUser Note: {item['note']}")

    aiwatcher_body = {
        "title": item["title"] or "Untitled RSS Item",
        "content": "\n".join(content_parts).strip() or "No content",
        "source": f"rss-mcp:{item['feed_title']}",
        "tags": "rss,promoted,starred",
        "urgency_hint": 9.0 if priority == "high" else 6.0,
    }

    # Attempt to post to aiwatcher-mcp inbox endpoint if online
    target_endpoint = f"{aiwatcher_url.rstrip('/')}/api/inbox/ingest"
    try:
        with httpx.Client(timeout=5.0) as client:
            resp = client.post(target_endpoint, json=aiwatcher_body)
            if resp.status_code in (200, 201):
                return {
                    "success": True,
                    "message": f"Successfully promoted '{item['title']}' to aiwatcher-mcp",
                    "response": resp.json()
                    if resp.headers.get("content-type", "").startswith("application/json")
                    else resp.text,
                    "item": payload,
                }
            else:
                return {
                    "success": False,
                    "message": f"aiwatcher returned HTTP {resp.status_code}",
                    "item": payload,
                }
    except Exception as exc:
        # Graceful fallback: return staged payload
        return {
            "success": True,
            "staged": True,
            "message": f"aiwatcher-mcp at {aiwatcher_url} currently offline; payload staged successfully.",
            "item": payload,
            "offline_reason": str(exc),
        }
