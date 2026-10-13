"""Comprehensive tests for Faves & Starred system, Discovery, and AIWatcher bridge."""

import pytest
from starlette.testclient import TestClient

from rss_mcp import aiwatcher_bridge, discovery, faves
from rss_mcp.api import build_app
from rss_mcp.feeds import subscribe
from rss_mcp.tools_reader import reader_ops


def test_faves_crud_and_collections():
    # 1. Create collection
    res = faves.create_collection("AI Research", "Curated papers and models", "#8b5cf6")
    assert res["success"]
    coll_id = res["collection"]["id"]

    # 2. List collections
    colls = faves.list_collections()
    assert any(c["id"] == coll_id for c in colls)

    # 3. Create feed and item to star
    sub = subscribe("https://example.com/test_ai_feed.xml", "AI Feed")
    feed_id = sub["feed"]["id"]

    from rss_mcp.db import connect, now

    con = connect()
    cur = con.execute(
        """
        INSERT INTO items (feed_id, guid, title, link, published, summary, is_read, is_starred)
        VALUES (?, ?, ?, ?, ?, ?, 0, 1)
        """,
        (feed_id, "guid-123", "Deep Learning Advances", "https://example.com/dl", now(), "Summary DL"),
    )
    con.commit()
    item_id = cur.lastrowid
    con.close()

    # 4. Add item to collection
    add_res = faves.add_item_to_collection(item_id, coll_id)
    assert add_res["success"]

    # 5. Set item note
    note_res = faves.set_item_note(item_id, "Very insightful architecture pattern")
    assert note_res["success"]
    assert faves.get_item_note(item_id) == "Very insightful architecture pattern"

    # 6. List starred items with collection filter
    items = faves.list_starred_items(collection_id=coll_id)
    assert len(items) >= 1
    target = next((i for i in items if i["id"] == item_id), None)
    assert target is not None
    assert target["note"] == "Very insightful architecture pattern"
    assert any(c["id"] == coll_id for c in target["collections"])

    # 7. Export starred items
    md = faves.export_starred(fmt="markdown", collection_id=coll_id)
    assert "Deep Learning Advances" in md
    assert "Very insightful architecture pattern" in md

    js = faves.export_starred(fmt="json", collection_id=coll_id)
    assert "Deep Learning Advances" in js

    # 8. Remove from collection and delete collection
    rem_res = faves.remove_item_from_collection(item_id, coll_id)
    assert rem_res["success"]
    del_res = faves.delete_collection(coll_id)
    assert del_res["success"]


def test_discovery_catalog_and_probe():
    catalog = discovery.get_recommended_catalog()
    assert len(catalog) >= 3
    assert any(cat["category"] == "AI & Machine Learning" for cat in catalog)

    # Probe fallback / conventional endpoints
    probe = discovery.discover_feeds_from_url("invalid-domain-nonexistent-123.org")
    assert probe["success"]
    assert isinstance(probe["feeds"], list)


def test_aiwatcher_bridge():
    bundles = aiwatcher_bridge.get_aiwatcher_bundles()
    assert isinstance(bundles, list)
    if bundles:
        bundle_id = bundles[0]["id"]
        import_res = aiwatcher_bridge.import_bundle_feeds(bundle_id)
        assert import_res["success"]

    # Promote item (offline fallback check)
    sub = subscribe("https://example.com/test_feed_pw.xml", "PW Feed")
    feed_id = sub["feed"]["id"]
    from rss_mcp.db import connect, now

    con = connect()
    cur = con.execute(
        """
        INSERT INTO items (feed_id, guid, title, link, published, summary, is_read, is_starred)
        VALUES (?, ?, ?, ?, ?, ?, 0, 1)
        """,
        (feed_id, "guid-pw-1", "AI Watcher Test", "https://example.com/pw", now(), "Summary PW"),
    )
    con.commit()
    item_id = cur.lastrowid
    con.close()

    prom_res = aiwatcher_bridge.promote_item_to_aiwatcher(item_id)
    assert prom_res["success"]
    assert prom_res.get("staged") or prom_res.get("response")


@pytest.mark.asyncio
async def test_reader_ops_new_operations():
    # Recommended feeds op
    rec = await reader_ops("recommended_feeds")
    assert rec["success"] and len(rec["categories"]) > 0

    # Discover feeds op
    disc = await reader_ops("discover_feeds", url="simonwillison.net")
    assert disc["success"]

    # Collections via reader_ops
    c_res = await reader_ops("create_collection", collection_name="Test Coll Op", collection_description="desc")
    assert c_res["success"]
    cid = c_res["collection"]["id"]

    l_res = await reader_ops("list_collections")
    assert l_res["success"] and any(c["id"] == cid for c in l_res["collections"])

    d_res = await reader_ops("delete_collection", collection_id=cid)
    assert d_res["success"]


def test_api_faves_and_discovery_routes():
    app = build_app()
    client = TestClient(app)

    # Catalog endpoint
    r = client.get("/api/discover/catalog")
    assert r.status_code == 200
    assert len(r.json()["categories"]) >= 3

    # Collections endpoints
    r = client.post("/api/faves/collections", json={"name": "API Coll", "description": "api", "color": "#10b981"})
    assert r.status_code == 200 and r.json()["success"]
    coll_id = r.json()["collection"]["id"]

    r = client.get("/api/faves/collections")
    assert r.status_code == 200 and any(c["id"] == coll_id for c in r.json()["collections"])

    # Starred list endpoint
    r = client.get("/api/faves")
    assert r.status_code == 200
    assert "items" in r.json()

    # Export endpoint
    r = client.get("/api/faves/export?format=markdown")
    assert r.status_code == 200
    assert "Starred RSS Items" in r.text

    # AIWatcher bundles endpoint
    r = client.get("/api/aiwatcher/bundles")
    assert r.status_code == 200
    assert "bundles" in r.json()

    # Cleanup collection
    r = client.delete(f"/api/faves/collections/{coll_id}")
    assert r.status_code == 200
