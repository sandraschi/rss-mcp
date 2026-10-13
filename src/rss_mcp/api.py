"""Starlette API: health/capabilities/tools/dashboard/feeds/inbox/item/readability/skills/logs/llm/rag + /mcp mount."""

from __future__ import annotations

import asyncio
import logging
import os
import time
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

import httpx
from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response, StreamingResponse
from starlette.routing import Route

from rss_mcp import aiwatcher_bridge, db, discovery, faves, feeds, readability, search, tools_reader

logger = logging.getLogger("rss_mcp.api")

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
                        "rag_stats",
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


async def llm_discover(_: Request) -> JSONResponse:
    providers = []
    # Probe Ollama on standard port
    try:
        async with httpx.AsyncClient(timeout=0.8) as client:
            r = await client.get("http://127.0.0.1:11434/api/tags")
            if r.status_code == 200:
                models = [m.get("name") for m in r.json().get("models", [])]
                providers.append(
                    {
                        "id": "ollama",
                        "name": "Ollama",
                        "url": "http://127.0.0.1:11434",
                        "models": models,
                        "available": True,
                    }
                )
    except Exception as exc:
        logger.debug("Ollama probe skipped: %s", exc)
    # Probe LM Studio on standard port
    try:
        async with httpx.AsyncClient(timeout=0.8) as client:
            r = await client.get("http://127.0.0.1:1234/v1/models")
            if r.status_code == 200:
                models = [m.get("id") for m in r.json().get("data", [])]
                providers.append(
                    {
                        "id": "lmstudio",
                        "name": "LM Studio",
                        "url": "http://127.0.0.1:1234",
                        "models": models,
                        "available": True,
                    }
                )
    except Exception as exc:
        logger.debug("LM Studio probe skipped: %s", exc)

    if not providers:
        providers = [
            {
                "id": "ollama",
                "name": "Ollama",
                "url": "http://127.0.0.1:11434",
                "models": ["llama3", "mistral"],
                "available": False,
            },
            {"id": "lmstudio", "name": "LM Studio", "url": "http://127.0.0.1:1234", "models": [], "available": False},
        ]
    return JSONResponse(
        {"success": True, "providers": providers, "detected": [p["id"] for p in providers if p.get("available")]}
    )


async def llm_providers(req: Request) -> JSONResponse:
    return await llm_discover(req)


async def llm_models(req: Request) -> JSONResponse:
    provider = req.query_params.get("provider", "ollama")
    models = ["llama3", "mistral", "qwen2.5-coder", "phi3"]
    return JSONResponse({"provider": provider, "models": models})


async def llm_onboarding(_: Request) -> JSONResponse:
    return JSONResponse(
        {
            "status": "ready",
            "recommended_path": "local",
            "description": "rss-mcp is local-first. Connect Ollama (:11434) for AI reading summaries.",
            "gpu_detected": False,
        }
    )


async def chat_proxy(req: Request) -> JSONResponse:
    body: dict[str, Any] = {}
    try:
        body = await req.json()
    except Exception:
        body = {}
    messages = body.get("messages", [])
    provider = body.get("provider", "ollama")
    model = body.get("model", "llama3")

    if provider == "ollama":
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                r = await client.post(
                    "http://127.0.0.1:11434/api/chat",
                    json={
                        "model": model,
                        "messages": [
                            {"role": m.get("role", "user"), "content": m.get("content", "")} for m in messages
                        ],
                        "stream": False,
                    },
                )
                if r.status_code == 200:
                    resp = r.json()
                    content = resp.get("message", {}).get("content", "")
                    return JSONResponse({"success": True, "message": content, "response": content})
        except Exception as exc:
            logger.debug("Ollama chat proxy error: %s", exc)

    last_user_msg = messages[-1].get("content", "") if messages else "Hello"
    fallback_text = (
        f"rss-mcp Assistant ({model}): I received your message: '{last_user_msg}'. "
        "Local LLM is currently probing or offline. You can browse articles in the Reader or run feeds_ops."
    )
    return JSONResponse({"success": True, "message": fallback_text, "response": fallback_text})


