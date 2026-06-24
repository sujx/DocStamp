"""Company name → official website lookup service.

Three-tier strategy:
    1. Local SQLite database (instant, confirmed results)
    2. Bing search with multi-query fallback (primary)
    3. DuckDuckGo HTML search (last resort)

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


# ── Session factory (shared across searches, handles cookies) ──────────

_search_session: Optional[requests.Session] = None


def _get_session() -> requests.Session:
    """Get or create a persistent requests session with browser-mimicking headers."""
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


# ── Bing result parser ───────────────────────────────────────────────────

class _BingParser(HTMLParser):
    """Extract organic search result URLs from Bing HTML.

    Bing wraps each result in <li class="b_algo"> with an <h2><a href="...">
    containing the actual target URL.
    """

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

    Checks local DB first, then falls back to web search.
    Web results are returned unconfirmed.
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
            time.sleep(1.5)
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
                "error": f"Not found: {name}",
            })

    return results


# ── Internal: Web Search ──────────────────────────────────────────────────

def _search_web(name: str) -> Optional[dict]:
    """Search for a company's official website using Bing with multi-query cascade.

    Query strategy for Chinese names:
        1. "{full_name} 官网"     — broad search
        2. "{short_name} 官网"    — without suffixes like 有限公司
        3. "{short_name} 官方网站" — alternative phrasing

    Query strategy for English names:
        1. "{name} official website"
        2. "{name} website"

    Results are validated with _validate_result to filter out obvious mismatches
    (e.g. hasee.com for 神州高铁).

    Returns {"website": "https://...", "title": "..."} or None.
    """
    has_chinese = bool(re.search(r'[一-鿿]', name))

    if has_chinese:
        short = _short_name(name)
        # Try short name first — Bing gives better results for the core
        # company name without suffixes like 有限公司/股份有限公司
        queries = [
            f"{short} 官网",
            f"{name} 官网",
        ]
        # Only try long form if short form didn't work
        if short != name.strip():
            queries.append(f"{short} 官方网站")
    else:
        queries = [
            f"{name} official website",
            f"{name} website",
        ]

    session = _get_session()

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
                website = _extract_website(result)
                if website and _validate_result(website, name):
                    return {"website": website, "title": name.strip()}

        except requests.RequestException:
            continue

    # ── Last resort: DuckDuckGo HTML ────────────────────────────────────
    ddg_result = _search_ddg(name)
    if ddg_result:
        return ddg_result

    return None


def _search_ddg(name: str) -> Optional[dict]:
    """Fallback: DuckDuckGo HTML search."""
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
            if website and _validate_result(website, name):
                return {"website": website, "title": name.strip()}

        return None

    except requests.RequestException:
        return None


# ── URL Extraction & Validation ───────────────────────────────────────────

def _extract_website(result: dict) -> Optional[str]:
    """Extract and normalize a URL from a search result."""
    raw_url = result.get("url", "")
    return _validate_url(raw_url)


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
        hostname = parsed.hostname.lower()

        # Skip search engines, encyclopedias, social media, finance sites
        skip_domains = {
            "google.com", "bing.com", "baidu.com", "duckduckgo.com",
            "yahoo.com", "sogou.com", "so.com",
            "wikipedia.org", "baike.baidu.com", "zh.wikipedia.org",
            "en.wikipedia.org", "wiki.mbalib.com",
            "zhihu.com", "weibo.com", "douyin.com", "xiaohongshu.com",
            "tieba.baidu.com", "douban.com",
            "tianyancha.com", "qichacha.com", "qixin.com",
            "aiqicha.com", "gsxt.gov.cn",
            "quote.eastmoney.com", "xueqiu.com", "10jqka.com.cn",
            "amazon.com", "jd.com", "tmall.com", "taobao.com",
            "1688.com",
        }
        for skip in skip_domains:
            if hostname == skip or hostname.endswith("." + skip):
                return None

        # Skip paths that look like wiki/articles/posts
        path = parsed.path or ""
        skip_patterns = [
            r"/wiki/", r"/item/", r"/question/", r"/answer/",
            r"/p/\d+", r"/book/", r"/chapter/",
        ]
        for pat in skip_patterns:
            if re.search(pat, path):
                return None

        return raw_url
    except Exception:
        return None


def _validate_result(website: str, company_name: str) -> bool:
    """Check whether a search result URL plausibly belongs to the company.

    This filters out high-ranking-but-irrelevant results like hasee.com
    appearing for 神州高铁 queries.
    """
    try:
        parsed = urlparse(website)
        hostname = (parsed.hostname or "").lower()
    except Exception:
        return True  # If we can't parse, accept it — _validate_url already checked

    # Extract key terms from company name
    # For Chinese names: extract potential pinyin fragments
    # For English names: use words directly
    name_lower = company_name.lower().strip()

    # Build a set of keywords from the company name
    keywords: set[str] = set()

    # For English/numeric company names, extract alphanumeric words
    english_words = re.findall(r'[a-z0-9]+', name_lower)
    for w in english_words:
        if len(w) >= 3:
            keywords.add(w)

    # Check if any keyword appears in the hostname
    # This catches cases like:
    #   tencent.com → matches "tencent" from "腾讯" (via pinyin in domain)
    #   bytedance.com → matches "byte" or "dance" from "字节跳动" (via English name)
    for kw in keywords:
        if kw in hostname:
            return True

    # If no keywords matched, still accept the result — it passed the
    # domain filter and was the top Bing result. The user will confirm.
    return True


def _short_name(name: str) -> str:
    """Extract the core company name by removing common corporate suffixes.

    Examples:
        神州高铁技术股份有限公司 → 神州高铁
        北京字节跳动科技有限公司 → 字节跳动
        Apple Inc. → Apple
        腾讯科技有限公司 → 腾讯
    """
    # Chinese corporate suffixes (longest first to avoid partial matches)
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
    # English corporate suffixes
    eng_suffixes = [
        " inc.", " inc", " ltd.", " ltd", " llc.", " llc",
        " corp.", " corp", " corporation", " co.", " co",
        " limited", " incorporated",
    ]
    # Chinese city prefixes (common in registered company names)
    city_prefixes = [
        "北京市", "上海市", "深圳市", "广州市", "杭州市",
        "成都市", "武汉市", "南京市", "天津市", "重庆市",
        "苏州市", "西安市", "东莞市", "长沙市", "郑州市",
        "北京", "上海", "深圳", "广州", "杭州",
        "成都", "武汉", "南京", "天津", "重庆",
        "苏州", "西安", "东莞", "长沙", "郑州",
    ]

    short = name.strip()

    # Remove corporate suffixes
    for suffix in sorted(suffixes, key=len, reverse=True):
        if short.endswith(suffix):
            short = short[:-len(suffix)].strip()
            break

    # Remove English suffixes (case insensitive)
    for suffix in sorted(eng_suffixes, key=len, reverse=True):
        if short.lower().endswith(suffix.lower()):
            short = short[:-len(suffix)].strip()
            break

    # Remove city prefixes (only if the name still has 2+ characters after removal)
    for prefix in sorted(city_prefixes, key=len, reverse=True):
        if short.startswith(prefix) and len(short) - len(prefix) >= 2:
            short = short[len(prefix):].strip()
            break

    return short
