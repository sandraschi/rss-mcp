# rss-mcp - Superduper local-first RSS reader + readability extractor

[![CI](https://github.com/sandraschi/rss-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/sandraschi/rss-mcp/actions/workflows/ci.yml)
[![FastMCP](https://img.shields.io/badge/FastMCP-3.1+-blue.svg)](https://github.com/jlowin/fastmcp)
[![Python 3.13](https://img.shields.io/badge/Python-3.13-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Subscribe to feeds, get clean article text without ad sites, full-text + semantic search. Pure local SQLite, no account needed.

## Features & Preview

- **Dashboard**: High-level KPIs (feeds, total items, unread, starred).
- **3-Pane Reader**: Feeds navigation, articles stream, and clean readability text extract pane.
- **Feeds Manager**: OPML import/export, feed health audits, refresh triggers.
- **Inbox & Starred**: Unified triage inbox and starred bookmarks.
- **RAG & Search**: FTS5 SQLite full-text search combined with LanceDB semantic vector sweeps.
- **Chat & LLM**: Built-in LLM exploration assistant with dynamic provider detection (Ollama, LM Studio, etc.).

## Framework Stack

- **Backend**: FastMCP 3.1+, Starlette / Uvicorn, SQLite3 WAL + FTS5, Trafilatura, LanceDB, Pyright (zero errors).
- **Frontend**: React 19, TypeScript, Vite, Tailwind CSS, Zustand, Lucide React, Biome linter.

## Install & Run

| Option | Command |
|---|---|
| A naked PC | `pwsh -File start.ps1` (installs uv/bun via winget as needed) |
| B dev backend | `uv sync ; uv run python -m rss_mcp --serve` |
| C stdio (Claude Desktop) | `uv run python -m rss_mcp` |
| D frontend | `cd webapp ; bun install ; bun run dev --port 11975` |

See [INSTALL.md](file:///d:/Dev/repos/rss-mcp/INSTALL.md). Onboarding: N/A (pure local util, no wrappee/account) - rationale in [docs/DEVELOPMENT.md](file:///d:/Dev/repos/rss-mcp/docs/DEVELOPMENT.md).

## Claude Desktop Configuration

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "rss-mcp": {
      "command": "uv",
      "args": [
        "--directory",
        "d:/Dev/repos/rss-mcp",
        "run",
        "python",
        "-m",
        "rss_mcp"
      ]
    }
  }
}
```

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `RSS_MCP_PORT` | `11974` | Backend server port (strict fleet standard) |
| `RSS_MCP_WEBAPP_PORT` | `11975` | Webapp frontend port |
| `RSS_MCP_HOST` | `127.0.0.1` | Host address to bind to |
| `RSS_MCP_DB` | `data/rss.sqlite3` | SQLite database file path |
| `RSS_MCP_LANCE_PATH` | `data/lancedb` | LanceDB vector database directory |

## Tools (all real, no stubs)

- `feeds_ops`: subscribe, unsubscribe, list_feeds, refresh_feed, refresh_all, fetch_items, get_item, mark_read, mark_star, remove_item, opml_import, opml_export, feed_health
- `readability_ops`: extract, get_cached, clear_cache, list_extractors
- `reader_ops`: inbox, starred, search_text, search_semantic, stats, trigger_sweep, sweep_status
- `show_reader_prefab_card`: Prefab card view for visual readers
- `rss_help`: Interactive help and quickstart
- `rss_shutdown`: Clean server termination

## Ports

Backend `11974`, frontend `11975`. Forbidden ports are never used (3000, 5000, 5173, 8000, 8080).

## vs glance-mcp

`glance-mcp` is a lightweight holdall (single-shot fetch, weather, probes). `rss-mcp` is the stateful full reader: subscriptions, polling with ETag, readability cache, FTS5, stars, OPML, background sweeps.

## Development

- Justfile shortcuts: `just lint`, `just typecheck`, `just test`, `just ci`, `just gates-green`
- Biome check: `bun run biome:ci` (in `webapp/`)
- Pre-commit hook: `powershell.exe -NoProfile -File scripts/pre-commit-biome.ps1`
- Pack MCPB bundle: `powershell.exe -NoProfile -File scripts/mcpb-pack.ps1`