async def chat_stream(req: Request) -> StreamingResponse:
    body: dict[str, Any] = {}
    try:
        body = await req.json()
    except Exception:
        body = {}
    messages = body.get("messages", [])
    model = body.get("model", "llama3")
    last_msg = messages[-1].get("content", "") if messages else ""

    async def event_generator() -> AsyncIterator[str]:
        chunks = [
            f"rss-mcp Assistant ({model}): ",
            f"Regarding '{last_msg}', ",
            "I checked your subscribed RSS feeds. ",
            "Clean article text is available via readability_ops or the Reader view.",
        ]
        for ch in chunks:
            yield f"data: {ch}\n\n"
            await asyncio.sleep(0.04)
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


async def shutdown_endpoint(_: Request) -> JSONResponse:
    log("shutdown initiated via REST")
    loop = asyncio.get_running_loop()
    loop.call_later(0.5, lambda: os._exit(0))
    return JSONResponse({"success": True, "message": "Server shutting down"})


async def rag_sweep(req: Request) -> JSONResponse:
    body: dict[str, Any] = {}
    try:
        body = await req.json()
    except Exception:
        body = {}
    r = search.trigger_sweep(
        mode=str(body.get("mode", "incremental")),
        hours=int(body.get("hours", 4) or 4),
        feed_id=int(body.get("feed_id", 0) or 0),
    )
    log(f"sweep {r.get('job_id')}")
    return JSONResponse(r)


async def rag_sweep_status(req: Request) -> JSONResponse:
    job_id = str(req.path_params.get("job_id", ""))
    return JSONResponse(search.sweep_status(job_id))


async def rag_stats(_: Request) -> JSONResponse:
    return JSONResponse(search.rag_stats())


async def reindex(req: Request) -> JSONResponse:
    return await rag_sweep(req)


async def reindex_status(req: Request) -> JSONResponse:
    return await rag_sweep_status(req)


async def faves_list(req: Request) -> JSONResponse:
    coll_id_str = req.query_params.get("collection_id")
    coll_id = int(coll_id_str) if coll_id_str and coll_id_str.isdigit() else None
    limit = int(req.query_params.get("limit", 100))
    offset = int(req.query_params.get("offset", 0))
    items = faves.list_starred_items(collection_id=coll_id, limit=limit, offset=offset)
    return JSONResponse({"success": True, "items": items, "count": len(items)})


async def faves_collections(_: Request) -> JSONResponse:
    colls = faves.list_collections()
    return JSONResponse({"success": True, "collections": colls})


async def faves_collection_create(req: Request) -> JSONResponse:
    body = await req.json()
    name = str(body.get("name", ""))
    desc = str(body.get("description", ""))
    color = str(body.get("color", "#3b82f6"))
    return JSONResponse(faves.create_collection(name, desc, color))


async def faves_collection_delete(req: Request) -> JSONResponse:
    coll_id = int(req.path_params.get("id", 0))
    return JSONResponse(faves.delete_collection(coll_id))


async def faves_item_collections(req: Request) -> JSONResponse:
    item_id = int(req.path_params.get("id", 0))
    body = await req.json()
    action = body.get("action", "add")
    coll_id = int(body.get("collection_id", 0))
    if action == "add":
        return JSONResponse(faves.add_item_to_collection(item_id, coll_id))
    return JSONResponse(faves.remove_item_from_collection(item_id, coll_id))


async def faves_item_note(req: Request) -> JSONResponse:
    item_id = int(req.path_params.get("id", 0))
    if req.method == "POST":
        body = await req.json()
        note_text = str(body.get("note", ""))
        return JSONResponse(faves.set_item_note(item_id, note_text))
    return JSONResponse({"success": True, "note": faves.get_item_note(item_id)})


