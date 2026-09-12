# rss-mcp Agent Guide
- `uv run python` only, never naked python. Full path uv: C:/Users/sandr/.local/bin/uv.exe
- Ruff line-length 120. No em dashes (ASCII hyphens only).
- Ports: backend 11974, frontend 11975.
- Portmanteaus: feeds_ops, readability_ops, reader_ops. No new tools without spec.
- DB via RSS_MCP_DB or data/rss.sqlite3. Never commit sqlite.
- justfile uses windows-shell powershell.exe.
