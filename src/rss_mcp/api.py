"""Starlette API: health/capabilities/tools/dashboard/feeds/inbox/item/readability/skills/logs/llm/rag + /mcp mount."""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any

from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from rss_mcp import db, feeds, readability, search, tools_reader

STARTED = time.time()
LOG_BUF: list[str] = []


def log(msg: str) -> None:
    LOG_BUF.append(f"{int(time.time())} {msg}")
    if len(LOG_BUF) > 500:
        del LOG_BUF[: len(LOG_BUF) - 500]


async def health(_: Request) -> JSONResponse:
    return JSONResponse({"ok": True, "service": "rss-mcp", "uptime_s": int(time.time() - STARTED)})


async def capabilities(_: Request) -> JSONResponse:
    return JSONResponse(
        {
            "service": "rss-mcp",
            "tools": ["feeds_ops", "readability_ops", "reader_ops"],
            "ports": {"backend": 11974, "frontend": 11975},
        }
    )


async def tools(_: Request) -> JSONResponse:
    return JSONResponse(
        {
            "tools": [
                {
                    "name": "feeds_ops",
                    "ops": [
                        "subscribe",
                        "unsubscribe",
                        "list_feeds",
                        "refresh_feed",
                        "refresh_all",
                        "fetch_items",
                        "get_item",
                        "mark_read",
                        "mark_star",
                        "remove_item",
                        "opml_import",
                        "opml_export",
                        "feed_health",
                    ],
                },
                {"name": "readability_ops", "ops": ["extract", "get_cached", "clear_cache", "list_extractors"]},
                {
                    "name": "reader_ops",
                    "ops": [
                        "inbox",
                        "starred",
                        "search_text",
                        "search_semantic",
                        "stats",
                        "trigger_sweep",
                        "sweep_status",
                    ],
                },
            ]
        }
    )


async def dashboard(_: Request) -> JSONResponse:
    stats = tools_reader.stats_payload()
    return JSONResponse({"success": True, "stats": stats, "uptime_s": int(time.time() - STARTED)})


async def feeds_list(_: Request) -> JSONResponse:
    return JSONResponse(feeds.list_feeds())


async def feeds_refresh(_: Request) -> JSONResponse:
    return JSONResponse(feeds.refresh_all())


async def inbox(_: Request) -> JSONResponse:
    r = await tools_reader.reader_ops("inbox", limit=25)
    return JSONResponse(r)


async def item(req: Request) -> JSONResponse:
    item_id = int(req.path_params.get("id", 0))
    db.init_db()
    con = db.connect()
    try:
        row = con.execute("SELECT * FROM items WHERE id=?", (item_id,)).fetchone()
        if row is None:
            return JSONResponse({"success": False, "message": f"No item {item_id}"}, status_code=404)
        return JSONResponse({"success": True, "message": f"Item {item_id}", "item": dict(row)})
    finally:
        con.close()


async def extract(req: Request) -> JSONResponse:
    body: dict[str, Any] = {}
    try:
        body = await req.json()
    except Exception:
        body = {}
    item_id = int(body.get("item_id", 0))
    return JSONResponse(readability.extract(item_id, force=bool(body.get("force", False))))


async def skills(_: Request) -> JSONResponse:
    p = Path(__file__).parent / "skills" / "rss-expert" / "SKILL.md"
    content = p.read_text(encoding="utf-8") if p.exists() else ""
    return JSONResponse({"skills": [{"name": "rss-expert", "content": content[:8000]}]})


async def logs(_: Request) -> JSONResponse:
    return JSONResponse({"logs": LOG_BUF[-200:]})


async def llm_chat(req: Request) -> JSONResponse:
    # Declared stub: proxy to local LLM is not wired in v1; endpoint exists for webapp Settings probe.
    return JSONResponse(
        {
            "success": False,
            "message": "LLM proxy not configured in v1 (declared stub). Use webapp Settings to probe providers.",
            "declared_stub": True,
        }
    )


async def rag_sweep(_: Request) -> JSONResponse:
    r = search.trigger_sweep()
    log(f"sweep {r.get('job_id')}")
    return JSONResponse(r)


async def rag_sweep_status(req: Request) -> JSONResponse:
    job_id = str(req.path_params.get("job_id", ""))
    return JSONResponse(search.sweep_status(job_id))


def build_app() -> Starlette:
    routes = [
        Route("/api/health", health),
        Route("/api/capabilities", capabilities),
        Route("/api/tools", tools),
        Route("/api/dashboard", dashboard),
        Route("/api/feeds", feeds_list),
        Route("/api/feeds/refresh", feeds_refresh, methods=["POST"]),
        Route("/api/inbox", inbox),
        Route("/api/item/{id:int}", item),
        Route("/api/readability/extract", extract, methods=["POST"]),
        Route("/api/skills", skills),
        Route("/api/logs", logs),
        Route("/api/llm/chat", llm_chat, methods=["POST"]),
        Route("/api/rag/sweep", rag_sweep, methods=["POST"]),
        Route("/api/rag/sweep/{job_id}", rag_sweep_status),
    ]
    app = Starlette(routes=routes)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://127.0.0.1:11975", "http://localhost:11975"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    try:
        from rss_mcp.server import mcp as _mcp

        app.mount("/mcp", _mcp.http_app())
    except Exception as e:
        log(f"mcp mount failed: {e}")
    return app


def serve(host: str = "127.0.0.1", port: int = 11974) -> None:
    import uvicorn

    host = os.getenv("RSS_MCP_HOST", host)
    port = int(os.getenv("RSS_MCP_PORT", str(port)))
    db.init_db()
    # Daemon probe pattern: try proxy to existing 127.0.0.1:11974/mcp, else full init.
    try:
        import httpx as _hx

        r = _hx.get(f"http://127.0.0.1:{port}/api/health", timeout=1.5)
        if r.status_code == 200:
            print(f"rss-mcp already running on {port}, refusing second bind.")
            return
    except Exception:
        pass
    uvicorn.run(build_app(), host=host, port=port, log_level="warning")
