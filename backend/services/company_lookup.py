"""Company name → official website lookup service.

Two-tier strategy:
    1. Local SQLite database (instant, confirmed results)
    2. AI LLM — asks the model for the company's official website

Uses the same AI config as other AI features (AI_API_KEY / AI_API_URL / AI_MODEL).
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


# ── LLM Lookup ────────────────────────────────────────────────────────────

def _ask_llm(name: str) -> Optional[dict]:
    """Ask the AI model for a company's official website.

    The LLM answers from its training data — no web search tool needed.
    """
    api_key = Config.COMPANY_LOOKUP_API_KEY
    if not api_key:
        return None

    has_chinese = bool(re.search(r'[一-鿿]', name))

    if has_chinese:
        system = "你是一个企业信息查询助手。只返回JSON，不要其他内容。"
        prompt = (
            f'查询公司"{name}"的正式全称和官方网站地址。\n'
            f'返回JSON格式：{{"name": "公司正式全称", "website": "https://官网地址"}}\n'
            f'如果不知道官网地址，website设为null。\n'
            f'只返回JSON。'
        )
    else:
        system = "You are a company information assistant. Only return JSON, nothing else."
        prompt = (
            f'Find the official full name and website for company "{name}".\n'
            f'Return JSON: {{"name": "official company name", "website": "https://website"}}\n'
            f'Set website to null if unknown.\n'
            f'Only return JSON.'
        )

    try:
        resp = requests.post(
            Config.COMPANY_LOOKUP_API_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": Config.COMPANY_LOOKUP_MODEL,
                "temperature": 0,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
            },
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()

        content = ""
        if "choices" in data and len(data["choices"]) > 0:
            content = data["choices"][0].get("message", {}).get("content", "")

        if not content:
            return None

        parsed = _parse_json(content)
        if not parsed:
            return None

        website = parsed.get("website")
        if not website or website == "null" or website is None:
            return None

        website = _validate_url(website)
        if not website:
            return None

        return {
            "website": website,
            "name": parsed.get("name", name.strip()),
        }

    except requests.RequestException:
        return None


def _parse_json(content: str) -> Optional[dict]:
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

    Checks local DB first, then asks the AI LLM.
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

    # ── Tier 2: AI LLM ─────────────────────────────────────────────────
    result = _ask_llm(name)
    if result:
        return ServiceResult.ok({
            "name": result["name"],
            "website": result["website"],
            "source": "web",
            "confirmed": False,
        })

    if not Config.COMPANY_LOOKUP_API_KEY:
        return ServiceResult.fail(
            ErrorCode.LOOKUP_NOT_FOUND,
            f"No local record for '{name}' and AI_API_KEY is not configured.",
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
            time.sleep(0.3)
        web_searches += 1

        web_result = _ask_llm(name)
        if web_result:
            results.append({
                "name": web_result["name"],
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
