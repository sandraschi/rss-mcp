set windows-shell := ["powershell.exe", "-NoLogo", "-Command"]

default:
    @just --list

serve:
    uv run python -m rss_mcp --serve

stdio:
    uv run python -m rss_mcp

test:
    uv sync --extra dev
    uv run pytest -q

lint:
    uv run ruff check src tests
    uv run ruff format --check src tests

fmt:
    uv run ruff check --fix src tests
    uv run ruff format src tests

ci:
    uv run ruff check src tests
    uv run ruff format --check src tests
    uv run pytest -q
    cd webapp ; bun run typecheck ; bunx biome check src

mcpb-pack:
    pwsh -NoProfile -File scripts/mcpb-pack.ps1

e2e:
    cd webapp ; bunx playwright test
