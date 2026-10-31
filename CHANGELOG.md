# Changelog
## Unreleased - 2026-10-31 (assfix)
- Fixed /mcp double-prefix (BUG-008): http_app(path="/") under Mount("/mcp") + bare-/mcp rewrite; initialize live-probed 200.
- Wired sub-app lifespan into parent (BUG-038); added GET /api/status + /api/v1/status.
- llm_models probes Ollama/LM Studio live, static list is declared offline fallback.
- start.ps1 uses full uv/bun paths (naked-exe instacrash fix); pre-commit-biome uses bun; hook installed.
- Tool-list sync: manifest + capabilities list all 6 tools; README bundle one-liner.
## 0.1.0 - 2026-09-12
- Initial release: feeds_ops, readability_ops, reader_ops, Prefab card, Starlette API, Vite webapp, OPML, FTS5, sweep jobs.
