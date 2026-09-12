"""SQLite layer: WAL, feeds/items FTS5, stars, extracts cache, jobs."""

from __future__ import annotations

import os
import sqlite3
import time
from pathlib import Path

SCHEMA = """
PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS feeds (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  url TEXT UNIQUE NOT NULL,
  title TEXT DEFAULT '',
  etag TEXT DEFAULT '',
  last_modified TEXT DEFAULT '',
  last_checked INTEGER DEFAULT 0,
  last_status INTEGER DEFAULT 0,
  error TEXT DEFAULT ''
);
CREATE TABLE IF NOT EXISTS items (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  feed_id INTEGER NOT NULL REFERENCES feeds(id) ON DELETE CASCADE,
  guid TEXT NOT NULL,
  title TEXT DEFAULT '',
  link TEXT DEFAULT '',
  published INTEGER DEFAULT 0,
  summary TEXT DEFAULT '',
  is_read INTEGER DEFAULT 0,
  is_starred INTEGER DEFAULT 0,
  UNIQUE(feed_id, guid)
);
CREATE VIRTUAL TABLE IF NOT EXISTS items_fts USING fts5(title, summary, content='items', content_rowid='id');
CREATE TABLE IF NOT EXISTS extracts (
  item_id INTEGER PRIMARY KEY REFERENCES items(id) ON DELETE CASCADE,
  title TEXT DEFAULT '',
  author TEXT DEFAULT '',
  text TEXT DEFAULT '',
  html TEXT DEFAULT '',
  extractor TEXT DEFAULT '',
  created INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS jobs (
  id TEXT PRIMARY KEY,
  kind TEXT DEFAULT '',
  total INTEGER DEFAULT 0,
  done INTEGER DEFAULT 0,
  status TEXT DEFAULT 'running',
  message TEXT DEFAULT '',
  updated INTEGER DEFAULT 0
);
"""


def db_path() -> Path:
    raw = os.getenv("RSS_MCP_DB", "data/rss.sqlite3")
    p = Path(raw)
    if not p.is_absolute():
        here = Path(__file__).resolve().parents[2]
        p = here / raw
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def connect() -> sqlite3.Connection:
    con = sqlite3.connect(str(db_path()))
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL;")
    con.execute("PRAGMA foreign_keys=ON;")
    return con


def init_db() -> None:
    con = connect()
    try:
        con.executescript(SCHEMA)
        con.commit()
    finally:
        con.close()


def now() -> int:
    return int(time.time())
