"""Pytest fixtures: isolate DB to tmp_path via RSS_MCP_DB."""

import pytest


@pytest.fixture(autouse=True)
def _tmp_db(tmp_path, monkeypatch):
    p = tmp_path / "rss.sqlite3"
    monkeypatch.setenv("RSS_MCP_DB", str(p))
    from rss_mcp import db

    db.init_db()
    yield p
