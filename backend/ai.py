"""AI features — text correction, format classification, filename suggestion, denoising.

All endpoints share a single DeepSeek API client with SHA256-based caching
and automatic fallback (return input unchanged when API is unavailable).

Set DOCSTAMP_DEEPSEEK_API_KEY to enable.  If absent, all endpoints return
the input unchanged with an empty/silent response.
"""

import hashlib
import json

import requests
from flask import Blueprint, jsonify, request

from cache import cache
from config import Config
from error_handler import validate_request
from schemas import AiTextSchema, AiDenoiseSchema

ai_bp = Blueprint("ai", __name__)

DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"
API_KEY = Config.DEEPSEEK_API_KEY
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
        resp = requests.post(
            DEEPSEEK_URL,
            headers={"Authorization": f"Bearer {API_KEY}"},
            json={
                "model": "deepseek-chat",
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
@validate_request(body=AiTextSchema)
def ai_correct():
    """Correct typos and punctuation in Markdown text."""
    text = request.parsed_body["text"]
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
@validate_request(body=AiTextSchema)
def ai_classify():
    """Detect if text is an official government document."""
    text = request.parsed_body["text"][:1500]
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
@validate_request(body=AiTextSchema)
def ai_suggest_filename():
    """Suggest a Chinese filename based on document content."""
    text = request.parsed_body["text"][:1000]
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
@validate_request(body=AiDenoiseSchema)
def ai_denoise():
    """Remove header/footer/watermark noise from PDF-extracted text."""
    text = request.parsed_body["text"]
    if not text.strip():
        return jsonify({"text": text})

    prompt = (
        "去除以下 PDF 提取文本中的噪音（页眉、页脚、页码、水印残留、重复标题行）。\n"
        "保留正文、段落结构、表格、作者署名和落款。\n"
        "返回 JSON：{\"text\": \"去噪后的全文\"}\n\n" + text[:5000]
    )
    result = _parse_json(_call(prompt, "你是 PDF 文本清理助手。"))

    return jsonify({"text": result.get("text", text)})
