"""Search: FTS5 + LanceDB/FastEmbed semantic, background sweep jobs.

RAG standard: sweeps run as background jobs returning job_id immediately.
Frontend polls status; MCP tools report progress via ctx.report_progress.
"""

from __future__ import annotations

import contextlib
import threading
import time
import uuid
from typing import Any

from rss_mcp import db
from rss_mcp.rag_store import MODEL_NAME, chunk_text, is_available

LAST_SWEEP: dict[str, Any] = {"at": None, "chunks": 0, "mode": None}


def _con() -> Any:
    db.init_db()
    return db.connect()


def search_text(query: str, limit: int = 25) -> dict[str, Any]:
    con = _con()
    try:
        try:
            rows = con.execute(
                "SELECT items.* FROM items_fts JOIN items ON items.id = items_fts.rowid"
                " WHERE items_fts MATCH ? ORDER BY rank LIMIT ?",
                (query, limit),
            ).fetchall()
        except Exception:
            like = f"%{query}%"
            rows = con.execute(
                "SELECT * FROM items WHERE title LIKE ? OR summary LIKE ? ORDER BY id DESC LIMIT ?",
                (like, like, limit),
            ).fetchall()
        items = [dict(r) for r in rows]
        return {"success": True, "message": f"{len(items)} hits for '{query}'", "items": items, "mode": "fts"}
    finally:
        con.close()


def search_semantic(query: str, limit: int = 10) -> dict[str, Any]:
    if not is_available():
        r = search_text(query, limit=limit)
        r["mode"] = "fts-only"
        r["message"] = "Semantic index not installed yet (lancedb/fastembed missing). FTS results. " + r.get(
            "message", ""
        )
        return r
    try:
        from rss_mcp.rag_store import RssVectorStore

        hits = RssVectorStore().search(query, limit=limit)
        return {"success": True, "message": f"{len(hits)} semantic hits", "items": hits, "mode": "semantic"}
    except Exception as e:
        r = search_text(query, limit=limit)
        r["mode"] = "semantic-error-fts-fallback"
        r["message"] = f"Semantic failed ({e}). FTS results. " + r.get("message", "")
        return r


def rag_stats() -> dict[str, Any]:
    total = 0
    if is_available():
        try:
            from rss_mcp.rag_store import RssVectorStore

            total = RssVectorStore().count()
        except Exception:
            total = 0
    con = _con()
    try:
        items = con.execute("SELECT COUNT(*) c FROM items").fetchone()["c"]
    finally:
        con.close()
    return {
        "success": True,
        "message": f"{total} vectors over {items} items",
        "total_vectors": total,
        "model": MODEL_NAME,
        "dims": 384,
        "engine": "fastembed+lancedb" if is_available() else "fts-only",
        "last_sweep": LAST_SWEEP,
        "items": items,
    }


def _sweep_items(mode: str, hours: int, feed_id: int) -> list[dict[str, Any]]:
    con = _con()
    try:
        q = "SELECT items.*, extracts.clean_text AS clean FROM items LEFT JOIN extracts ON extracts.item_id = items.id"
        clauses: list[str] = []
        args: list[Any] = []
        if feed_id:
            clauses.append("items.feed_id = ?")
            args.append(feed_id)
        if mode == "incremental":
            cutoff = int(time.time()) - max(hours, 1) * 3600
            clauses.append("(items.fetched_at >= ? OR items.published >= ?)")
            args.extend([cutoff, cutoff])
        if clauses:
            q += " WHERE " + " AND ".join(clauses)
        q += " ORDER BY items.id DESC LIMIT 2000"
        rows = con.execute(q, tuple(args)).fetchall()
        return [dict(r) for r in rows]
    finally:
        con.close()


