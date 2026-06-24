"""Company name → official website lookup service.

Two-tier strategy:
    1. Local SQLite database (instant, confirmed results)
    2. Zhipu BigModel web search API (raw search results, no LLM interpretation)

Set COMPANY_LOOKUP_API_KEY (or DOCSTAMP_DEEPSEEK_API_KEY) to enable web search.
"""

import re
import time
from typing import Optional
from urllib.parse import urlparse

import requests

from config import Config
from errors import ErrorCode, ServiceResult
from models import CompanyRecord


# ── Web Search (Zhipu dedicated endpoint) ────────────────────────────────

def _search_web(name: str) -> Optional[dict]:
    """Search for a company's official website using Zhipu's web search API.

    Uses the dedicated /api/paas/v4/web_search endpoint which returns
    raw search results directly — no LLM chat, no interpretation layer.

    Returns {"website": "https://...", "name": "..."} or None.
    """
    api_key = Config.COMPANY_LOOKUP_API_KEY
    if not api_key:
        return None

    query = f"{name} 官网"

    try:
        resp = requests.post(
            Config.COMPANY_LOOKUP_API_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "search_query": query[:70],       # API limit: 70 chars
                "search_engine": Config.COMPANY_LOOKUP_SEARCH_ENGINE,
                "search_intent": True,
                "count": 10,
            },
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()

        results = data.get("search_result") or []
        if not results:
            return None

        # Pick the best candidate — first result that passes validation
        for r in results:
            link = (r.get("link") or "").strip()
            website = _validate_url(link)
            if website and _is_plausible_official_site(website, name):
                return {"website": website, "name": name.strip()}

        return None

    except requests.RequestException:
        return None


# ── Public API ────────────────────────────────────────────────────────────

def lookup_company(name: str, db: CompanyRecord) -> ServiceResult[dict]:
    """Look up a company's official website.

    Checks local DB first, then web search API.
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

    # ── Tier 2: Web search API ─────────────────────────────────────────
    result = _search_web(name)
    if result:
        return ServiceResult.ok({
            "name": name.strip(),
            "website": result["website"],
            "source": "web",
            "confirmed": False,
        })

    if not Config.COMPANY_LOOKUP_API_KEY:
        return ServiceResult.fail(
            ErrorCode.LOOKUP_NOT_FOUND,
            f"No local record for '{name}' and COMPANY_LOOKUP_API_KEY is not configured.",
        )

    return ServiceResult.fail(
        ErrorCode.LOOKUP_NOT_FOUND,
        f"No official website found for '{name}'.",
    )


def confirm_company(
    name: str,
    website: str,
    db: CompanyRecord,
    corrected_name: Optional[str] = None,
    corrected_website: Optional[str] = None,
    source: str = "web",
) -> ServiceResult[dict]:
    """Confirm and save a company record to the local database."""
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
    """Synchronous batch lookup for Celery task use."""
    from models import _normalize_company_name
    db = CompanyRecord(db_path)
    results: list[dict] = []
    web_searches = 0

    for name in names:
        name = name.strip()
        if not name:
            results.append({"name": "", "website": "", "source": "error", "error": "Empty name"})
            continue

        normalized = _normalize_company_name(name)

        local = db.find_by_name(normalized)
        if local:
            results.append({
                "name": name,
                "website": local["website"],
                "source": "local",
                "confirmed": bool(local.get("confirmed_at")),
            })
            continue

        if web_searches > 0:
            time.sleep(0.5)
        web_searches += 1

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
                "error": "Not found",
            })

    return results


# ── URL Validation ────────────────────────────────────────────────────────

def _validate_url(raw_url: str) -> Optional[str]:
    """Validate and normalize a URL. Returns None if invalid."""
    if not raw_url:
        return None
    raw_url = raw_url.strip()
    if not raw_url.startswith("http"):
        raw_url = "https://" + raw_url.lstrip("/")
    if "://" not in raw_url:
        return None
    try:
        parsed = urlparse(raw_url)
        if not parsed.hostname:
            return None
        if parsed.scheme not in ("http", "https"):
            return None
        return raw_url
    except Exception:
        return None


def _is_plausible_official_site(url: str, company_name: str) -> bool:
    """Check if a URL is likely to be a company's official website.

    Rejects encyclopedia, social media, business registry, and other
    clearly-not-official-site URLs.
    """
    try:
        parsed = urlparse(url)
        hostname = (parsed.hostname or "").lower()
        path = (parsed.path or "").lower()
        full = hostname + path
    except Exception:
        return False

    # Known noise domains
    noise_domains = [
        "baike.baidu.com", "baike.eastmoney.com",
        "zh.wikipedia.org", "en.wikipedia.org", "wikipedia.org",
        "zhihu.com", "weibo.com", "douyin.com", "xiaohongshu.com",
        "tieba.baidu.com", "douban.com",
        "tianyancha.com", "qichacha.com", "qixin.com", "aiqicha.baidu.com",
        "gsxt.gov.cn",
        "quote.eastmoney.com", "xueqiu.com", "10jqka.com.cn",
        "static.cninfo.com.cn",
    ]
    for nd in noise_domains:
        if hostname == nd or hostname.endswith("." + nd):
            return False

    # gov.cn domains (unless company is government-related)
    if hostname.endswith(".gov.cn") and "政府" not in company_name:
        return False

    return True
