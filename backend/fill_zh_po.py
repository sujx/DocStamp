"""Fill zh_Hans_CN translations into backend/translations/zh_Hans_CN/LC_MESSAGES/messages.po.

Run from the WSL clone with the backend venv active:
    .venv/bin/python fill_zh_po.py
Re-runnable: existing msgstrs are preserved; unknown new msgids are left empty
and listed on stdout for you to add to TRANSLATIONS.
"""

import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[0]))

from babel.messages.pofile import read_po, write_po

TZ = {"Asia/Shanghai": "+0800"}  # noqa

TRANSLATIONS = {
    "Resource not found": "资源不存在",
    "Method not allowed": "请求方法不允许",
    "Request entity too large": "请求体过大",
    "系统异常": "系统异常",
    "File too large": "文件过大",
    "No content provided": "未提供内容",
    "Content is empty": "内容为空",
    "No file provided": "未提供文件",
    "No file selected": "未选择文件",
    "Invalid filename": "文件名无效",
    "File type not allowed for download": "不允许下载该文件类型",
    "File not found": "文件不存在",
    "No files provided": "未提供文件",
    "No files selected": "未选择文件",
    "At least 2 files are required for merging": "合并至少需要 2 个文件",
    "At least 2 valid Excel files are required": "至少需要 2 个有效的 Excel 文件",
    "No valid images uploaded": "没有上传有效的图片",
    "Thumbnail not found": "缩略图不存在",
    "No pages specified for deletion": "未指定要删除的页面",
    "No source file provided": "未提供源文件",
    "No insert file provided": "未提供插入文件",
    "No page order specified": "未指定页面顺序",
    "At least 2 PDF files are required": "至少需要 2 个 PDF 文件",
    "At least 2 valid PDF files are required": "至少需要 2 个有效的 PDF 文件",
    "Session not found": "会话不存在",
    "Invalid DPI for page rendering": "页面渲染的 DPI 无效",
    "DPI must be between %(lo)s and %(hi)s": "DPI 必须在 %(lo)s 到 %(hi)s 之间",
    "Page out of range": "页码超出范围",
    "Request body must be valid JSON": "请求体必须是合法的 JSON",
    "Pages must be a list of page numbers": "页码必须是页码数字列表",
    "No regions were marked": "没有标记任何区域",
    "Mosaic block size must be a whole number": "马赛克块大小必须是整数",
    "Mosaic block size must be between %(lo)s and %(hi)s": "马赛克块大小必须在 %(lo)s 到 %(hi)s 之间",
    "Nothing to download for this session": "该会话没有可下载的内容",
    "Invalid session id": "会话 ID 无效",
    "Batch size must be at least 1": "批次大小至少为 1",
    "Interval must be non-negative": "分组间隔必须为非负数",
    "Task not found": "任务不存在",
    "Invalid batch number": "批次号无效",
    "Batch file not found": "批次文件不存在",
    "No properties to modify": "没有需要修改的属性",
    "No valid files uploaded": "没有上传有效的文件",
    "No file could be modified": "没有文件被成功修改",
    "URL is required": "请输入 URL",
    "%(description)s failed (exit code %(code)s): %(stderr)s": "%(description)s失败（退出码 %(code)s）：%(stderr)s",
    "%(description)s timed out after %(timeout)ss": "%(description)s超时（%(timeout)s 秒）",
    "%(description)s failed: command '%(cmd)s' not found. Please ensure it is installed.": "%(description)s失败：未找到命令“%(cmd)s”，请确认已安装。",
    "File not found: %(fp)s": "文件不存在：%(fp)s",
    "No headers found in '%(name)s'": "“%(name)s”中未找到表头",
    "Structure mismatch in '%(name)s': expected %(expected)s, got %(got)s": "“%(name)s”结构不一致：期望 %(expected)s，实际 %(got)s",
    "No images provided": "未提供图片",
    "Image not found: %(path)s": "图片不存在：%(path)s",
    "Invalid or corrupt image: %(path)s (%(e)s)": "图片无效或已损坏：%(path)s（%(e)s）",
    "Image to PDF conversion failed: %(e)s": "图片转 PDF 失败：%(e)s",
    "Failed to create PDF: %(e)s": "创建 PDF 失败：%(e)s",
    "Unsupported file format: %(ext)s": "不支持的文件格式：%(ext)s",
    "Input file not found": "输入文件不存在",
    "Failed to read PDF: %(e)s": "读取 PDF 失败：%(e)s",
    "Mode must be 'page_number', 'header', or 'footer'": "模式必须是“page_number”、“header”或“footer”",
    "Text template is required": "必须提供文本模板",
    "Invalid position: %(position)s": "位置无效：%(position)s",
    "PDF has no pages": "PDF 没有页面",
    "Quality must be 'low', 'medium', or 'high'": "质量必须是“low”、“medium”或“high”",
    "Page number %(p)s out of range (1-%(total)s)": "页码 %(p)s 超出范围（1-%(total)s）",
    "Insert PDF has no pages": "待插入的 PDF 没有页面",
    "Insert position %(at_position)s out of range (0-%(total)s)": "插入位置 %(at_position)s 超出范围（0-%(total)s）",
    "Insert page %(p)s out of range (1-%(insert_total)s)": "插入页 %(p)s 超出范围（1-%(insert_total)s）",
    "Order must contain all pages 1-%(total)s exactly once": "顺序必须恰好包含 1-%(total)s 的每一页一次",
    "At least one PDF file is required": "至少需要 1 个 PDF 文件",
    "This PDF is encrypted — decrypt it first, then upload it again": "该 PDF 已加密——请先解密，再重新上传",
    "File not found: %(filepath)s": "文件不存在：%(filepath)s",
    "The PDF has no pages": "该 PDF 没有页面",
    "The PDF has %(page_count)s pages; this tool accepts up to %(max_pages)s": "该 PDF 有 %(page_count)s 页，本工具最多支持 %(max_pages)s 页",
    "Enter a keyword or pattern to search for": "请输入要搜索的关键词或正则",
    "The pattern is too long (limit %(MAX_PATTERN_LENGTH)s characters)": "正则表达式过长（上限 %(MAX_PATTERN_LENGTH)s 个字符）",
    "Invalid regular expression: %(e)s": "正则表达式无效：%(e)s",
    "Page %(p)s out of range (1-%(page_count)s)": "第 %(p)s 页超出范围（1-%(page_count)s）",
    "Failed to search the PDF: %(e)s": "搜索 PDF 失败：%(e)s",
    "Mark %(mark)s: invalid page number": "第 %(mark)s 个标记：页码无效",
    "Mark %(mark)s: page %(page)s is out of range (1-%(total)s)": "第 %(mark)s 个标记：第 %(page)s 页超出范围（1-%(total)s）",
    "Failed to redact PDF: %(e)s": "PDF 脱敏失败：%(e)s",
    "Unsupported format: %(fmt)s. Use 'png' or 'jpeg'.": "不支持的格式：%(fmt)s，请使用 png 或 jpeg。",
    "Invalid DPI: %(dpi)s": "无效的 DPI：%(dpi)s",
    "DPI must be between %(MIN_DPI)s and %(MAX_DPI)s, got %(dpi)s": "DPI 必须在 %(MIN_DPI)s 到 %(MAX_DPI)s 之间，当前为 %(dpi)s",
    "Page %(p)s out of range (1-%(total_pages)s)": "第 %(p)s 页超出范围（1-%(total_pages)s）",
    "pdftoppm failed: %(stderr)s": "pdftoppm 执行失败：%(stderr)s",
    "pdftoppm not found. Install poppler-utils: apt install poppler-utils": "未找到 pdftoppm，请安装 poppler-utils：apt install poppler-utils",
    "PDF text extraction failed: %(e)s": "PDF 文本提取失败：%(e)s",
    "No extractable text found in this PDF": "该 PDF 中没有可提取的文本",
    "Failed to read properties: %(e)s": "读取属性失败：%(e)s",
    "No files provided for batch processing": "未提供批量处理的文件",
    "Invalid URL format": "URL 格式无效",
    "Failed to convert WebP: %(e)s": "WebP 转换失败：%(e)s",
    "Too many requests. Please try again later.": "请求过于频繁，请稍后再试。",
    "Cannot parse datetime: %(value)s": "无法解析日期时间：%(value)s",
    "Cannot read file: %(err)s": "无法读取文件：%(err)s",
    "File size %(size)s exceeds limit of %(limit)s": "文件大小 %(size)s 超过上限 %(limit)s",
    "File has no extension": "文件没有扩展名",
    "File extension .%(ext)s is not allowed": "不允许的文件扩展名 .%(ext)s",
    "Cannot read file for magic check: %(err)s": "无法读取文件进行魔数校验：%(err)s",
    "File content does not match .%(ext)s format; upload rejected": "文件内容与 .%(ext)s 格式不符，已拒绝上传",
    "No filename provided": "未提供文件名",
    "Invalid characters in filename": "文件名包含非法字符",
    "Invalid filename after sanitization": "文件名清洗后无效",
}


def main() -> None:
    backend = Path(__file__).resolve().parents[0]
    pot_path = backend / "translations" / "messages.pot"
    po_path = backend / "translations" / "zh_CN" / "LC_MESSAGES" / "messages.po"
    po_path.parent.mkdir(parents=True, exist_ok=True)

    cat = read_po(pot_path.open("rb"))
    cat.fuzzy = False
    missing = []
    for message in cat:
        if not message.id:
            continue
        if message.string:
            continue
        if message.id in TRANSLATIONS:
            message.string = TRANSLATIONS[message.id]
        else:
            missing.append(message.id)

    cat.locale = "zh_CN"

    buf = io.BytesIO()
    write_po(buf, cat, width=76)
    po_path.write_bytes(buf.getvalue())
    print(f"wrote {po_path} ({len(TRANSLATIONS)} known translations)")
    if missing:
        print("UNTRANSLATED msgids (add them to TRANSLATIONS):")
        for m in missing:
            print("  ", repr(m))


if __name__ == "__main__":
    main()
