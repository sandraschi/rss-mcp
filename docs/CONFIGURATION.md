# CONFIGURATION
- RSS_MCP_DB: sqlite path, default data/rss.sqlite3 (repo-relative if relative).
- RSS_MCP_PORT: default 11974. RSS_MCP_HOST: default 127.0.0.1.
- CORS allowlist: http://127.0.0.1:11975 and http://localhost:11975 only.
- Fetch cap 2MB per feed/page. Timeouts 15s feeds, 20s articles.
- Semantic search needs optional lancedb/fastembed; without them search_semantic returns FTS with a message.
