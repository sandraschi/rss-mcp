"""Readability: trafilatura primary + BeautifulSoup/readability-lxml fallback, DB cache."""

from __future__ import annotations

import time
from typing import Any

import httpx
import trafilatura
from bs4 import BeautifulSoup
from readability import Document

from rss_mcp import db

MAX_BYTES = 2 * 1024 * 1024


def _con() -> Any:
    db.init_db()
    return db.connect()


def _download(url: str) -> tuple[str, str]:
    with httpx.Client(timeout=20.0, follow_redirects=True, headers={"User-Agent": "rss-mcp/0.1.0"}) as c:
        r = c.get(url)
        r.raise_for_status()
        raw = r.content[:MAX_BYTES]
        text = raw.decode("utf-8", errors="replace")
        return text, r.headers.get("content-type", "")


def _extract_with_trafilatura(html: str, url: str) -> dict[str, Any] | None:
    try:
        downloaded = trafilatura.extract(html, include_comments=False, include_tables=True, output_format="json")
        if not downloaded:
            return None
        import json as _json

        data = _json.loads(downloaded)
        text = (data.get("text") or "").strip()
        if len(text) < 200:
            return None
        return {
            "title": data.get("title", ""),
            "author": data.get("author", ""),
            "text": text,
            "html": html[:20000],
            "extractor": "trafilatura",
        }
    except Exception:
        return None


def _extract_fallback(html: str) -> dict[str, Any]:
    try:
        doc = Document(html)
        title = doc.short_title() or ""
        clean_html = doc.summary()
        soup = BeautifulSoup(clean_html, "html.parser")
        text = soup.get_text(separator="\n").strip()
        return {
            "title": title,
            "author": "",
            "text": text[:50000],
            "html": clean_html[:20000],
            "extractor": "readability-lxml",
        }
    except Exception:
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "aside"]):
            tag.decompose()
        text = soup.get_text(separator="\n").strip()
        title = (soup.title.string if soup.title and soup.title.string else "").strip()
        return {
            "title": title,
            "author": "",
            "text": text[:50000],
            "html": str(soup)[:20000],
            "extractor": "beautifulsoup",
        }


def extract(item_id: int, force: bool = False) -> dict[str, Any]:
    con = _con()
    try:
        item = con.execute("SELECT * FROM items WHERE id=?", (item_id,)).fetchone()
        if item is None:
            return {"success": False, "message": f"No item {item_id}"}
        if not force:
            cached = con.execute("SELECT * FROM extracts WHERE item_id=?", (item_id,)).fetchone()
            if cached:
                d = dict(cached)
                return {"success": True, "message": "Cache hit", "cached": True, **d}
        url = item["link"]
        if not url:
            return {"success": False, "message": "Item has no link"}
        try:
            html, _ct = _download(url)
        except Exception as e:
            return {"success": False, "message": f"Download failed: {e}"}
        got = _extract_with_trafilatura(html, url) or _extract_fallback(html)
        if not (got.get("text") or "").strip():
            return {"success": False, "message": "No readable text found (paywall or empty page?)"}
        con.execute(
            "INSERT OR REPLACE INTO extracts(item_id, title, author, text, html, extractor, created) VALUES(?,?,?,?,?,?,?)",
            (
                item_id,
                got["title"][:500],
                got["author"][:300],
                got["text"],
                got["html"],
                got["extractor"],
                int(time.time()),
            ),
        )
        con.commit()
        return {
            "success": True,
            "message": f"Extracted via {got['extractor']}",
            "cached": False,
            "item_id": item_id,
            **got,
        }
    finally:
        con.close()


def get_cached(item_id: int) -> dict[str, Any]:
    con = _con()
    try:
        row = con.execute("SELECT * FROM extracts WHERE item_id=?", (item_id,)).fetchone()
        if row is None:
            return {"success": False, "message": "No cached extract"}
        d = dict(row)
        return {"success": True, "message": "Cache hit", **d}
    finally:
        con.close()


def clear_cache(item_id: int | None = None) -> dict[str, Any]:
    con = _con()
    try:
        if item_id is None:
            cur = con.execute("DELETE FROM extracts")
        else:
            cur = con.execute("DELETE FROM extracts WHERE item_id=?", (item_id,))
        con.commit()
        return {"success": True, "message": f"Cleared {cur.rowcount} cached extracts", "cleared": cur.rowcount}
    finally:
        con.close()


def list_extractors() -> dict[str, Any]:
    return {
        "success": True,
        "message": "2 extractors available",
        "extractors": [
            {"name": "trafilatura", "role": "primary", "notes": "Best for news/blogs, strips ads and chrome."},
            {
                "name": "readability-lxml",
                "role": "fallback",
                "notes": "Mozilla Readability port plus BeautifulSoup cleanup. No paywall bypass.",
            },
        ],
    }
