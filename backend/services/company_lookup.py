"""Company name → official website lookup service.

Three-tier strategy:
    1. Local SQLite database (instant, confirmed results)
    2. LLM-powered web search (Zhipu/DeepSeek with web_search tool)
    3. Bing HTML scraping (fallback when API key not configured)
    4. DuckDuckGo HTML search (last resort)

Results from web search are returned as unconfirmed — the user must explicitly
confirm before they are saved to the local database.
"""

import json
import re
import time
from html.parser import HTMLParser
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

    prompt = (
        f'Find the official website URL for the company "{name}". '
        f"Return ONLY a JSON object with keys: website (the full URL), name (company name). "
        f"If you cannot find the official website, return: {{\"website\": null, \"name\": \"{name}\"}}. "
        f"Do not return encyclopedia pages (baike, wikipedia), social media, or stock pages. "
        f"Return the company's OWN official website."
    )
    if has_chinese:
        prompt = (
            f'查找公司"{name}"的官方网站地址。'
            f'只返回JSON对象，包含键：website（完整URL）、name（公司名称）。'
            f'如果找不到官网，返回：{{"website": null, "name": "{name}"}}。'
            f'不要返回百科页面、社交媒体、股票页面。只返回公司自己的官方网站。'
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

        # Extract the assistant's message content
        content = ""
        if "choices" in data and len(data["choices"]) > 0:
            choice = data["choices"][0]
            msg = choice.get("message", {})
            content = msg.get("content", "")

        if not content:
            return None

        # Parse the JSON response from the LLM
        parsed = _parse_llm_json(content)
        if not parsed:
            return None

        website = parsed.get("website")
        if not website or website == "null" or website is None:
            return None

        # Validate and normalize the URL
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

    # Strip markdown code fences
    content = content.strip()
    if content.startswith("```"):
        lines = content.split("\n")
        # Remove opening fence (```json or ```)
        if lines[0].startswith("```"):
            lines = lines[1:]
        # Remove closing fence
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        content = "\n".join(lines)

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        # Try to extract JSON from the content using regex
        match = re.search(r'\{[^{}]*"website"\s*:\s*"[^"]*"[^{}]*\}', content, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        # Try broader JSON extraction
        match = re.search(r'\{.*\}', content, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        return None


# ── Bing HTML scraping (fallback) ─────────────────────────────────────────

def _search_bing(name: str) -> Optional[dict]:
    """Search Bing HTML for a company's official website.

    Used as fallback when LLM web search API is not configured.
    Uses multi-query cascade and result scoring.
    """
    has_chinese = bool(re.search(r'[一-鿿]', name))

    if has_chinese:
        short = _short_name(name)
        queries = [
            f"{short} 官网",
            f"{name} 官网",
        ]
        if short != name.strip():
            queries.append(f"{short} 官方网站")
    else:
        queries = [
            f"{name} official website",
            f"{name} website",
        ]

    session = _get_session()
    all_candidates: list[tuple[str, int]] = []

    for query in queries:
        try:
            resp = session.get(
                "https://www.bing.com/search",
                params={"q": query, "setlang": "zh-cn" if has_chinese else "en"},
                timeout=15,
            )
            if resp.status_code != 200 or len(resp.text) < 5000:
                continue

            parser = _BingParser()
            parser.feed(resp.text[:300_000])
            parser.close()

            for result in parser.results:
                website = _validate_url(result.get("url", ""))
                if website:
                    score = _score_result(website, name)
                    if score > -100:
                        all_candidates.append((website, score))

        except requests.RequestException:
            continue

    if all_candidates:
        all_candidates.sort(key=lambda x: x[1], reverse=True)
        best_url, best_score = all_candidates[0]
        if has_chinese:
            has_strong = any(s >= 4 for _, s in all_candidates)
            if best_score >= 3 and has_strong:
                return {"website": best_url, "title": name.strip()}
        else:
            if best_score >= 2:
                return {"website": best_url, "title": name.strip()}

    return None


def _search_ddg(name: str) -> Optional[dict]:
    """Last resort: DuckDuckGo HTML search."""
    try:
        resp = requests.post(
            "https://html.duckduckgo.com/html/",
            data={"q": f"{name} 官网", "kl": "cn-zh"},
            timeout=15,
            headers={
                "User-Agent": "docStamp-CompanyLookup/1.0",
                "Accept": "text/html",
            },
        )
        resp.raise_for_status()

        class _DDGParser(HTMLParser):
            def __init__(self):
                super().__init__()
                self.results: list[dict] = []
                self._in_result = False
                self._in_link = False
                self._current: dict = {}

            def handle_starttag(self, tag, attrs):
                d = dict(attrs)
                classes = (d.get("class") or "").split()
                if tag == "div" and "result" in classes:
                    self._in_result = True
                    self._current = {}
                if self._in_result and tag == "a" and "result__a" in classes:
                    self._in_link = True
                    self._current["url"] = d.get("href", "")

            def handle_endtag(self, tag):
                if self._in_link and tag == "a":
                    self._in_link = False
                if tag == "div" and self._in_result:
                    self._in_result = False
                    if self._current.get("url"):
                        self.results.append(dict(self._current))

        parser = _DDGParser()
        parser.feed(resp.text[:300_000])
        parser.close()

        for result in parser.results:
            raw_url = result.get("url", "")
            if "uddg=" in raw_url:
                from urllib.parse import parse_qs, urlparse as _urlparse
                parsed = _urlparse(raw_url)
                if parsed.query:
                    params = parse_qs(parsed.query)
                    target = params.get("uddg", [None])[0]
                    if target:
                        raw_url = target
            if raw_url and not raw_url.startswith("http"):
                raw_url = "https://" + raw_url.lstrip("/")
            website = _validate_url(raw_url)
            if website and _score_result(website, name) >= 0:
                return {"website": website, "title": name.strip()}

        return None

    except requests.RequestException:
        return None


# ── Session & Parsers (shared by Bing fallback) ──────────────────────────

_search_session: Optional[requests.Session] = None


def _get_session() -> requests.Session:
    global _search_session
    if _search_session is None:
        _search_session = requests.Session()
        _search_session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "DNT": "1",
        })
        try:
            _search_session.get("https://www.bing.com/", timeout=10)
        except requests.RequestException:
            pass
    return _search_session


class _BingParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.results: list[dict] = []
        self._in_algo = False
        self._in_h2 = False
        self._current: dict = {}

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        classes = (d.get("class") or "").split()
        if tag == "li" and "b_algo" in classes:
            self._in_algo = True
            self._current = {}
        if self._in_algo and tag == "h2":
            self._in_h2 = True
        if self._in_h2 and tag == "a":
            href = d.get("href", "")
            if href and href.startswith("http"):
                self._current["url"] = href

    def handle_endtag(self, tag):
        if self._in_h2 and tag == "h2":
            self._in_h2 = False
        if tag == "li" and self._in_algo:
            self._in_algo = False
            if self._current.get("url"):
                self.results.append(dict(self._current))


# ── Public API ────────────────────────────────────────────────────────────

def lookup_company(name: str, db: CompanyRecord) -> ServiceResult[dict]:
    """Look up a company's official website.

    Checks local DB first, then LLM web search (with API key),
    then Bing scraping (fallback), then DuckDuckGo (last resort).
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

    # ── Tier 2: LLM web search (primary) ───────────────────────────────
    result = _search_llm(name)
    if result:
        return ServiceResult.ok({
            "name": name.strip(),
            "website": result["website"],
            "source": "web",
            "confirmed": False,
        })

    # ── Tier 3: Bing HTML scraping (fallback) ──────────────────────────
    result = _search_bing(name)
    if result:
        return ServiceResult.ok({
            "name": name.strip(),
            "website": result["website"],
            "source": "web",
            "confirmed": False,
        })

    # ── Tier 4: DuckDuckGo HTML (last resort) ──────────────────────────
    result = _search_ddg(name)
    if result:
        return ServiceResult.ok({
            "name": name.strip(),
            "website": result["website"],
            "source": "web",
            "confirmed": False,
        })

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

    for i, name in enumerate(names):
        name = name.strip()
        if not name:
            results.append({"name": name, "website": "", "source": "error", "error": "Empty name"})
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

        # Try LLM first, then fall back
        web_result = _search_llm(name) or _search_bing(name) or _search_ddg(name)
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


# ── Result Scoring (for Bing fallback) ────────────────────────────────────

def _score_result(website: str, company_name: str) -> int:
    """Score a search result URL for relevance to the company name.

    Returns:
        >= 4   — strong candidate (root path on commercial TLD)
        3      — plausible (commercial TLD, clean domain)
        < 0    — hard rejection (noise: dictionary, gov, social media)
    """
    try:
        parsed = urlparse(website)
        hostname = (parsed.hostname or "").lower()
    except Exception:
        return 0

    # ── Hard rejections ───────────────────────────────────────────────
    noise_domains = {
        "hanyuguoxue.com", "zdic.net", "zdic.com",
        "zidian.net", "chengyu.com", "chazidian.com",
        "chagushici.com",
        "beijing.gov.cn", "shanghai.gov.cn", "guangdong.gov.cn",
        "wikipedia.org", "baike.baidu.com", "wiki.mbalib.com",
        "zh.wikipedia.org", "en.wikipedia.org",
        "zhihu.com", "weibo.com", "douyin.com", "xiaohongshu.com",
        "tieba.baidu.com", "douban.com",
        "tianyancha.com", "qichacha.com", "qixin.com",
        "aiqicha.baidu.com", "gsxt.gov.cn",
        "quote.eastmoney.com", "xueqiu.com", "10jqka.com.cn",
        "eastmoney.com",
        "visitbeijing.com.cn", "travelchinaguide.com",
    }
    for noise in noise_domains:
        if hostname == noise or hostname.endswith("." + noise):
            return -100

    noise_keywords = [
        "zidian", "cidian", "hanyu", "guoxue", "chengyu",
        "gushi", "shici", "zuci", "bishun", "juzi",
        "wiki", "baike", "encyclopedia",
        "travel", "visit", "tourism", "tour",
        "news", "blog", "forum", "bbs",
        "hanzipi", "mihoyo", "hoyoverse",
        "jiaguwen", "renlu", "hgcha",
    ]
    url_full = (hostname + parsed.path).lower() if parsed.path else hostname
    for nk in noise_keywords:
        if nk in url_full:
            return -100

    if hostname.endswith(".gov.cn") and "政府" not in company_name:
        return -100

    # ── Scoring ──────────────────────────────────────────────────────
    score = 0
    if hostname.endswith(".com") or hostname.endswith(".cn") or hostname.endswith(".com.cn"):
        score += 2

    path = parsed.path or ""
    if len(path) <= 1:
        score += 1

    parts = hostname.split(".")
    if len(parts) <= 3:
        score += 1
    if len(hostname) > 30:
        score -= 2

    # English keyword matching
    name_lower = company_name.lower().strip()
    english_words = re.findall(r'[a-z0-9]+', name_lower)
    for w in english_words:
        if len(w) >= 3 and w in hostname:
            score += 5

    free_hosts = [
        "github.io", "gitlab.io", "netlify.app", "vercel.app",
        "wordpress.com", "blogspot.com", "weebly.com",
        "wixsite.com", "web.app", "firebaseapp.com",
        "myshopify.com", "aliexpress.com",
    ]
    for fh in free_hosts:
        if hostname.endswith("." + fh):
            score -= 3

    return score


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


# ── Short Name Extraction ─────────────────────────────────────────────────

def _short_name(name: str) -> str:
    """Extract the core company name by removing common corporate suffixes."""
    suffixes = [
        "技术股份有限公司", "科技股份有限公司",
        "股份有限公司", "有限责任公司", "有限公司", "责任公司",
        "集团有限公司", "集团公司", "集团",
        "技术有限公司", "科技有限公司",
        "网络科技有限公司", "信息技术有限公司",
        "网络技术有限公司", "在线网络技术有限公司",
        "计算机系统有限公司", "计算机科技有限公司",
        "信息科技有限公司", "软件技术有限公司",
        "网络技术", "信息技术", "科技", "技术",
    ]
    eng_suffixes = [
        " inc.", " inc", " ltd.", " ltd", " llc.", " llc",
        " corp.", " corp", " corporation", " co.", " co",
        " limited", " incorporated",
    ]
    city_prefixes = [
        "北京市", "上海市", "深圳市", "广州市", "杭州市",
        "成都市", "武汉市", "南京市", "天津市", "重庆市",
        "苏州市", "西安市", "东莞市", "长沙市", "郑州市",
        "北京", "上海", "深圳", "广州", "杭州",
        "成都", "武汉", "南京", "天津", "重庆",
        "苏州", "西安", "东莞", "长沙", "郑州",
    ]

    short = name.strip()
    for suffix in sorted(suffixes, key=len, reverse=True):
        if short.endswith(suffix):
            short = short[:-len(suffix)].strip()
            break
    for suffix in sorted(eng_suffixes, key=len, reverse=True):
        if short.lower().endswith(suffix.lower()):
            short = short[:-len(suffix)].strip()
            break
    for prefix in sorted(city_prefixes, key=len, reverse=True):
        if short.startswith(prefix) and len(short) - len(prefix) >= 2:
            short = short[len(prefix):].strip()
            break
    return short
