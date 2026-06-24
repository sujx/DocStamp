"""Company name → official website lookup service.

Two-tier strategy:
    1. Local SQLite database (instant, confirmed results)
    2. LLM-powered web search (Zhipu/DeepSeek with web_search tool)

Set COMPANY_LOOKUP_API_KEY (or DOCSTAMP_DEEPSEEK_API_KEY) to enable web search.
Without an API key, only local DB results are returned.
"""

import json
import re
import time
from typing import Optional
from urllib.parse import urlparse

import requests

from config import Config
from errors import ErrorCode, ServiceResult
from models import CompanyRecord


# ── LLM Web Search ────────────────────────────────────────────────────────

def _search_llm(name: str) -> Optional[dict]:
    """Use an LLM with web search capability to find a company's official website.

    Calls an OpenAI-compatible chat completion API with web_search tool enabled.
    The LLM searches the web and extracts the correct website URL.

    Supported providers (set via COMPANY_LOOKUP_API_URL + COMPANY_LOOKUP_MODEL):
        - Zhipu BigModel (glm-4-flash with web_search tool)
        - Any OpenAI-compatible API with web search support

    Returns {"website": "https://...", "title": "..."} or None.
    """
    api_key = Config.COMPANY_LOOKUP_API_KEY
    if not api_key:
        return None

    api_url = Config.COMPANY_LOOKUP_API_URL
    model = Config.COMPANY_LOOKUP_MODEL

    has_chinese = bool(re.search(r'[一-鿿]', name))

    if has_chinese:
        prompt = (
            f'查找公司"{name}"的官方网站地址。'
            f'只返回JSON对象，包含键：website（完整URL）、name（公司名称）。'
            f'如果找不到官网，返回：{{"website": null, "name": "{name}"}}。'
            f'不要返回百科页面、社交媒体、股票页面。只返回公司自己的官方网站。'
        )
    else:
        prompt = (
            f'Find the official website URL for the company "{name}". '
            f"Return ONLY a JSON object with keys: website (the full URL), name (company name). "
            f"If you cannot find the official website, return: {{\"website\": null, \"name\": \"{name}\"}}. "
            f"Do not return encyclopedia pages (baike, wikipedia), social media, or stock pages. "
            f"Return the company's OWN official website."
        )

    try:
        resp = requests.post(
            api_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "temperature": 0,
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant that finds company websites. Always respond in valid JSON format."},
                    {"role": "user", "content": prompt},
                ],
                "tools": [{
                    "type": "web_search",
                    "web_search": {"enable": True},
                }],
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()

        content = ""
        if "choices" in data and len(data["choices"]) > 0:
            choice = data["choices"][0]
            msg = choice.get("message", {})
            content = msg.get("content", "")

        if not content:
            return None

        parsed = _parse_llm_json(content)
        if not parsed:
            return None

        website = parsed.get("website")
        if not website or website == "null" or website is None:
            return None

        website = _validate_url(website)
        if not website:
            return None

        return {"website": website, "title": parsed.get("name", name.strip())}

    except requests.RequestException:
        return None


def _parse_llm_json(content: str) -> Optional[dict]:
    """Parse JSON from LLM response, handling markdown code fences."""
    if not content:
        return None

    content = content.strip()
    if content.startswith("```"):
        lines = content.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        content = "\n".join(lines)

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        match = re.search(r'\{[^{}]*"website"\s*:\s*"[^"]*"[^{}]*\}', content, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        match = re.search(r'\{.*\}', content, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        return None


# ── Public API ────────────────────────────────────────────────────────────

def lookup_company(name: str, db: CompanyRecord) -> ServiceResult[dict]:
    """Look up a company's official website.

    Checks local DB first, then LLM web search.
    Without an API key, only local DB results are returned.
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

    # ── Tier 2: LLM web search ─────────────────────────────────────────
    result = _search_llm(name)
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
            f"No local record for '{name}' and COMPANY_LOOKUP_API_KEY is not configured. "
            f"Set the API key to enable web search.",
        )

    return ServiceResult.fail(
        ErrorCode.LOOKUP_NOT_FOUND,
        f"No official website found for '{name}'. Try a more complete company name.",
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

        web_result = _search_llm(name)
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