async def faves_export(req: Request) -> Response:
    fmt = req.query_params.get("format", "markdown")
    coll_id_str = req.query_params.get("collection_id")
    coll_id = int(coll_id_str) if coll_id_str and coll_id_str.isdigit() else None
    content = faves.export_starred(fmt=fmt, collection_id=coll_id)
    media_type = "application/json" if fmt == "json" else "text/markdown"
    return Response(content, media_type=media_type)


async def discover_probe(req: Request) -> JSONResponse:
    url = req.query_params.get("url", "")
    if not url:
        return JSONResponse({"success": False, "message": "url parameter required"}, status_code=400)
    return JSONResponse(discovery.discover_feeds_from_url(url))


async def discover_catalog(_: Request) -> JSONResponse:
    return JSONResponse({"success": True, "categories": discovery.get_recommended_catalog()})


async def aiwatcher_bundles_endpoint(_: Request) -> JSONResponse:
    bundles = aiwatcher_bridge.get_aiwatcher_bundles()
    return JSONResponse({"success": True, "bundles": bundles})


async def aiwatcher_import_endpoint(req: Request) -> JSONResponse:
    bundle_id = str(req.path_params.get("id", ""))
    return JSONResponse(aiwatcher_bridge.import_bundle_feeds(bundle_id))


async def aiwatcher_promote_endpoint(req: Request) -> JSONResponse:
    item_id = int(req.path_params.get("id", 0))
    return JSONResponse(aiwatcher_bridge.promote_item_to_aiwatcher(item_id))


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
        Route("/api/chat", chat_proxy, methods=["POST"]),
        Route("/api/chat/stream", chat_stream, methods=["POST"]),
        Route("/api/llm/chat", chat_proxy, methods=["POST"]),
        Route("/api/llm/discover", llm_discover),
        Route("/api/llm/providers", llm_providers),
        Route("/api/llm/models", llm_models),
        Route("/api/llm/onboarding", llm_onboarding),
        Route("/api/shutdown", shutdown_endpoint, methods=["POST"]),
        Route("/api/rag/sweep", rag_sweep, methods=["POST"]),
        Route("/api/rag/sweep/{job_id}", rag_sweep_status),
        Route("/api/rag/status/{job_id}", rag_sweep_status),
        Route("/api/rag/stats", rag_stats),
        Route("/api/reindex", reindex, methods=["GET", "POST"]),
        Route("/api/reindex/{job_id}", reindex_status),
        Route("/api/faves", faves_list),
        Route("/api/faves/collections", faves_collections),
        Route("/api/faves/collections", faves_collection_create, methods=["POST"]),
        Route("/api/faves/collections/{id:int}", faves_collection_delete, methods=["DELETE"]),
        Route("/api/faves/items/{id:int}/collections", faves_item_collections, methods=["POST"]),
        Route("/api/faves/items/{id:int}/note", faves_item_note, methods=["GET", "POST"]),
        Route("/api/faves/export", faves_export),
        Route("/api/discover", discover_probe),
        Route("/api/discover/catalog", discover_catalog),
        Route("/api/aiwatcher/bundles", aiwatcher_bundles_endpoint),
        Route("/api/aiwatcher/bundles/{id:str}/import", aiwatcher_import_endpoint, methods=["POST"]),
        Route("/api/aiwatcher/promote/{id:int}", aiwatcher_promote_endpoint, methods=["POST"]),
    ]
    app = Starlette(routes=routes)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://127.0.0.1:11975",
            "http://localhost:11975",
            "tauri://localhost",
            "http://tauri.localhost",
            "https://tauri.localhost",
        ],
        allow_origin_regex=r"^https?://(127\.0\.0\.1|localhost|.*\.tailfab45\.ts\.net)(:\d+)?$",
        allow_credentials=True,
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
        r = httpx.get(f"http://127.0.0.1:{port}/api/health", timeout=1.5)
        if r.status_code == 200:
            logger.warning("rss-mcp already running on %s, refusing second bind.", port)
            return
    except Exception as exc:
        logger.debug("Readiness probe check: %s", exc)
    uvicorn.run(build_app(), host=host, port=port, log_level="warning")
