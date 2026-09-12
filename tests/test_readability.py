"""Readability tests on static HTML fixture (no network, declared fixture)."""

from rss_mcp import db, readability

HTML = """<html><head><title>Static Article</title></head><body>
<article><h1>Static Article</h1>
<p>Vienna is a city with a long history of coffee houses and newspapers.</p>
<p>Readers like clean text without ads, popups, or tracking scripts.</p>
<p>This fixture paragraph adds length so trafilatura fallback paths trigger reliably.</p>
</article></body></html>"""


def test_fallback_extracts_static_html():
    got = readability._extract_fallback(HTML)
    assert "Vienna" in got["text"]
    assert got["extractor"] in ("readability-lxml", "beautifulsoup")


def test_list_extractors():
    r = readability.list_extractors()
    assert r["success"] and len(r["extractors"]) == 2


def test_cache_roundtrip():
    con = db.connect()
    try:
        con.execute("INSERT INTO feeds(url, title) VALUES(?, ?)", ("http://example.com/f.xml", "F"))
        fid = con.execute("SELECT id FROM feeds WHERE url=?", ("http://example.com/f.xml",)).fetchone()["id"]
        con.execute(
            "INSERT INTO items(feed_id, guid, title, link) VALUES(?,?,?,?)", (fid, "g1", "T", "http://example.com/1")
        )
        iid = con.execute("SELECT id FROM items WHERE guid='g1'").fetchone()["id"]
        con.execute(
            "INSERT INTO extracts(item_id, title, text, extractor, created) VALUES(?,?,?,?,?)",
            (iid, "T", "hello", "test", 1),
        )
        con.commit()
    finally:
        con.close()
    r = readability.get_cached(iid)
    assert r["success"] and r["text"] == "hello"
    c = readability.clear_cache(iid)
    assert c["success"] and c["cleared"] == 1