def _run_sweep(job_id: str, mode: str, hours: int, feed_id: int) -> None:
    db.init_db()
    con = _con()
    try:
        con.execute("UPDATE jobs SET total=0, done=0, status='running', message='sweep started' WHERE id=?", (job_id,))
        con.commit()
    finally:
        con.close()
    try:
        items = _sweep_items(mode, hours, feed_id)
        chunks: list[dict[str, Any]] = []
        for it in items:
            body = (it.get("clean") or it.get("summary") or it.get("title") or "").strip()
            for i, ch in enumerate(chunk_text(body)):
                chunks.append(
                    {
                        "id": f"{it['id']}-{i}",
                        "text": ch,
                        "item_id": int(it["id"]),
                        "feed_id": int(it.get("feed_id") or 0),
                        "title": str(it.get("title") or ""),
                    }
                )
        if mode == "full" and is_available():
            with contextlib.suppress(Exception):
                from rss_mcp.rag_store import RssVectorStore

                RssVectorStore().drop()
        done = 0
        if is_available() and chunks:
            from rss_mcp.rag_store import RssVectorStore

            store = RssVectorStore()
            batch = 64
            for s in range(0, len(chunks), batch):
                store.upsert_chunks(chunks[s : s + batch], mode="append")
                done = min(s + batch, len(chunks))
                con = _con()
                try:
                    con.execute(
                        "UPDATE jobs SET total=?, done=?, updated=?, message=? WHERE id=?",
                        (len(chunks), done, int(time.time()), f"embedding {done}/{len(chunks)}", job_id),
                    )
                    con.commit()
                finally:
                    con.close()
        else:
            # FTS-only path still refreshes feeds so incremental stays useful.
            from rss_mcp import feeds as _feeds

            ids = sorted({int(it.get("feed_id") or 0) for it in items if it.get("feed_id")}) or [
                r["id"] for r in _feed_ids()
            ]
            total = max(len(ids), 1)
            con = _con()
            try:
                con.execute("UPDATE jobs SET total=? WHERE id=?", (total, job_id))
                con.commit()
            finally:
                con.close()
            for n, fid in enumerate(ids, 1):
                if fid:
                    with contextlib.suppress(Exception):
                        _feeds.refresh_feed(int(fid))
                con = _con()
                try:
                    con.execute(
                        "UPDATE jobs SET done=?, updated=?, message=? WHERE id=?",
                        (n, int(time.time()), f"swept {n}/{total}", job_id),
                    )
                    con.commit()
                finally:
                    con.close()
            done = 0
        LAST_SWEEP.update({"at": int(time.time()), "chunks": done, "mode": mode})
        con = _con()
        try:
            con.execute(
                "UPDATE jobs SET done=?, total=?, status='complete', updated=?, message='sweep complete' WHERE id=?",
                (done, max(done, 1), int(time.time()), job_id),
            )
            con.commit()
        finally:
            con.close()
    except Exception as e:
        con = _con()
        try:
            con.execute(
                "UPDATE jobs SET status='error', updated=?, message=? WHERE id=?",
                (int(time.time()), f"sweep failed: {e}", job_id),
            )
            con.commit()
        finally:
            con.close()


def _feed_ids() -> list[dict[str, Any]]:
    con = _con()
    try:
        return [dict(r) for r in con.execute("SELECT id FROM feeds ORDER BY id").fetchall()]
    finally:
        con.close()


def trigger_sweep(mode: str = "incremental", hours: int = 4, feed_id: int = 0) -> dict[str, Any]:
    mode = mode if mode in ("incremental", "full") else "incremental"
    job_id = uuid.uuid4().hex[:12]
    con = _con()
    try:
        con.execute(
            "INSERT INTO jobs(id, kind, total, done, status, message, updated) VALUES(?,?,?,?,?,?,?)",
            (job_id, "rag-sweep", 0, 0, "queued", f"{mode} queued", int(time.time())),
        )
        con.commit()
    finally:
        con.close()
    t = threading.Thread(target=_run_sweep, args=(job_id, mode, hours, feed_id), daemon=True)
    t.start()
    return {"success": True, "message": f"Sweep started: {job_id} ({mode})", "job_id": job_id, "status": "queued"}


def sweep_status(job_id: str) -> dict[str, Any]:
    con = _con()
    try:
        row = con.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
        if row is None:
            return {"success": False, "message": f"No job {job_id}", "status": "error", "chunks": 0}
        d = dict(row)
        status = str(d.get("status", "running"))
        if status == "done":
            status = "complete"
        return {
            "success": True,
            "message": f"Job {job_id}: {status} {d.get('done', 0)}/{d.get('total', 0)}",
            "status": status,
            "chunks": int(d.get("done", 0) or 0),
            "job": d,
        }
    finally:
        con.close()
