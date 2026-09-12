# ARCHITECTURE
- src/rss_mcp/db.py: sqlite WAL, feeds/items/FTS5/extracts/jobs.
- feeds.py: httpx capped 2MB + ETag/Last-Modified, feedparser, defusedxml OPML.
- readability.py: trafilatura primary, readability-lxml/BS4 fallback, DB cache.
- search.py: FTS5 MATCH with LIKE fallback, optional LanceDB, threaded sweep jobs with job_id polling.
- tools_*.py: three portmanteaus, dialogic dicts.
- server.py: FastMCP 3.4.4 instance, skills provider, Prefab card, prompts.
- api.py: Starlette 1.0, explicit CORS for :11975 only, /api/* plus /mcp mount, /api/rag/sweep job pattern.
- webapp/: Vite React TS Tailwind, proxy /api + /mcp to :11974.
- No Tauri in v1 (T1+T2 only per gate).
