# DEVELOPMENT
## Onboarding N/A rationale
This repo is a pure local util with no wrappee app and no online account: feeds are public HTTP, storage is local SQLite, extraction is local libs. Hence no wrappee install flow, no account flow, no MOCK-until-onboarded gate. Webapp shows live /api/dashboard with honest empty states when DB is empty.
## Declared doubles (only these)
- tests use respx HTTP mocks for feed refresh (declared in test name) and static HTML fixtures for readability (no network).
- POST /api/llm/chat is a declared stub returning {declared_stub: true} - v1 has no LLM wiring; Settings page probes providers directly.
- No other mocks. No fake KPIs: dashboard reads live counts.
## Commands
- uv sync --extra dev ; uv run pytest -q ; uv run ruff check src tests ; just ci
- webapp: bun install ; bun run typecheck ; bunx biome check src
