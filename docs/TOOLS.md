# TOOLS (implemented only, no planned stubs)
## feeds_ops
subscribe(url, title) / unsubscribe(feed_id) / list_feeds() / refresh_feed(feed_id) / refresh_all() / fetch_items(feed_id?, unread_only, limit) / get_item(item_id) / mark_read(item_id, is_read) / mark_star(item_id, is_starred) / remove_item(item_id) / opml_import(opml_text) / opml_export() / feed_health(feed_id)
## readability_ops
extract(item_id, force) / get_cached(item_id) / clear_cache(item_id?) / list_extractors()
## reader_ops
inbox(limit) / starred(limit) / search_text(query, limit) / search_semantic(query, limit) / stats() / trigger_sweep() / sweep_status(job_id)
## Prefab + util
show_reader_prefab_card() app=True ToolResult+PrefabApp with text fallback. rss_help(). rss_shutdown().
