"""DOCX XML 读取助手：把「打开产物 → 取 sectPr / 某段的 pPr / 某 run 的字体与颜色」封成纯函数。

纪要模块的版式断言一律读 XML 原值，不依赖 python-docx 的高层属性——这样工单
002-006 与 009 的国标符合性集共用同一套读法，断言写的就是 Word 看到的字节。
段落按文本定位（`paragraph_containing`），因为产物结构会随工单增长，序号不稳。
"""

import io

from docx import Document
from docx.oxml.ns import qn

# ── 打开与单位换算 ───────────────────────────────────────────────────

def open_docx(content: bytes) -> Document:
    """从字节流打开一份 DOCX（直接吃 HTTP 响应体，不落盘）。"""
    return Document(io.BytesIO(content))


def attr_of(element, name: str) -> str | None:
    """读 qn(name) 属性；元素为 None 或属性缺失返回 None。"""
    if element is None:
        return None
    return element.get(qn(name))


def mm(element, name: str) -> float | None:
    """把元素上某属性的 twips 值折算成毫米。"""
    raw = attr_of(element, name)
    return None if raw is None else int(raw) * 25.4 / 1440


def pt(element, name: str) -> float | None:
    """把元素上某属性的 twips 值折算成磅。"""
    raw = attr_of(element, name)
    return None if raw is None else int(raw) / 20


# ── 节与页面 ─────────────────────────────────────────────────────────

def sect_pr(doc: Document):
    """第一节的 w:sectPr。"""
    return doc.sections[0]._sectPr


def page_setup(doc: Document):
    """(w:pgSz, w:pgMar) 两个元素，供页面尺寸与页边距断言。"""
    sp = sect_pr(doc)
    return sp.find(qn("w:pgSz")), sp.find(qn("w:pgMar"))


# ── 段落 ─────────────────────────────────────────────────────────────

def paragraph_containing(doc: Document, needle: str):
    """第一段文本含 needle 的 w:p 元素；找不到直接失败，避免断言读空。"""
    for para in doc.paragraphs:
        if needle in para.text:
            return para._element
    raise AssertionError(f"产物里没有文本包含 {needle!r} 的段落")


def p_pr(p) -> object | None:
    """段落的 w:pPr。"""
    return p.find(qn("w:pPr"))


def p_child(p, path: str):
    """pPr 下的直接子元素，path 形如 'w:spacing'。"""
    pr = p_pr(p)
    return None if pr is None else pr.find(qn(path))


def alignment(p) -> str | None:
    """w:jc/@w:val —— 'both' 即两端对齐，'center' 居中。"""
    return attr_of(p_child(p, "w:jc"), "w:val")


def indent(p, name: str) -> int | None:
    """w:ind 上的一个属性（如 'w:firstLineChars'），返回原值整数。"""
    raw = attr_of(p_child(p, "w:ind"), name)
    return None if raw is None else int(raw)


def spacing(p, name: str) -> int | None:
    """w:spacing 上的一个属性（如 'w:line'、'w:before'），返回原值整数。"""
    raw = attr_of(p_child(p, "w:spacing"), name)
    return None if raw is None else int(raw)


def border(p, edge: str, name: str) -> str | None:
    """pPr/w:pBdr 下某条边（如 'w:bottom'）的属性值。"""
    pbdr = p_child(p, "w:pBdr")
    return None if pbdr is None else attr_of(pbdr.find(qn(edge)), name)


def tab_stops(p) -> list[tuple[str, int]]:
    """w:tabs 里的制表位，按文档顺序返回 (w:val, w:pos)。"""
    tabs = p_child(p, "w:tabs")
    if tabs is None:
        return []
    return [(t.get(qn("w:val")), int(t.get(qn("w:pos")))) for t in tabs.findall(qn("w:tab"))]


# ── 设置与页脚 ───────────────────────────────────────────────────────

def setting_on(doc: Document, tag: str) -> bool:
    """settings.xml 里某个开关元素（如 'w:evenAndOddHeaders'）是否为真。"""
    element = doc.settings.element.find(qn(tag))
    if element is None:
        return False
    return (element.get(qn("w:val")) or "true") != "false"


def footer_paragraph(doc: Document, kind: str = "odd"):
    """页码所在段落：kind 取 'odd'（默认页脚）或 'even'，返回 w:p 元素。"""
    section = doc.sections[0]
    footer = section.even_page_footer if kind == "even" else section.footer
    paragraphs = footer.paragraphs
    if not paragraphs:
        raise AssertionError(f"{kind} 页脚里没有段落")
    return paragraphs[0]._element


def forced_page_breaks(doc: Document) -> list:
    """强制另起一页的元素——分页符与分节符。7.5 不编页码的空白页只可能由它们产生。"""
    body = doc.element.body
    breaks = [e for e in body.iter(qn("w:br")) if attr_of(e, "w:type") in ("page", "evenPage", "oddPage")]
    return breaks + [e for e in body.iter(qn("w:sectPr")) if e.getparent().tag == qn("w:pPr")]


def field_instruction(p) -> str | None:
    """段落里 w:instrText 的文本（PAGE 域指令），没有则 None。"""
    for instr in p.iter(qn("w:instrText")):
        if instr.text and "PAGE" in instr.text:
            return instr.text.strip()
    return None


def paragraphs(doc: Document) -> list:
    """全文 w:p 元素，按文档顺序。"""
    return [para._element for para in doc.paragraphs]


def text_of(p) -> str:
    """段落可见文本：拼所有 w:t，忽略域代码。"""
    return "".join(t.text or "" for t in p.iter(qn("w:t")))


# ── 文本块（run） ─────────────────────────────────────────────────────

def runs(p) -> list:
    """段落下的 w:r 元素列表。"""
    return p.findall(qn("w:r"))


def first_run(p):
    """段落的第一个 w:r；没有则失败。"""
    found = runs(p)
    if not found:
        raise AssertionError("段落里没有 run")
    return found[0]


def r_pr(run):
    """run 的 w:rPr。"""
    return run.find(qn("w:rPr"))


def r_child(run, tag: str):
    """rPr 下的直接子元素，tag 形如 'w:rFonts'。"""
    pr = r_pr(run)
    return None if pr is None else pr.find(qn(tag))


def east_asia_font(run) -> str | None:
    """w:rFonts/@w:eastAsia —— 中文字体名。"""
    return attr_of(r_child(run, "w:rFonts"), "w:eastAsia")


def ascii_font(run) -> str | None:
    """w:rFonts/@w:ascii —— 西文/数字字体名。"""
    return attr_of(r_child(run, "w:rFonts"), "w:ascii")


def run_color(run) -> str | None:
    """w:color/@w:val —— 未显式设置返回 None（即随默认黑色）。"""
    return attr_of(r_child(run, "w:color"), "w:val")


def run_size_pt(run) -> float | None:
    """w:sz/@w:val 半磅 → 磅。"""
    raw = attr_of(r_child(run, "w:sz"), "w:val")
    return None if raw is None else int(raw) / 2
