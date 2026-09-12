# INSTALL - rss-mcp

## Option A - Naked PC (recommended)
1. Install PowerShell 7, uv, bun (winget).
2. `pwsh -File start.ps1` - starts backend :11974 and frontend :11975.

## Option B - Backend only
`uv sync` then `uv run python -m rss_mcp --serve`.

## Option C - Claude Desktop (stdio)
Add server `rss-mcp` with command `uv run python -m rss_mcp` in directory D:/Dev/repos/rss-mcp.

## Option D - Frontend dev
`cd webapp ; bun install ; bun run dev --port 11975`. Proxies /api and /mcp to 127.0.0.1:11974.

## Onboarding
N/A - pure local util, no wrappee or account. See docs/ONBOARDING.md and docs/DEVELOPMENT.md rationale.
