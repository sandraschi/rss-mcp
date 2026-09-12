"""Feed tests: subscribe/list, OPML roundtrip, refresh with respx mock (declared double)."""

import httpx
import respx

from rss_mcp import feeds

FEED_XML = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><title>Test Feed</title>
<item><guid>1</guid><title>Vienna news one</title><link>http://example.com/1</link><description>First story</description></item>
<item><guid>2</guid><title>Vienna news two</title><link>http://example.com/2</link><description>Second story</description></item>
</channel></rss>"""


def test_subscribe_and_list():
    r = feeds.subscribe("http://example.com/feed.xml", "Example")
    assert r["success"]
    lst = feeds.list_feeds()
    assert lst["success"] and len(lst["feeds"]) == 1


def test_opml_roundtrip():
    feeds.subscribe("http://example.com/a.xml", "A")
    feeds.subscribe("http://example.com/b.xml", "B")
    exp = feeds.opml_export()
    assert exp["success"] and "a.xml" in exp["opml"]
    # wipe and reimport
    for f in feeds.list_feeds()["feeds"]:
        feeds.unsubscribe(int(f["id"]))
    imp = feeds.opml_import(exp["opml"])
    assert imp["success"] and imp["added"] == 2


@respx.mock
def test_refresh_with_mock():
    respx.get("http://example.com/feed.xml").mock(return_value=httpx.Response(200, text=FEED_XML))
    feeds.subscribe("http://example.com/feed.xml", "Example")
    fid = feeds.list_feeds()["feeds"][0]["id"]
    r = feeds.refresh_feed(int(fid))
    assert r["success"] and r["added"] == 2
