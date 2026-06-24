"""Company name → official website lookup service.

Two-tier strategy:
    1. Local SQLite database (instant, confirmed results)
    2. DuckDuckGo HTML search (fallback, no API key required)

Results from web search are returned as unconfirmed — the user must explicitly
confirm before they are saved to the local database.
"""

import re
import time
from html.parser import HTMLParser
from typing import Optional
from urllib.parse import urlparse

import requests

from errors import ErrorCode, ServiceResult
from models import CompanyRecord


# ── DuckDuckGo result parser ──────────────────────────────────────────────

class _DDGResultParser(HTMLParser):
    """Extract search result links and snippets from DuckDuckGo HTML."""

    def __init__(self):
        super().__init__()
        self.results: list[dict] = []
        self._in_result = False
        self._in_link = False
        self._in_snippet = False
        self._current: dict = {}
        self._capture = ""

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        classes = (attrs_dict.get("class") or "").split()

        if tag == "div" and "result" in classes:
            self._in_result = True
            self._current = {}

        if self._in_result and tag == "a" and "result__a" in classes:
            self._in_link = True
            href = attrs_dict.get("href", "")
            self._current["url"] = href

        if self._in_result and tag == "a" and "result__snippet" in classes:
            self._in_snippet = True
            self._capture = ""

    def handle_endtag(self, tag):
        if self._in_snippet and tag == "a":
            self._in_snippet = False
            self._current["snippet"] = self._capture.strip()
        if self._in_link and tag == "a":
            self._in_link = False
        if tag == "div" and self._in_result:
            self._in_result = False
            if self._current.get("url"):
                self.results.append(dict(self._current))

    def handle_data(self, data):
        if self._in_link:
            self._current["title"] = (self._current.get("title") or "") + data
        if self._in_snippet:
            self._capture += data


# ── Public API ────────────────────────────────────────────────────────────

def lookup_company(name: str, db: CompanyRecord) -> ServiceResult[dict]:
    """Look up a company's official website.

    Checks local DB first, then falls back to web search.
    Web results are returned unconfirmed.

    Args:
        name: Company name to look up.
        db: CompanyRecord instance for local DB access.

    Returns:
        ServiceResult[dict] with keys: name, website, source, confirmed.
    """
    if not name or not name.strip():
        return ServiceResult.fail(ErrorCode.VALIDATION_ERROR, "Company name is required")

    from models import _normalize_company_name
    normalized = _normalize_company_name(name)

    # ── Tier 1: Local database ─────────────────────────────────────────
    local = db.find_by_name(normalized)
    if local:
        return ServiceResult.ok({
            "name": name.strip(),
            "website": local["website"],
            "source": "local",
            "confirmed": bool(local.get("confirmed_at")),
        })

    # ── Tier 2: Web search ─────────────────────────────────────────────
    result = _search_web(name)
    if not result:
        return ServiceResult.fail(
            ErrorCode.LOOKUP_NOT_FOUND,
            f"No official website found for '{name}'. Try a more complete company name.",
        )

    return ServiceResult.ok({
        "name": name.strip(),
        "website": result["website"],
        "source": "web",
        "confirmed": False,
    })


def confirm_company(
    name: str,
    website: str,
    db: CompanyRecord,
    corrected_name: Optional[str] = None,
    corrected_website: Optional[str] = None,
    source: str = "web",
) -> ServiceResult[dict]:
    """Confirm and save a company record to the local database.

    If the user corrected the name or website, the corrected values are used.
    """
    final_name = (corrected_name or name).strip()
    final_website = (corrected_website or website).strip()

    if not final_name:
        return ServiceResult.fail(ErrorCode.VALIDATION_ERROR, "Company name is required")
    if "://" not in final_website:
        return ServiceResult.fail(ErrorCode.VALIDATION_ERROR, "Website must include scheme (https://...)")

    try:
        record = db.upsert(final_name, final_website, source=source)
        return ServiceResult.ok({
            "name": record["name"],
            "website": record["website"],
            "source": record.get("source", source),
            "confirmed": True,
            "saved": True,
        })
    except Exception as e:
        return ServiceResult.fail(ErrorCode.LOOKUP_FAILED, f"Failed to save record: {e}")


