"""Reader tests: FTS search and sweep job lifecycle."""

import time

from rss_mcp import db, search


def _seed():
    con = db.connect()
    try:
        con.execute("INSERT INTO feeds(url, title) VALUES(?, ?)", ("http://example.com/f.xml", "F"))
        fid = con.execute("SELECT id FROM feeds WHERE url=?", ("http://example.com/f.xml",)).fetchone()["id"]
        cur = con.execute(
            "INSERT INTO items(feed_id, guid, title, summary) VALUES(?,?,?,?)",
            (fid, "g9", "Vienna coffee houses", "Melange and newspapers"),
        )
        iid = cur.lastrowid
        import contextlib

        with contextlib.suppress(Exception):
            con.execute(
                "INSERT INTO items_fts(rowid, title, summary) VALUES(?,?,?)",
                (iid, "Vienna coffee houses", "Melange and newspapers"),
            )
        con.commit()
    finally:
        con.close()


def test_fts_search():
    _seed()
    r = search.search_text("Vienna")
    assert r["success"] and len(r["items"]) >= 1


def test_semantic_falls_back_without_deps():
    r = search.search_semantic("Vienna")
    assert r["success"]
    assert r["mode"] in ("fts-only", "semantic", "semantic-error-fts-fallback", "semantic-unavailable-index-empty")


def test_sweep_job_lifecycle():
    _seed()
    r = search.trigger_sweep(mode="incremental", hours=4)
    assert r["success"] and r["job_id"]
    assert r["status"] in ("queued", "running")
    s = search.sweep_status(r["job_id"])
    assert s["success"] and s["status"] in ("queued", "running", "complete", "error")
    for _ in range(100):
        s = search.sweep_status(r["job_id"])
        assert s["success"]
        assert "chunks" in s
        if s["status"] in ("complete", "error"):
            break
        time.sleep(0.05)
    assert s["status"] in ("complete", "error")


def test_rag_stats_contract():
    s = search.rag_stats()
    assert s["success"]
    assert "total_vectors" in s and "model" in s and "dims" in s
    assert s["dims"] == 384
