---
name: rss-mcp
description: Local-first RSS reader and readability extractor with LanceDB/FastEmbed semantic search
---

# rss-mcp Skill

Use rss-mcp for stateful RSS feed management and clean article extraction without web clutter or ads.

## Recommended Flow
1. Check available feeds: `feeds_ops(operation="list_feeds")`
2. Subscribe to new feeds: `feeds_ops(operation="subscribe", url="<feed_url>")`
3. Check inbox: `reader_ops(operation="inbox")`
4. Clean extract article: `readability_ops(operation="extract", item_id=<item_id>)`
5. Semantic vector search: `reader_ops(operation="search_semantic", query="<query>")`
