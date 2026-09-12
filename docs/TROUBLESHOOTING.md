# TROUBLESHOOTING
- DB locked: single writer, WAL on; delete data/rss.sqlite3-wal on crash.
- 304 not modified: normal for conditional GET, not an error.
- Empty dashboard: subscribe first, then refresh_all.
- Trafilatura short text: falls back to readability-lxml automatically.
- Paywall/empty: extract returns success False with honest message, no bypass.
- Semantic returns fts-only: install lancedb + fastembed optionally.
- Ports busy: start.ps1 clears 11974/11975 first.
