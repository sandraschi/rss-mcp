"""Feed fetching: feedparser + httpx size-capped 2MB, conditional GET, OPML, health."""

from __future__ import annotations

import time
import xml.etree.ElementTree as ET
from typing import Any

import feedparser
import httpx
from defusedxml import ElementTree as DET

from rss_mcp import db

MAX_BYTES = 2 * 1024 * 1024


def _con() -> Any:
    db.init_db()
    return db.connect()


def subscribe(url: str, title: str = "") -> dict[str, Any]:
    con = _con()
    try:
        con.execute("INSERT OR IGNORE INTO feeds(url, title) VALUES(?, ?)", (url, title))
        con.commit()
        row = con.execute("SELECT * FROM feeds WHERE url=?", (url,)).fetchone()
        return {"success": True, "message": f"Subscribed {url}", "feed": dict(row)}
    finally:
        con.close()


def unsubscribe(feed_id: int) -> dict[str, Any]:
    con = _con()
    try:
        cur = con.execute("DELETE FROM feeds WHERE id=?", (feed_id,))
        con.execute("DELETE FROM items WHERE feed_id=?", (feed_id,))
        con.commit()
        if cur.rowcount == 0:
            return {"success": False, "message": f"No feed {feed_id}"}
        return {"success": True, "message": f"Unsubscribed feed {feed_id}"}
    finally:
        con.close()


def list_feeds() -> dict[str, Any]:
    con = _con()
    try:
        rows = con.execute("SELECT * FROM feeds ORDER BY id").fetchall()
        feeds = [dict(r) for r in rows]
        out = []
        for f in feeds:
            n = con.execute("SELECT COUNT(*) c FROM items WHERE feed_id=?", (f["id"],)).fetchone()["c"]
            u = con.execute("SELECT COUNT(*) c FROM items WHERE feed_id=? AND is_read=0", (f["id"],)).fetchone()["c"]
            f["item_count"] = n
            f["unread_count"] = u
            out.append(f)
        return {"success": True, "message": f"{len(out)} feeds", "feeds": out}
    finally:
        con.close()


def _fetch_bytes(url: str, etag: str, last_mod: str) -> tuple[bytes, dict[str, Any]]:
    headers = {"User-Agent": "rss-mcp/0.1.0"}
    if etag:
        headers["If-None-Match"] = etag
    if last_mod:
        headers["If-Modified-Since"] = last_mod
    with httpx.Client(timeout=15.0, follow_redirects=True) as client:
        resp = client.get(url, headers=headers)
        meta = {
            "status": resp.status_code,
            "etag": resp.headers.get("etag", ""),
            "last_modified": resp.headers.get("last-modified", ""),
        }
        if resp.status_code == 304:
            return b"", meta
        resp.raise_for_status()
        data = resp.content[:MAX_BYTES]
        return data, meta


