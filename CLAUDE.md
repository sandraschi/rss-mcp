# CLAUDE.md - rss-mcp

Local-first RSS reader and readability extractor FastMCP server with React/Tailwind webapp.

## Architecture

- **Backend**: Python 3.13, FastMCP 3.1+, SQLite WAL + FTS5, Trafilatura/Readability, LanceDB vector storage.
  - Entry point: `src/rss_mcp/__main__.py`, FastMCP server in `src/rss_mcp/server.py`.
  - REST and MCP mount: `src/rss_mcp/api.py`.
  - Database: `src/rss_mcp/db.py`, `src/rss_mcp/feeds.py`, `src/rss_mcp/search.py`.
  - RAG: `src/rss_mcp/rag_store.py`.
- **Frontend**: React 19, Vite, Tailwind CSS, Zustand, Lucide icons in `webapp/`.
- **Ports**: Backend `11974`, Webapp `11975` (strict fleet registry). Forbidden ports (3000, 5000, 5173, 8000, 8080) are never used.

## Essential Commands

### Python Backend
- Setup / sync: `uv sync --extra dev`
- Run stdio: `uv run python -m rss_mcp`
- Run HTTP server: `uv run python -m rss_mcp --serve` (or `uv run python -m rss_mcp --port 11974 --webapp-port 11975`)
- Lint and format: `uv run ruff check src tests` and `uv run ruff format src tests`
- Typecheck: `uv run pyright src`
- Test: `uv run pytest tests/ -q`
- Coverage: `uv run pytest tests/ --cov=rss_mcp --cov-report=term-missing`

### Webapp Frontend
- Setup: `cd webapp && bun install`
- Dev server: `cd webapp && bun run dev --port 11975`
- Typecheck: `cd webapp && bun run check`
- Biome check: `cd webapp && bun run biome:ci`
- Build: `cd webapp && bun run build`

### Fleet Quality Gates
- Just commands: `just lint`, `just typecheck`, `just test`, `just ci`, `just gates-green`
- Biome pre-commit: `powershell.exe -NoProfile -File scripts/pre-commit-biome.ps1`
- MCPB pack: `powershell.exe -NoProfile -File scripts/mcpb-pack.ps1`

## MCP Tool Surface

1. `feeds_ops(action, ...)`: `subscribe`, `unsubscribe`, `list_feeds`, `refresh_feed`, `refresh_all`, `fetch_items`, `get_item`, `mark_read`, `mark_star`, `remove_item`, `opml_import`, `opml_export`, `feed_health`
2. `readability_ops(action, ...)`: `extract`, `get_cached`, `clear_cache`, `list_extractors`
3. `reader_ops(action, ...)`: `inbox`, `starred`, `search_text`, `search_semantic`, `stats`, `trigger_sweep`, `sweep_status`
4. `show_reader_prefab_card(view, feed_id, item_id, query)`: UI Prefab for visual display
5. `rss_help()`: Interactive assistance and quickstart guide
6. `rss_shutdown(delay_seconds)`: Clean server termination

## Key Guidelines & Conventions

- No em-dashes (use ASCII hyphens only).
- Never catch exceptions without logging or proper suppression (`contextlib.suppress`).
- All tools must define return format documentation and examples.
- Keep test coverage above 60% with pyright zero-errors gate enabled.
