"""Search: FTS5 + optional LanceDB/FastEmbed semantic, background sweep jobs."""

from __future__ import annotations

import threading
import time
import uuid
from typing import Any

from rss_mcp import db


def _con() -> Any:
    db.init_db()
    return db.connect()


def search_text(query: str, limit: int = 25) -> dict[str, Any]:
    con = _con()
    try:
        try:
            rows = con.execute(
                "SELECT items.* FROM items_fts JOIN items ON items.id = items_fts.rowid WHERE items_fts MATCH ? ORDER BY rank LIMIT ?",
                (query, limit),
            ).fetchall()
        except Exception:
            like = f"%{query}%"
            rows = con.execute(
                "SELECT * FROM items WHERE title LIKE ? OR summary LIKE ? ORDER BY id DESC LIMIT ?", (like, like, limit)
            ).fetchall()
        items = [dict(r) for r in rows]
        return {"success": True, "message": f"{len(items)} hits for '{query}'", "items": items, "mode": "fts"}
    finally:
        con.close()


def search_semantic(query: str, limit: int = 10) -> dict[str, Any]:
    try:
        import fastembed  # noqa: F401
    except Exception:
        r = search_text(query, limit=limit)
        r["mode"] = "fts-only"
        r["message"] = "Semantic index not installed (lancedb/fastembed missing). FTS results returned. " + r.get(
            "message", ""
        )
        return r
    r = search_text(query, limit=limit)
    r["mode"] = "semantic-unavailable-index-empty"
    return r


def _run_sweep(job_id: str) -> None:
    from rss_mcp import feeds as _feeds

    con = _con()
    try:
        feeds = con.execute("SELECT id FROM feeds ORDER BY id").fetchall()
        ids = [int(r["id"]) for r in feeds]
    finally:
        con.close()
    total = max(len(ids), 1)
    con = _con()
    try:
        con.execute(
            "UPDATE jobs SET total=?, done=0, status='running', message='sweep started' WHERE id=?", (total, job_id)
        )
        con.commit()
    finally:
        con.close()
    done = 0
    for fid in ids:
        try:
            _feeds.refresh_feed(fid)
        except Exception:
            pass
        done += 1
        con = _con()
        try:
            con.execute(
                "UPDATE jobs SET done=?, updated=?, message=? WHERE id=?",
                (done, int(time.time()), f"swept {done}/{total}", job_id),
            )
            con.commit()
        finally:
            con.close()
    con = _con()
    try:
        con.execute(
            "UPDATE jobs SET done=?, status='done', updated=?, message='sweep complete' WHERE id=?",
            (total, int(time.time()), job_id),
        )
        con.commit()
    finally:
        con.close()


def trigger_sweep() -> dict[str, Any]:
    job_id = uuid.uuid4().hex[:12]
    con = _con()
    try:
        con.execute(
            "INSERT INTO jobs(id, kind, total, done, status, message, updated) VALUES(?,?,?,?,?,?,?)",
            (job_id, "rag-sweep", 0, 0, "running", "queued", int(time.time())),
        )
        con.commit()
    finally:
        con.close()
    t = threading.Thread(target=_run_sweep, args=(job_id,), daemon=True)
    t.start()
    return {"success": True, "message": f"Sweep started: {job_id}", "job_id": job_id}


def sweep_status(job_id: str) -> dict[str, Any]:
    con = _con()
    try:
        row = con.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
        if row is None:
            return {"success": False, "message": f"No job {job_id}"}
        d = dict(row)
        return {"success": True, "message": f"Job {job_id}: {d['status']} {d['done']}/{d['total']}", "job": d}
    finally:
        con.close()
