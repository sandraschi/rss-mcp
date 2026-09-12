# GitHub Copilot Instructions - rss-mcp

rss-mcp is a local-first RSS reader and readability extractor MCP server with LanceDB/FastEmbed semantic search.

## Key Guidelines
- Always use `uv run python`, never invoke system python directly.
- Ruff line length is 120; no em dashes in any file (ASCII hyphens only).
- Ports: Backend 11974, Frontend 11975. Never bind forbidden dev ports (3000, 5000, 5173, 8000, 8080).
- Tool portmanteaus: `feeds_ops` (subscription lifecycle), `readability_ops` (clean-text extraction), `reader_ops` (reading surface & RAG sweeps).
- All tool returns must be dialogic dictionaries with `success` (bool) and `message` (str).
