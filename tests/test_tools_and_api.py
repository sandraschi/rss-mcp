"""Tests for MCP portmanteaus, server endpoints, and Starlette REST API."""

import pytest
from starlette.testclient import TestClient

from rss_mcp.api import build_app
from rss_mcp.server import rss_help, rss_shutdown, rss_status_resource, show_reader_prefab_card
from rss_mcp.tools_feeds import feeds_ops
from rss_mcp.tools_read import readability_ops
from rss_mcp.tools_reader import reader_ops


@pytest.mark.asyncio
async def test_server_tools():
    h = await rss_help()
    assert h["success"] and "feeds_ops" in h["tools"]

    s = await rss_shutdown()
    assert s["success"]

    card = await show_reader_prefab_card()
    assert card is not None

    res = await rss_status_resource()
    assert "feeds" in res


@pytest.mark.asyncio
async def test_feeds_ops_lifecycle():
    sub = await feeds_ops("subscribe", url="http://example.com/test_feed.xml", title="Test")
    assert sub["success"]
    fid = sub["feed"]["id"]

    lst = await feeds_ops("list_feeds")
    assert lst["success"] and len(lst["feeds"]) >= 1

    health = await feeds_ops("feed_health", feed_id=fid)
    assert health["success"]

    items = await feeds_ops("fetch_items", feed_id=fid)
    assert items["success"]

    exp = await feeds_ops("opml_export")
    assert exp["success"] and "test_feed.xml" in exp["opml"]

    unsub = await feeds_ops("unsubscribe", feed_id=fid)
    assert unsub["success"]


@pytest.mark.asyncio
async def test_readability_ops():
    exts = await readability_ops("list_extractors")
    assert exts["success"] and any(e.get("name") == "trafilatura" for e in exts["extractors"])

    cached = await readability_ops("get_cached", item_id=99999)
    assert not cached["success"]

    clr = await readability_ops("clear_cache", item_id=99999)
    assert clr["success"]


@pytest.mark.asyncio
async def test_reader_ops():
    inb = await reader_ops("inbox")
    assert inb["success"]

    star = await reader_ops("starred")
    assert star["success"]

    st = await reader_ops("stats")
    assert st["success"] and "feeds" in st["stats"]

    rst = await reader_ops("rag_stats")
    assert rst["success"]

    sw = await reader_ops("trigger_sweep", mode="incremental", hours=1)
    assert sw["success"] and "job_id" in sw

    stat = await reader_ops("sweep_status", job_id=sw["job_id"])
    assert "status" in stat

    import asyncio

    await asyncio.sleep(0.15)


def test_starlette_api():
    app = build_app()
    client = TestClient(app)

    r = client.get("/api/health")
    assert r.status_code == 200 and r.json()["ok"]

    r = client.get("/api/capabilities")
    assert r.status_code == 200 and "feeds_ops" in r.json()["tools"]

    r = client.get("/api/tools")
    assert r.status_code == 200 and len(r.json()["tools"]) == 3

    r = client.get("/api/dashboard")
    assert r.status_code == 200 and r.json()["success"]

    r = client.get("/api/feeds")
    assert r.status_code == 200

    r = client.get("/api/inbox")
    assert r.status_code == 200

    r = client.get("/api/skills")
    assert r.status_code == 200

    r = client.get("/api/logs")
    assert r.status_code == 200

    r = client.get("/api/llm/discover")
    assert r.status_code == 200 and "providers" in r.json()

    r = client.get("/api/llm/providers")
    assert r.status_code == 200

    r = client.get("/api/llm/models")
    assert r.status_code == 200

    r = client.get("/api/llm/onboarding")
    assert r.status_code == 200 and r.json()["status"] == "ready"

    r = client.post("/api/chat", json={"messages": [{"role": "user", "content": "hello"}]})
    assert r.status_code == 200 and r.json()["success"]

    r = client.get("/api/rag/stats")
    assert r.status_code == 200
