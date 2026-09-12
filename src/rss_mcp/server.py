"""FastMCP server: rss-mcp instance, portmanteaus + help + shutdown + prefab card + skills."""

from __future__ import annotations

import contextlib
import json
from pathlib import Path
from typing import Any

from fastmcp import FastMCP
from fastmcp.tools import ToolResult

from rss_mcp import db, tools_feeds, tools_read, tools_reader

mcp = FastMCP(
    "rss-mcp",
    instructions="Local-first RSS reader + readability extractor. Subscribe, refresh, read clean text, FTS + semantic search.",
)

tools_feeds.register(mcp)
tools_read.register(mcp)
tools_reader.register(mcp)

with contextlib.suppress(Exception):
    from fastmcp.server.providers import SkillsDirectoryProvider

    skills_dir = Path(__file__).parent / "skills"
    if skills_dir.exists():
        mcp.add_provider(SkillsDirectoryProvider(str(skills_dir)))


@mcp.tool(annotations={"read_only": True})
async def rss_help() -> dict[str, Any]:
    """rss_help - Capability summary and op list.

    ## Return Format
    Dictionary with `success` (bool), `message` (str), registered tools, ports, and comparison vs glance-mcp.

    ## Examples
    - {} -> summary of reader capabilities and registered tools.
    """
    return {
        "success": True,
        "message": "rss-mcp: stateful local reader",
        "tools": ["feeds_ops", "readability_ops", "reader_ops", "show_reader_prefab_card", "rss_help", "rss_shutdown"],
        "ports": {"backend": 11974, "frontend": 11975},
        "vs_glance_mcp": "glance-mcp is a lightweight holdall (single-shot fetch, weather, probes). rss-mcp is a full reader with subscriptions, polling, readability cache, FTS, stars.",
    }


@mcp.tool(annotations={"destructive": True})
async def rss_shutdown() -> dict[str, Any]:
    """rss_shutdown - Graceful shutdown hook for the daemon.

    ## Return Format
    Dictionary with `success` (bool) and acknowledgement `message` (str).

    ## Examples
    - {} -> acknowledges shutdown request.
    """
    return {"success": True, "message": "Shutdown acknowledged. Stop the daemon with Ctrl+C or stop.bat."}


@mcp.tool(app=True, annotations={"read_only": True})
async def show_reader_prefab_card() -> Any:
    """show_reader_prefab_card - Prefab stats card for list/status/stats coverage.

    ## Return Format
    ToolResult with PrefabApp structured content plus plain-text fallback.

    ## Examples
    - {} -> renders reader stats card.
    """
    stats = tools_reader.stats_payload()
    lines = [
        f"rss-mcp reader: {stats.get('feeds', 0)} feeds, {stats.get('items', 0)} items, "
        f"{stats.get('unread', 0)} unread, {stats.get('starred', 0)} starred, "
        f"{stats.get('extracts', 0)} cached extracts."
    ]
    try:
        from prefab_ui.app import PrefabApp
        from prefab_ui.components import Card, CardContent, CardHeader, CardTitle, Text

        with Card(css_class="max-w-lg") as view:
            with CardHeader():
                CardTitle("rss-mcp Reader")
            with CardContent():
                Text(f"Feeds: {stats.get('feeds', 0)}  Items: {stats.get('items', 0)}")
                Text(f"Unread: {stats.get('unread', 0)}  Starred: {stats.get('starred', 0)}")
                Text(f"Cached extracts: {stats.get('extracts', 0)}")
        return ToolResult(content="\n".join(lines), structured_content=PrefabApp(view=view, title="rss-mcp Reader"))
    except Exception:
        return {"success": True, "message": lines[0], "stats": stats}


@mcp.resource("rss://status")
async def rss_status_resource() -> str:
    """rss://status - Dynamic reader metrics and system status resource.

    ## Return Format
    JSON string containing feed counts, items, unread, starred, and extracts.
    """
    return json.dumps(tools_reader.stats_payload())


@mcp.prompt("rss_help")
async def rss_help_prompt() -> str:
    return "rss-mcp help: use feeds_ops to subscribe/list/refresh, readability_ops to extract clean text, reader_ops for inbox/search/stats."


def _lifespan_probe() -> None:
    db.init_db()


_lifespan_probe()


def run_stdio() -> None:
    mcp.run()


def run_http(host: str = "127.0.0.1", port: int = 11974) -> None:
    from rss_mcp.api import serve

    serve(host=host, port=port)
