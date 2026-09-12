"""CLI entry: stdio default, --serve for HTTP daemon on 11974."""

from __future__ import annotations

import argparse
import os


def main() -> None:
    ap = argparse.ArgumentParser(prog="rss-mcp")
    ap.add_argument("--serve", action="store_true", help="Run HTTP daemon (Starlette + /mcp).")
    ap.add_argument("--port", type=int, default=int(os.getenv("RSS_MCP_PORT", "11974")))
    ap.add_argument("--host", default=os.getenv("RSS_MCP_HOST", "127.0.0.1"))
    args = ap.parse_args()
    if args.serve:
        from rss_mcp.api import serve

        serve(host=args.host, port=args.port)
    else:
        from rss_mcp.server import mcp

        mcp.run()


if __name__ == "__main__":
    main()
