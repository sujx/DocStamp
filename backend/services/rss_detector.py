"""RSS/Atom feed detector — three-layer detection strategy.

Layer 1: HTML <link> tag scanning (auto-discovery)
Layer 2: Common path probing (/feed, /rss, /atom.xml...)
Layer 3: Site-specific rules from rss_rules.json (like RSSHub-Radar)
"""

import json
import os
import re
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

import requests

from errors import ErrorCode, ServiceResult

# ── Common paths to probe ────────────────────────────────────────────────
COMMON_FEED_PATHS = [
    "/feed", "/rss", "/atom.xml", "/feed.xml", "/index.xml",
    "/feed/", "/rss.xml", "/atom", "/feeds/posts/default",
]

# ── RSS/Atom MIME types for <link> tag detection ──────────────────────────
FEED_MIME_TYPES = {
    "application/rss+xml",
    "application/atom+xml",
    "application/feed+json",
    "application/xml",
    "text/xml",
}


class _LinkParser(HTMLParser):
    """Extract <link> tags with rel=alternate and feed MIME types."""

    def __init__(self):
        super().__init__()
        self.feeds: list[dict] = []

    def handle_starttag(self, tag, attrs):
        if tag != "link":
            return
        attr_dict = dict(attrs)
        rel = attr_dict.get("rel", "").lower()
        mime = attr_dict.get("type", "").lower()
        href = attr_dict.get("href", "")

        if "alternate" in rel and href and mime in FEED_MIME_TYPES:
            self.feeds.append({
                "url": href,
                "title": attr_dict.get("title", ""),
                "type": "rss" if "rss" in mime else ("atom" if "atom" in mime else "feed"),
            })


def detect_feeds(url: str) -> ServiceResult[list[dict]]:
    """Find RSS/Atom feeds for a given website URL.

    Args:
        url: Website URL (with or without scheme).

    Returns:
        ServiceResult[list[dict]] with feed entries {url, title, type}.
    """
    url = _normalize_url(url)
    if not url:
        return ServiceResult.fail(ErrorCode.VALIDATION_ERROR, "Invalid URL format")

    seen = set()
    feeds: list[dict] = []

    # Layer 1: HTML <link> tag scanning
    try:
        resp = requests.get(url, timeout=15, headers={
            "User-Agent": "docStamp-RSS-Detector/1.0",
            "Accept": "text/html,application/xhtml+xml",
        })
        resp.raise_for_status()

        # Force correct encoding for Chinese/eastern character sets
        if resp.encoding and resp.encoding.lower() in ("iso-8859-1", "latin-1", "windows-1252"):
            resp.encoding = resp.apparent_encoding or "utf-8"

        html_text = resp.text[:500_000]

        # Parse HTML for <link> tags
        parser = _LinkParser()
        parser.feed(html_text)  # first 500KB is enough
        parser.close()

        for f in parser.feeds:
            resolved = urljoin(resp.url, f["url"])
            key = resolved
            if key not in seen:
                seen.add(key)
                feeds.append({"url": resolved, "title": f["title"], "type": f["type"]})

    except requests.RequestException:
        pass  # Site unreachable — continue to other layers

    # Layer 2: Common path probing
    domain = urlparse(url).netloc
    for path in COMMON_FEED_PATHS:
        probe_url = f"https://{domain}{path}"
        if probe_url in seen:
            continue
        try:
            r = requests.head(probe_url, timeout=5, allow_redirects=True, headers={
                "User-Agent": "docStamp-RSS-Detector/1.0",
            })
            if r.status_code == 200:
                content_type = r.headers.get("content-type", "")
                feed_type = _guess_type(content_type)
                if feed_type:
                    seen.add(probe_url)
                    feeds.append({"url": probe_url, "title": path.strip("/"), "type": feed_type})
        except requests.RequestException:
            continue

    # Layer 3: Site-specific rules
    try:
        rules_path = os.path.join(os.path.dirname(__file__), "..", "rss_rules.json")
        with open(rules_path, "r") as f:
            rules = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        rules = {}

    if domain in rules:
        site_rules = rules[domain]

        # Direct feeds
        for feed in site_rules.get("feeds", []):
            key = feed["url"]
            if key not in seen:
                seen.add(key)
                feeds.append(dict(feed))

        # Path-based rules (like RSSHub-Radar)
        path_only = urlparse(url).path or "/"
        for rule in site_rules.get("path_rules", []):
            params = _match_pattern(rule["pattern"], path_only)
            if params is not None:
                feed_url = rule["feed"]
                feed_title = rule.get("title", "")
                for k, v in params.items():
                    feed_url = feed_url.replace(f":{k}", v)
                    feed_title = feed_title.replace(f":{k}", v)
                if feed_url not in seen:
                    seen.add(feed_url)
                    feeds.append({
                        "url": feed_url,
                        "title": feed_title,
                        "type": rule.get("type", "rss"),
                    })

    return ServiceResult.ok(feeds)


# ── Helpers ─────────────────────────────────────────────────────────────

def _normalize_url(url: str) -> str:
    """Add https:// if no scheme provided."""
    url = url.strip()
    if not url:
        return ""
    if "://" not in url:
        url = "https://" + url
    parsed = urlparse(url)
    if not parsed.netloc:
        return ""
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path or '/'}"


def _guess_type(content_type: str) -> str:
    """Guess feed type from Content-Type header."""
    ct = content_type.lower()
    if "rss" in ct or "xml" in ct:
        return "rss"
    if "atom" in ct:
        return "atom"
    if "json" in ct:
        return "json"
    return ""


def _match_pattern(pattern: str, path: str) -> dict | None:
    """Match a URL path against a pattern with :param placeholders.

    Example: _match_pattern('/:user/:repo', '/DIYgod/RSSHub')
    → {'user': 'DIYgod', 'repo': 'RSSHub'}
    """
    pattern_parts = pattern.strip("/").split("/")
    path_parts = path.strip("/").split("/")

    if len(pattern_parts) != len(path_parts):
        return None

    params = {}
    for pp, rp in zip(pattern_parts, path_parts):
        if pp.startswith(":"):
            params[pp[1:]] = rp
        elif pp.lower() != rp.lower():
            return None
    return params