def refresh_feed(feed_id: int) -> dict[str, Any]:
    con = _con()
    try:
        feed = con.execute("SELECT * FROM feeds WHERE id=?", (feed_id,)).fetchone()
        if feed is None:
            return {"success": False, "message": f"No feed {feed_id}", "added": 0}
        url = feed["url"]
        try:
            data, meta = _fetch_bytes(url, feed["etag"] or "", feed["last_modified"] or "")
        except Exception as e:
            con.execute(
                "UPDATE feeds SET last_checked=?, last_status=0, error=? WHERE id=?",
                (int(time.time()), str(e)[:500], feed_id),
            )
            con.commit()
            return {"success": False, "message": f"Fetch failed: {e}", "added": 0}
        if meta["status"] == 304:
            con.execute("UPDATE feeds SET last_checked=? WHERE id=?", (int(time.time()), feed_id))
            con.commit()
            return {"success": True, "message": "Not modified (304)", "added": 0}
        parsed = feedparser.parse(data)
        title = (parsed.feed.get("title", "") or feed["title"] or "")[:300]
        added = 0
        for e in parsed.entries[:200]:
            guid = (e.get("id") or e.get("link") or e.get("title") or "")[:500]
            if not guid:
                continue
            etitle = (e.get("title", "") or "")[:500]
            link = (e.get("link", "") or "")[:1000]
            summary = (e.get("summary", "") or e.get("description", "") or "")[:4000]
            pub = 0
            try:
                if e.get("published_parsed"):
                    pub = int(time.mktime(e.published_parsed))
            except Exception:
                pub = 0
            cur = con.execute(
                "INSERT OR IGNORE INTO items(feed_id, guid, title, link, published, summary) VALUES(?,?,?,?,?,?)",
                (feed_id, guid, etitle, link, pub, summary),
            )
            if cur.rowcount:
                added += 1
                rowid = cur.lastrowid
                try:
                    con.execute("INSERT INTO items_fts(rowid, title, summary) VALUES(?,?,?)", (rowid, etitle, summary))
                except Exception:
                    pass
        con.execute(
            "UPDATE feeds SET title=?, etag=?, last_modified=?, last_checked=?, last_status=?, error=? WHERE id=?",
            (
                title,
                meta.get("etag", ""),
                meta.get("last_modified", ""),
                int(time.time()),
                meta.get("status", 200),
                "",
                feed_id,
            ),
        )
        con.commit()
        return {"success": True, "message": f"Refreshed feed {feed_id}: +{added} items", "added": added}
    finally:
        con.close()


def refresh_all() -> dict[str, Any]:
    feeds = list_feeds().get("feeds", [])
    total = 0
    errors = 0
    for f in feeds:
        r = refresh_feed(int(f["id"]))
        total += int(r.get("added", 0))
        if not r.get("success"):
            errors += 1
    return {
        "success": True,
        "message": f"Refreshed {len(feeds)} feeds, +{total} items, {errors} errors",
        "added": total,
        "feeds": len(feeds),
    }


def opml_export() -> dict[str, Any]:
    feeds = list_feeds().get("feeds", [])
    root = ET.Element("opml", version="2.0")
    head = ET.SubElement(root, "head")
    t = ET.SubElement(head, "title")
    t.text = "rss-mcp subscriptions"
    body = ET.SubElement(root, "body")
    for f in feeds:
        ET.SubElement(
            body,
            "outline",
            {
                "type": "rss",
                "text": f.get("title") or f["url"],
                "title": f.get("title") or f["url"],
                "xmlUrl": f["url"],
            },
        )
    xml = ET.tostring(root, encoding="unicode")
    return {"success": True, "message": f"Exported {len(feeds)} feeds", "opml": xml}


def opml_import(opml_text: str) -> dict[str, Any]:
    try:
        root = DET.fromstring(opml_text.encode("utf-8")[:MAX_BYTES])
    except Exception as e:
        return {"success": False, "message": f"OPML parse failed: {e}", "added": 0}
    urls: list[tuple[str, str]] = []
    for node in root.iter("outline"):
        u = node.get("xmlUrl") or node.get("xmlurl") or ""
        if u:
            urls.append((u, node.get("title") or node.get("text") or ""))
    added = 0
    for u, t in urls:
        r = subscribe(u, t)
        if r.get("success"):
            added += 1
    return {"success": True, "message": f"Imported {added}/{len(urls)} feeds", "added": added}


def feed_health(feed_id: int) -> dict[str, Any]:
    con = _con()
    try:
        feed = con.execute("SELECT * FROM feeds WHERE id=?", (feed_id,)).fetchone()
        if feed is None:
            return {"success": False, "message": f"No feed {feed_id}", "healthy": False}
        healthy = bool(feed["last_status"] and 200 <= int(feed["last_status"]) < 400)
        return {
            "success": True,
            "message": "healthy" if healthy else "unhealthy",
            "healthy": healthy,
            "feed": dict(feed),
        }
    finally:
        con.close()
