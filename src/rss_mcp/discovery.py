"""Feed discovery & recommender catalog: probe URLs for RSS/Atom tags and curate topics."""

from __future__ import annotations

import logging
import re
from typing import Any
from urllib.parse import urljoin

import httpx

logger = logging.getLogger("rss_mcp.discovery")

# Pre-curated high-signal RSS recommenders across tech, AI, science, and fleet interests
RECOMMENDED_CATALOG: list[dict[str, Any]] = [
    {
        "category": "AI & Machine Learning",
        "feeds": [
            {
                "title": "Simon Willison Weblog",
                "url": "https://simonwillison.net/atom/entries/",
                "description": "LLMs, AI engineering, data journalism, and Python.",
                "tags": ["AI", "LLM", "Python"],
            },
            {
                "title": "Simon Willison TIL",
                "url": "https://til.simonwillison.net/tils.atom",
                "description": "Things learned every day: prompt design, tools, MCP, sqlite.",
                "tags": ["AI", "Today I Learned"],
            },
            {
                "title": "HN AI & LLM Signal",
                "url": "https://hnrss.org/newest?q=LLM+OR+GPT+OR+Claude&points=25",
                "description": "Curated top Hacker News submissions about LLMs and AI.",
                "tags": ["AI", "Hacker News"],
            },
            {
                "title": "ArXiv CS.AI Latest",
                "url": "https://rss.arxiv.org/rss/cs.AI",
                "description": "Latest research papers in Artificial Intelligence from arXiv.",
                "tags": ["AI", "Research", "Papers"],
            },
            {
                "title": "ArXiv CS.CL Computation & Language",
                "url": "https://rss.arxiv.org/rss/cs.CL",
                "description": "Natural language processing, transformers, and LLM foundations.",
                "tags": ["NLP", "Research"],
            },
        ],
    },
    {
        "category": "IDE & Developer Tools (Fleet Signal)",
        "feeds": [
            {
                "title": "HN Cursor MCP Signal",
                "url": "https://hnrss.org/newest?q=cursor+MCP&points=10",
                "description": "Community discussions and tool releases for Cursor & Model Context Protocol.",
                "tags": ["Cursor", "MCP", "DevTools"],
            },
            {
                "title": "HN Windsurf IDE Signal",
                "url": "https://hnrss.org/newest?q=windsurf+IDE&points=10",
                "description": "Windsurf IDE, agentic cascades, and toolchain updates.",
                "tags": ["Windsurf", "DevTools"],
            },
            {
                "title": "Zed Editor Releases",
                "url": "https://github.com/zed-industries/zed/releases.atom",
                "description": "High-performance Rust code editor official release notes.",
                "tags": ["Zed", "Rust", "Releases"],
            },
            {
                "title": "Reddit r/CursorAI",
                "url": "https://www.reddit.com/r/CursorAI/new/.rss",
                "description": "Community tips, prompts, rules, and workflows for Cursor AI.",
                "tags": ["Cursor", "Reddit"],
            },
        ],
    },
    {
        "category": "Tech & Engineering",
        "feeds": [
            {
                "title": "Hacker News Frontpage",
                "url": "https://hnrss.org/frontpage",
                "description": "Top submissions on Hacker News.",
                "tags": ["Tech", "Startups"],
            },
            {
                "title": "Lobste.rs",
                "url": "https://lobste.rs/rss",
                "description": "Computing-focused community with high-signal technical discussions.",
                "tags": ["Programming", "Systems"],
            },
            {
                "title": "Changelog Master Feed",
                "url": "https://changelog.com/master/feed",
                "description": "News and podcasts for software developers.",
                "tags": ["Dev", "Open Source"],
            },
        ],
    },
    {
        "category": "Science & Space",
        "feeds": [
            {
                "title": "Nature Breaking News",
                "url": "https://www.nature.com/nature.rss",
                "description": "Leading international weekly journal of science.",
                "tags": ["Science", "Research"],
            },
            {
                "title": "NASA Breaking News",
                "url": "https://www.nasa.gov/rss/dyn/breaking_news.rss",
                "description": "Latest news and discoveries from NASA missions.",
                "tags": ["Space", "NASA"],
            },
        ],
    },
]

# Patterns for discovering RSS / Atom links in HTML <head>
LINK_RE = re.compile(
    r'<link[^>]+type=["\'](?:application/rss\+xml|application/atom\+xml|application/feed\+json)["\'][^>]*>',
    re.IGNORECASE,
)
HREF_RE = re.compile(r'href=["\']([^"\']+)["\']', re.IGNORECASE)
TITLE_RE = re.compile(r'title=["\']([^"\']+)["\']', re.IGNORECASE)


def get_recommended_catalog() -> list[dict[str, Any]]:
    """Return the curated list of recommended feeds categorized by domain."""
    return RECOMMENDED_CATALOG


def discover_feeds_from_url(url: str, timeout: float = 12.0) -> dict[str, Any]:
    """Probe a website URL to extract auto-discoverable RSS/Atom links."""
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) rss-mcp/0.1.0"}
    normalized_url = url.strip()
    if not (normalized_url.startswith("http://") or normalized_url.startswith("https://")):
        normalized_url = "https://" + normalized_url

    found: list[dict[str, str]] = []

    # 1. Fetch HTML and look for <link rel="alternate" type="application/rss+xml">
    try:
        with httpx.Client(timeout=timeout, follow_redirects=True) as client:
            resp = client.get(normalized_url, headers=headers)
            if resp.status_code == 200:
                html = resp.text
                for match in LINK_RE.finditer(html):
                    tag = match.group(0)
                    href_match = HREF_RE.search(tag)
                    if href_match:
                        feed_href = href_match.group(1)
                        full_feed_url = urljoin(str(resp.url), feed_href)
                        title_match = TITLE_RE.search(tag)
                        title = title_match.group(1) if title_match else "Discovered Feed"
                        if not any(f["url"] == full_feed_url for f in found):
                            found.append({"url": full_feed_url, "title": title})
    except Exception as exc:
        logger.debug("HTML link tag discovery failed for %s: %s", normalized_url, exc)

    # 2. If nothing found in HTML headers, probe common conventional endpoints
    if not found:
        common_candidates = [
            urljoin(normalized_url, "/feed"),
            urljoin(normalized_url, "/rss"),
            urljoin(normalized_url, "/atom.xml"),
            urljoin(normalized_url, "/feed.xml"),
            urljoin(normalized_url, "/rss.xml"),
            urljoin(normalized_url, "/index.xml"),
        ]
        with httpx.Client(timeout=5.0, follow_redirects=True) as client:
            for candidate in common_candidates:
                try:
                    head_resp = client.head(candidate, headers=headers)
                    if head_resp.status_code == 200:
                        content_type = head_resp.headers.get("content-type", "").lower()
                        if "xml" in content_type or "rss" in content_type or "atom" in content_type:
                            found.append({"url": candidate, "title": f"Feed at {candidate}"})
                            break
                except Exception as probe_exc:
                    logger.debug("Conventional endpoint probe failed for %s: %s", candidate, probe_exc)
                    continue

    return {
        "success": True,
        "input_url": url,
        "resolved_url": normalized_url,
        "feeds": found,
        "count": len(found),
    }