def batch_lookup(names: list[str], db_path: str) -> list[dict]:
    """Synchronous batch lookup for Celery task use.

    Returns a list of result dicts (including failures as error entries).
    Rate-limited to ~1s between web searches.
    """
    from models import _normalize_company_name
    db = CompanyRecord(db_path)
    results: list[dict] = []

    for i, name in enumerate(names):
        name = name.strip()
        if not name:
            results.append({"name": name, "website": "", "source": "error", "error": "Empty name"})
            continue

        normalized = _normalize_company_name(name)

        # Check local DB first
        local = db.find_by_name(normalized)
        if local:
            results.append({
                "name": name,
                "website": local["website"],
                "source": "local",
                "confirmed": bool(local.get("confirmed_at")),
            })
            continue

        # Web search with rate limiting
        if i > 0:
            time.sleep(1.5)  # Be polite to search engines

        web_result = _search_web(name)
        if web_result:
            results.append({
                "name": name,
                "website": web_result["website"],
                "source": "web",
                "confirmed": False,
            })
        else:
            results.append({
                "name": name,
                "website": "",
                "source": "error",
                "error": f"Not found: {name}",
            })

    return results


# ── Internal: Web Search ──────────────────────────────────────────────────

def _search_web(name: str) -> Optional[dict]:
    """Search DuckDuckGo HTML for a company's official website.

    Uses the HTML-only endpoint (no JS, no API key required).
    Returns {"website": "https://...", "title": "..."} or None.
    """
    query = f"{name} 官网"
    url = "https://html.duckduckgo.com/html/"

    try:
        resp = requests.post(
            url,
            data={"q": query, "kl": "cn-zh"},
            timeout=15,
            headers={
                "User-Agent": "docStamp-CompanyLookup/1.0",
                "Accept": "text/html",
            },
        )
        resp.raise_for_status()

        parser = _DDGResultParser()
        parser.feed(resp.text[:300_000])
        parser.close()

        for result in parser.results:
            website = _extract_website(result)
            if website:
                return {"website": website, "title": result.get("title", "").strip()}

        return None

    except requests.RequestException:
        return None


def _extract_website(result: dict) -> Optional[str]:
    """Extract and validate a website URL from a DDG search result.

    DuckDuckGo HTML results use redirect URLs (//duckduckgo.com/l/?uddg=...).
    We extract the actual target URL from the redirect parameter.
    """
    raw_url = result.get("url", "")

    # DDG redirect URLs look like: //duckduckgo.com/l/?uddg=https://example.com&rut=...
    if "uddg=" in raw_url:
        from urllib.parse import parse_qs, urlparse as _urlparse
        parsed = _urlparse(raw_url)
        if parsed.query:
            params = parse_qs(parsed.query)
            target = params.get("uddg", [None])[0]
            if target:
                raw_url = target

    # Ensure scheme
    if raw_url and not raw_url.startswith("http"):
        raw_url = "https://" + raw_url.lstrip("/")

    if not raw_url or "://" not in raw_url:
        return None

    # Filter out non-website results
    parsed = urlparse(raw_url)
    hostname = (parsed.hostname or "").lower()

    # Skip search engine pages, social media, encyclopedias
    skip_domains = {
        "duckduckgo.com", "google.com", "bing.com", "baidu.com",
        "zhihu.com", "weibo.com", "douyin.com",
        "wikipedia.org", "baike.baidu.com", "zh.wikipedia.org",
    }
    if hostname in skip_domains or hostname.endswith(".baidu.com"):
        return None

    return raw_url
