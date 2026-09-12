"""LanceDB + FastEmbed vector store for rss-mcp article chunks.

Fleet default stack: lancedb + fastembed (BAAI/bge-small-en-v1.5, 384 dims).
Lazy imports so unit tests without the heavy deps still pass; runtime
reports availability via rag stats.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

MODEL_NAME = "BAAI/bge-small-en-v1.5"
TABLE_NAME = "rss_chunks"
CHUNK_SIZE = 800
CHUNK_OVERLAP = 120


def data_root() -> Path:
    root = Path(os.getenv("RSS_MCP_DATA", str(Path(__file__).resolve().parents[2] / "data")))
    root.mkdir(parents=True, exist_ok=True)
    return root


def lancedb_path() -> str:
    return str(data_root() / "lancedb")


def is_available() -> bool:
    try:
        import lancedb  # noqa: F401
        from fastembed import TextEmbedding  # noqa: F401

        return True
    except Exception:
        return False


def chunk_text(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    text = (text or "").strip()
    if not text:
        return []
    if len(text) <= size:
        return [text]
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        chunks.append(text[start:end])
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)
    return chunks


class RssVectorStore:
    """Thin wrapper over LanceDB table rss_chunks."""

    def __init__(self, uri: str | None = None, model: str = MODEL_NAME) -> None:
        import lancedb
        from fastembed import TextEmbedding

        self.uri = uri or lancedb_path()
        Path(self.uri).mkdir(parents=True, exist_ok=True)
        self.db = lancedb.connect(self.uri)
        cache = str(data_root() / "fastembed_cache")
        Path(cache).mkdir(parents=True, exist_ok=True)
        self.model = TextEmbedding(model_name=model, cache_dir=cache)
        self.model_name = model
        self.table = TABLE_NAME

    def _embed(self, texts: list[str]) -> list[list[float]]:
        return [e.tolist() for e in self.model.embed(texts)]

    def upsert_chunks(self, rows: list[dict[str, Any]], mode: str = "append") -> int:
        if not rows:
            return 0
        texts = [r["text"] for r in rows]
        vectors = self._embed(texts)
        data = [
            {
                "id": r["id"],
                "vector": v,
                "text": r["text"],
                "item_id": r["item_id"],
                "feed_id": r.get("feed_id", 0),
                "title": r.get("title", ""),
            }
            for r, v in zip(rows, vectors, strict=False)
        ]
        if mode == "overwrite" or self.table not in self.db.list_tables():
            self.db.create_table(self.table, data=data, mode="overwrite")
        else:
            self.db.open_table(self.table).add(data)
        return len(data)

    def search(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        if self.table not in self.db.list_tables():
            return []
        qv = next(iter(self.model.embed([query]))).tolist()
        return self.db.open_table(self.table).search(qv).limit(limit).to_list()

    def count(self) -> int:
        if self.table not in self.db.list_tables():
            return 0
        return int(self.db.open_table(self.table).count_rows())

    def drop(self) -> None:
        if self.table in self.db.list_tables():
            self.db.drop_table(self.table)
