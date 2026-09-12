set windows-shell := ["powershell.exe", "-NoLogo", "-Command"]

default:
    @just --list

bootstrap:
    uv sync --extra dev
    cd webapp ; bun install
    uv run pre-commit install

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
    uv run pyright src
    cd webapp ; bun run check ; bun run biome:ci

fmt:
    uv run ruff check --fix src tests
    uv run ruff format src tests

ci:
    uv run ruff check src tests
    uv run ruff format --check src tests
    uv run pyright src
    uv run pytest -q
    cd webapp ; bun run check ; bun run biome:ci

certify:
    just ci
    powershell.exe -NoProfile -File scripts/mcpb-pack.ps1

gates-green:
    just ci

mcpb-pack:
    powershell.exe -NoProfile -File scripts/mcpb-pack.ps1

e2e:
    cd webapp ; bunx playwright test

cua-webapp-test:
    cd webapp ; bunx playwright test
