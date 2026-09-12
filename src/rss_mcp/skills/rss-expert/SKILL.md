# rss-expert skill
Use rss-mcp to read RSS without ad sites.
- feeds_ops list_feeds/subscribe/refresh_all/fetch_items/get_item/mark_read/mark_star/opml_import/opml_export/feed_health
- readability_ops extract(item_id)/get_cached/list_extractors (trafilatura then readability-lxml, no paywall bypass)
- reader_ops inbox/starred/search_text/search_semantic/stats/trigger_sweep/sweep_status
- show_reader_prefab_card for the stats card.
Glance-mcp is a lightweight holdall (single-shot fetch). rss-mcp is the stateful full reader: subscriptions, polling, cache, FTS.
