# rss-mcp - Superduper local-first RSS reader + readability extractor

Subscribe to feeds, get clean article text without ad sites, full-text + semantic search. Pure local SQLite, no account needed.

## Preview

Dashboard with KPIs (feeds/items/unread/starred), 3-pane Reader (feeds/items/clean text), Feeds manager with OPML, Inbox, Tools drill-down, Skills, Chat, Settings, Help, Logs.

## Install

| Option | Command |
|---|---|
| A naked PC | `pwsh -File start.ps1` (installs uv/bun via winget as needed) |
| B dev backend | `uv sync ; uv run python -m rss_mcp --serve` |
| C stdio (Claude Desktop) | `uv run python -m rss_mcp` |
| D frontend | `cd webapp ; bun install ; bun run dev --port 11975` |

See INSTALL.md. Onboarding: N/A (pure local util, no wrappee/account) - rationale in docs/DEVELOPMENT.md.

## Tools (all real, no stubs)

- feeds_ops: subscribe, unsubscribe, list_feeds, refresh_feed, refresh_all, fetch_items, get_item, mark_read, mark_star, remove_item, opml_import, opml_export, feed_health
- readability_ops: extract, get_cached, clear_cache, list_extractors
- reader_ops: inbox, starred, search_text, search_semantic, stats, trigger_sweep, sweep_status
- show_reader_prefab_card (Prefab app=True), rss_help, rss_shutdown

## Ports

Backend 11974, frontend 11975. Forbidden ports never used (3000/5000/5173/8000/8080).

## vs glance-mcp

glance-mcp is a lightweight holdall (single-shot fetch, weather, probes). rss-mcp is the stateful full reader: subscriptions, polling with ETag, readability cache, FTS5, stars, OPML, background sweeps.

## Dev

`just lint`, `just test`, `just ci`. See docs/DEVELOPMENT.md for declared doubles.
