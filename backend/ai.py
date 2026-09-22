"""AI features — text correction, format classification, filename suggestion, denoising.

All endpoints share a single DeepSeek API client with SHA256-based caching
and automatic fallback (return input unchanged when API is unavailable).

Set DOCSTAMP_DEEPSEEK_API_KEY to enable.  If absent, all endpoints return
the input unchanged with an empty/silent response.
"""

import hashlib
import json

from flask import Blueprint, jsonify

from cache import cache
from config import Config
from error_handler import validate_request
from schemas import AiTextSchema, AiDenoiseSchema
from utils.rate_limit import rate_limit

ai_bp = Blueprint("ai", __name__)

API_KEY = Config.AI_API_KEY
API_URL = Config.AI_API_URL
API_MODEL = Config.AI_MODEL
CACHE_TTL = 3600


# ── Helpers ────────────────────────────────────────────────────────────

def _hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def _call(prompt: str, system: str = "", temperature: float = 0) -> str | None:
    """Call DeepSeek with prompt-level caching. Returns None on any failure."""
    if not API_KEY:
        return None

    cache_key = f"ai:{_hash(prompt + system)}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        import requests  # lazy — only needed when AI endpoint is called

        resp = requests.post(
            API_URL,
            headers={"Authorization": f"Bearer {API_KEY}"},
            json={
                "model": API_MODEL,
                "temperature": temperature,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
            },
            timeout=15,
        )
        resp.raise_for_status()
        result = resp.json()["choices"][0]["message"]["content"]
    except Exception:
        return None

    cache.set(cache_key, result, timeout=CACHE_TTL)
    return result


def _parse_json(raw: str | None) -> dict:
    """Safely parse LLM JSON output. Returns empty dict on failure."""
    if raw is None:
        return {}
    try:
        # Some models wrap JSON in ``` fences
        body = raw.strip()
        if body.startswith("```"):
            body = body.split("\n", 1)[1].rsplit("\n", 1)[0]
        return json.loads(body)
    except (json.JSONDecodeError, IndexError, AttributeError):
        return {}


# ── Routes ─────────────────────────────────────────────────────────────

@ai_bp.route("/api/v1/ai/correct", methods=["POST"])
@rate_limit(max_requests=20, window_seconds=60)
@validate_request(body=AiTextSchema)
def ai_correct(body: AiTextSchema):
    """Correct typos and punctuation in Markdown text."""
    text = body.text
    if not text.strip():
        return jsonify({"text": text, "changed": False})

    prompt = (
        "修正以下文本的错别字和标点错误。Markdown 标记（#、**、- 等）保持原样。\n"
        "返回 JSON：{\"text\": \"修正后的全文\"}\n\n" + text
    )
    result = _parse_json(_call(prompt, "你是中文校对助手，只修正明确错误，不改变原意。"))

    corrected = result.get("text", text)
    return jsonify({"text": corrected, "changed": corrected != text})


@ai_bp.route("/api/v1/ai/classify", methods=["POST"])
@rate_limit(max_requests=30, window_seconds=60)
@validate_request(body=AiTextSchema)
def ai_classify(body: AiTextSchema):
    """Detect if text is an official government document."""
    text = body.text[:1500]
    if not text.strip():
        return jsonify({"is_official": False, "confidence": 0})

    prompt = (
        "判断以下文本是否为正式公文（通知、请示、报告、函、纪要等）。\n"
        "正式公文特征：有发文机关、标题、主送机关、正文、落款。\n"
        "返回 JSON：{\"is_official\": true/false, \"confidence\": 0-1}\n\n" + text
    )
    result = _parse_json(_call(prompt, "你是中文公文格式识别助手。"))

    return jsonify({
        "is_official": result.get("is_official", False),
        "confidence": result.get("confidence", 0),
    })


@ai_bp.route("/api/v1/ai/suggest-filename", methods=["POST"])
@rate_limit(max_requests=30, window_seconds=60)
@validate_request(body=AiTextSchema)
def ai_suggest_filename(body: AiTextSchema):
    """Suggest a Chinese filename based on document content."""
    text = body.text[:1000]
    if not text.strip():
        return jsonify({"filename": ""})

    prompt = (
        "根据以下文档内容，生成一个简洁的中文文件名（15 字以内，不含扩展名）。\n"
        "格式：发文机关 + 事由 + 文种（如\"国务院关于加强环境保护工作的通知\"）。\n"
        "返回 JSON：{\"filename\": \"建议文件名\"}\n\n" + text
    )
    result = _parse_json(_call(prompt, "你是文档命名助手。"))

    return jsonify({"filename": result.get("filename", "")})


@ai_bp.route("/api/v1/ai/denoise", methods=["POST"])
@rate_limit(max_requests=20, window_seconds=60)
@validate_request(body=AiDenoiseSchema)
def ai_denoise(body: AiDenoiseSchema):
    """Remove header/footer/watermark noise from PDF-extracted text."""
    text = body.text
    if not text.strip():
        return jsonify({"text": text})

    system = (
        '你是 PDF 文本清理专家。去除从 PDF 提取的文本中的噪音，保留正文完整性。\n'
        '需要去除：\n'
        '1. 页眉（如"第 X 页""Chapter X"）\n'
        '2. 页脚（如页码、版权声明"© 2025 xxx"）\n'
        '3. 水印文字残留（如"DRAFT""CONFIDENTIAL""草稿"）\n'
        '4. 重复的标题行（每页顶部重复出现的内容）\n'
        '不要去除：正文内容、段落结构、表格数据、作者署名和落款。\n'
        '返回 JSON：{"text": "去噪后的全文"}'
    )
    result = _parse_json(_call(text[:8000], system))

    return jsonify({"text": result.get("text", text)})
