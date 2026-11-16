"""会议纪要 DOCX 生成 —— GB/T 9704—2012 第 10.3 条「纪要格式」。

不复用 services/formatter.py：那是「已有文档 → 重排版式」的后处理器，且它的
_set_run_font 会主动删掉 w:color（backend/services/formatter.py:69），红色纪要
标志会被抹黑。本模块从结构化字段直接生成，版式常量按
docs/superpowers/specs/2026-11-16-meeting-minutes-design.md §5 逐条落值。
"""

import re
from datetime import date

# docx.Document 是工厂函数，mypy 不接受它作类型标注；标注走真身 docx.document.Document。
from docx import Document
from docx.document import Document as DocxDocument
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor, Twips
from flask_babel import lazy_gettext as _l

from errors import ErrorCode, ServiceResult

# ── 版式常量（spec §5 逐条落值，勿从单位样例反推） ────────────────────

# 5.2.1：A4；天头 37 / 地脚 35 / 订口 28 / 切口 26 mm → 版心 156×225 mm。
PAGE_MM = {"width": 210, "height": 297, "top": 37, "bottom": 35, "left": 28, "right": 26}

# 版心宽：版记分隔线要与它等宽，右制表位也按它折算出「右空一字」。
CORE_WIDTH_MM = PAGE_MM["width"] - PAGE_MM["left"] - PAGE_MM["right"]

# 5.2.2：默认字体 3 号仿宋体。flag 属 10.3 纪要标志，ascii 走西文衬线。
FONT = {
    "flag": "方正小标宋简体",
    "body": "仿宋_GB2312",
    "heiti": "黑体",
    "kaiti": "楷体_GB2312",
    "song": "宋体",
    "ascii": "Times New Roman",
}

# 7.3.3 层次序号：序号 run 换字体，条目正文仍是仿宋。
LEVEL_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"^[一二三四五六七八九十]+、"), FONT["heiti"]),
    (re.compile(r"^（[一二三四五六七八九十]+）"), FONT["kaiti"]),
    (re.compile(r"^\d+\."), FONT["body"]),
    (re.compile(r"^（\d+）"), FONT["body"]),
)

# 字号（磅）：二号 22 / 三号 16 / 四号 14。
SIZE_PT = {"two": 22, "three": 16, "four": 14}

# 5.2.3：一般每面排 22 行 → 版心高 225mm ÷ 22 = 固定 29 磅行距。
LINE_PT = 29

# 7.3.3：每个自然段左空二字（200 = 2.00 字），回行顶格靠不写 w:left 保证。
FIRST_LINE_CHARS = 200

# 10.3 + D2/D3：标志上边缘距版心上边缘 35mm；国标未规定标志字号与红色色值，
# 按钉死值取二号小标宋 + 纯红（与单位样例、formatter 的标题字号一致）。
FLAG_TOP_MM = 35
FLAG_COLOR = "FF0000"

# D6：标志与主体之间空二行，接一条红色分隔线；国标未定线粗，钉单位样例的 2.25 磅
# （w:sz 以 1/8 磅计 → 18）。
HEAD_RULE_PT = 2.25
HEAD_RULE_BLANK_LINES = 2

# 10.3 第 2、3 条：标签 + 全角冒号占三字位，故回行对齐位是左空五字（2 空 + 2 标签 + 1 冒号），
# 首行由悬挂回退三字落到「左空二字」。
ROSTER_LEFT_CHARS = 500

# 10.3 的行款顺序固定：出席 → 请假 → 列席。
ROSTER_BLOCKS: tuple[tuple[str, str], ...] = (
    ("attendees", "出席"),
    ("leave", "请假"),
    ("witness", "列席"),
)

# 7.3.4：「附件」二字 + 全角冒号共三字，首行左空二字，故回行对齐位在五字处；
# 带顺序号（「1. 」约二字）时名称首字再后移到七字位。
ATTACH_LABEL = "附件"
ATTACH_WRAP_CHARS = 500
ATTACH_NUMBERED_WRAP_CHARS = 700
# 7.3.4「附件名称后不加标点符号」：把用户手打的结尾标点剥掉。
NAME_TRAILING_PUNCTUATION = "。；，、；,.;"

# 7.4.2 抄送机关：左右各空一字，「抄送」二字 + 全角冒号共三字，故回行对齐位在四字处
# （左空一字 + 三字），首行由悬挂回退三字落到一字位。
CC_LABEL = "抄送"
CC_LEFT_CHARS = 100
CC_WRAP_CHARS = 400
CC_RIGHT_CHARS = 100

# 7.4.1：版记分隔线与版心等宽，首末粗线、中间细线；国标按毫米给厚度（推荐 0.35 / 0.25），
# w:sz 以 1/8 磅计 → 0.35mm≈8、0.25mm≈6。色走 auto（5.2.4：除标志与版头线外全为黑色）。
COLOPHON_RULE_COLOR = "auto"
COLOPHON_THICK_MM = 0.35
COLOPHON_THIN_MM = 0.25
# 分隔线段落只撑到线本身的高度，不再多吃一个 29 磅行。
COLOPHON_RULE_LINE_PT = 1

# 7.4.3：印发机关左空一字、印发日期右空一字，日期后加「印发」二字。
PRINT_SUFFIX = "印发"

# 7.5：页码用 4 号半角宋体，数字左右各一条一字线；单页码居右空一字、双页码居左空一字。
PAGE_DASH = "—"
PAGE_EDGE_CHARS = 100
# 7.5：一字线上距版心下边缘 7mm。Word 的「页脚距边界」量的是页脚底边到页面底边，
# 一字线在这一行的中间，故要从地脚里再扣掉半个 4 号字高（14pt ≈ 4.94mm）。
DASH_ABOVE_CORE_MM = 7
FOUR_MM = SIZE_PT["four"] * 25.4 / 72
FOOTER_FROM_BOTTOM_MM = PAGE_MM["bottom"] - DASH_ABOVE_CORE_MM - FOUR_MM / 2


def _chars_to_twips(char_hundredths: int, size_pt: float = SIZE_PT["three"]) -> int:
    """w:*Chars（百分之一字）→ twips，给只认 w:left/w:hanging 的渲染器兜底。"""
    return int(char_hundredths / 100 * size_pt * 20)


def _mm(value: float) -> Twips:
    """毫米 → OOXML twips（1mm = 1440/25.4 twips）。"""
    return Twips(round(value * 1440 / 25.4))


def _mm_to_pt(value_mm: float) -> float:
    """毫米 → 磅（1mm = 72/25.4 磅），给以磅计的分隔线厚度用。"""
    return value_mm * 72 / 25.4


def _apply_page_setup(doc: DocxDocument) -> None:
    section = doc.sections[0]
    section.page_width = _mm(PAGE_MM["width"])
    section.page_height = _mm(PAGE_MM["height"])
    section.top_margin = _mm(PAGE_MM["top"])
    section.bottom_margin = _mm(PAGE_MM["bottom"])
    section.left_margin = _mm(PAGE_MM["left"])
    section.right_margin = _mm(PAGE_MM["right"])


def _set_font(run, east_asia: str, size_pt: float) -> None:
    """run 级显式字体：中文走 w:rFonts/@w:eastAsia，西文走 ascii，保留任何 w:color。"""
    run.font.name = FONT["ascii"]
    run.font.size = Pt(size_pt)
    run._element.rPr.rFonts.set(qn("w:eastAsia"), east_asia)


def _add_flag_paragraph(doc: DocxDocument, text: str) -> None:
    """10.3 纪要标志：居中红色小标宋，上边缘距版心上边缘 35mm（D2 字面读法）。"""
    para = doc.add_paragraph()
    run = para.add_run(text)
    _set_font(run, FONT["flag"], SIZE_PT["two"])
    run.font.color.rgb = RGBColor.from_string(FLAG_COLOR)
    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    fmt = para.paragraph_format
    fmt.line_spacing = Pt(LINE_PT)
    fmt.space_before = _mm(FLAG_TOP_MM)


def _bottom_border(color: str, width_pt: float):
    """一个只带下边框的 w:pBdr：单线、指定色与粗、贴着文字（w:space=0）。"""
    pbdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), str(round(width_pt * 8)))  # w:sz 以 1/8 磅计
    bottom.set(qn("w:space"), "0")
    bottom.set(qn("w:color"), color)
    pbdr.append(bottom)
    return pbdr


def _add_head_rule(doc: DocxDocument) -> None:
    """D6：版头红色分隔线。空段落画下边框；与版心等宽靠「不加任何缩进」保证。"""
    para = doc.add_paragraph()
    p_pr = para._p.get_or_add_pPr()
    # w:pBdr 在 CT_PPr 的模式里排在 w:spacing 之前，python-docx 未建模它，只能手动插到首位。
    p_pr.insert(0, _bottom_border(FLAG_COLOR, HEAD_RULE_PT))
    spacing = p_pr.get_or_add_spacing()
    spacing.set(qn("w:beforeLines"), str(HEAD_RULE_BLANK_LINES * 100))
    spacing.set(qn("w:before"), str(int(LINE_PT * HEAD_RULE_BLANK_LINES * 20)))
    spacing.set(qn("w:line"), str(int(LINE_PT * 20)))
    spacing.set(qn("w:lineRule"), "exact")


def _add_colophon_rule(doc: DocxDocument, width_mm: float) -> None:
    """7.4.1 的一条版记分隔线：空段下边框，靠「不加缩进」与版心等宽。"""
    para = doc.add_paragraph()
    p_pr = para._p.get_or_add_pPr()
    p_pr.insert(0, _bottom_border(COLOPHON_RULE_COLOR, _mm_to_pt(width_mm)))
    spacing = p_pr.get_or_add_spacing()
    spacing.set(qn("w:line"), str(int(COLOPHON_RULE_LINE_PT * 20)))
    spacing.set(qn("w:lineRule"), "exact")


def _add_body_paragraph(doc: DocxDocument, text: str) -> None:
    para = doc.add_paragraph()
    for pattern, font in LEVEL_PATTERNS:
        match = pattern.match(text)
        if not match:
            continue
        number = match.group(0)
        _set_font(para.add_run(number), font, SIZE_PT["three"])
        _set_font(para.add_run(text[len(number) :]), FONT["body"], SIZE_PT["three"])
        break
    else:
        _set_font(para.add_run(text), FONT["body"], SIZE_PT["three"])
    para.paragraph_format.line_spacing = Pt(LINE_PT)
    para.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    ind = para._p.get_or_add_pPr().get_or_add_ind()
    ind.set(qn("w:firstLineChars"), str(FIRST_LINE_CHARS))
    ind.set(qn("w:firstLine"), str(int(SIZE_PT["three"] * 2 * 20)))


def _add_blank_line(doc: DocxDocument) -> None:
    """占满一个 29 磅行的空段：国标多处「××下空一行」用的就是它。"""
    para = doc.add_paragraph()
    para.paragraph_format.line_spacing = Pt(LINE_PT)


def _roster_names(people: list[dict]) -> str:
    """逐人「单位 姓名」，人与人之间用顿号（spec §8 C1 的粒度）。整行空白不算一条。"""
    pairs = [((p.get("org") or "").strip(), (p.get("name") or "").strip()) for p in people]
    return "、".join(f"{org} {name}".strip() for org, name in pairs if org or name)


def _first_nameless(data: dict) -> tuple[str, int] | None:
    """第一个填了单位却没填姓名的人，返回 (中文标签, 第几人)。

    10.3 要「标注出席人单位、姓名」，缺姓名就排不出合格的一条；只填姓名不填单位仍算合格，
    单位不明的实际情况在样例里存在，故不挡。
    """
    for key, label in ROSTER_BLOCKS:
        for i, person in enumerate(data.get(key, []), start=1):
            org = (person.get("org") or "").strip()
            name = (person.get("name") or "").strip()
            if org and not name:
                return label, i
    return None


def _add_hanging_paragraph(
    doc: DocxDocument,
    pieces: list[tuple[str, str]],
    first_chars: int,
    wrap_chars: int,
    size_pt: float = SIZE_PT["three"],
    right_chars: int | None = None,
) -> None:
    """悬挂缩进段：首行落在 first_chars 字位，回行落到 wrap_chars 字位（均为百分之一字）。"""
    para = doc.add_paragraph()
    for text, font in pieces:
        _set_font(para.add_run(text), font, size_pt)
    para.paragraph_format.line_spacing = Pt(LINE_PT)
    hanging = wrap_chars - first_chars
    ind = para._p.get_or_add_pPr().get_or_add_ind()
    ind.set(qn("w:leftChars"), str(wrap_chars))
    ind.set(qn("w:left"), str(_chars_to_twips(wrap_chars, size_pt)))
    ind.set(qn("w:hangingChars"), str(hanging))
    ind.set(qn("w:hanging"), str(_chars_to_twips(hanging, size_pt)))
    if right_chars is not None:
        ind.set(qn("w:rightChars"), str(right_chars))
        ind.set(qn("w:right"), str(_chars_to_twips(right_chars, size_pt)))


def _add_roster_paragraph(doc: DocxDocument, label: str, names: str) -> None:
    _add_hanging_paragraph(
        doc,
        [(f"{label}：", FONT["heiti"]), (names, FONT["body"])],
        FIRST_LINE_CHARS,
        ROSTER_LEFT_CHARS,
    )


def _add_cc_paragraph(doc: DocxDocument, orgs: list[str]) -> None:
    """7.4.2：抄送在印发机关与印发日期之上一行，左右各空一字，末名后句号。"""
    _add_hanging_paragraph(
        doc,
        [(f"{CC_LABEL}：{'、'.join(orgs)}。", FONT["body"])],
        CC_LEFT_CHARS,
        CC_WRAP_CHARS,
        SIZE_PT["four"],
        CC_RIGHT_CHARS,
    )


def _print_date_text(value: date | None) -> str:
    """7.3.5.4：年、月、日用阿拉伯数字标全，月与日不编虚位；末尾按 7.4.3 补「印发」。"""
    return "" if value is None else f"{value.year}年{value.month}月{value.day}日{PRINT_SUFFIX}"


def _add_tabbed_paragraph(doc: DocxDocument, pieces: list[str], size_pt: float) -> None:
    """每个要素前跳一个制表位：左停在一字位（机关左空一字），右停在版心宽减一字位（日期右空一字）。

    不用空格硬顶，也不用整段右对齐：空格随字号错位，右对齐会把机关一起推走（7.4.3）。
    """
    para = doc.add_paragraph()
    one_char_twips = int(size_pt * 20)
    stops = para.paragraph_format.tab_stops
    stops.add_tab_stop(Twips(one_char_twips), WD_TAB_ALIGNMENT.LEFT)
    stops.add_tab_stop(Twips(_mm(CORE_WIDTH_MM).twips - one_char_twips), WD_TAB_ALIGNMENT.RIGHT)
    for text in pieces:
        run = para.add_run()
        run._r.append(OxmlElement("w:tab"))
        _set_font(run, FONT["body"], size_pt)
        run.add_text(text)
    para.paragraph_format.line_spacing = Pt(LINE_PT)


def _add_print_paragraph(doc: DocxDocument, org: str, value: date | None) -> None:
    _add_tabbed_paragraph(doc, [p for p in (org, _print_date_text(value)) if p], SIZE_PT["four"])


def _add_colophon(doc: DocxDocument, cc_orgs: list[str], print_org: str, print_date: date | None) -> None:
    """7.4 版记：首末粗线夹住要素，两要素之间压一条细线（7.4.1）。"""
    has_cc = bool(cc_orgs)
    has_print = bool(print_org or print_date)
    if not (has_cc or has_print):
        return
    _add_colophon_rule(doc, COLOPHON_THICK_MM)
    if has_cc:
        _add_cc_paragraph(doc, cc_orgs)
    if has_cc and has_print:
        _add_colophon_rule(doc, COLOPHON_THIN_MM)
    if has_print:
        _add_print_paragraph(doc, print_org, print_date)
    _add_colophon_rule(doc, COLOPHON_THICK_MM)


def _add_page_text_run(para, text: str) -> None:
    """页码两侧的一字线：4 号宋体。"""
    _set_font(para.add_run(text), FONT["song"], SIZE_PT["four"])


def _add_page_field(para) -> None:
    """PAGE 域。写 w:dirty 让 Word 打开即重算，于是不必缓存结果，页码也不会是字面量「1」。"""
    run = para.add_run()
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    begin.set(qn("w:dirty"), "true")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = " PAGE "
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    for element in (begin, instr, end):
        run._r.append(element)
    _set_font(run, FONT["song"], SIZE_PT["four"])


def _add_page_footer(footer, side: str, align: WD_ALIGN_PARAGRAPH) -> None:
    """一套页码页脚：「— 数字 —」，段落在奇偶页各贴一边并空出一字（7.5 单右双左）。"""
    footer.is_linked_to_previous = False
    para = footer.paragraphs[0]
    para.alignment = align
    ind = para._p.get_or_add_pPr().get_or_add_ind()
    ind.set(qn(f"w:{side}Chars"), str(PAGE_EDGE_CHARS))
    ind.set(qn(f"w:{side}"), str(_chars_to_twips(PAGE_EDGE_CHARS, SIZE_PT["four"])))
    _add_page_text_run(para, f"{PAGE_DASH} ")
    _add_page_field(para)
    _add_page_text_run(para, f" {PAGE_DASH}")


def _apply_page_numbers(doc: DocxDocument) -> None:
    """7.5 页码：奇偶页各排一套页脚是「单页码居右、双页码居左」的前提。

    国标不给空白页编页码。本模块正文、附件与版记连续流动，既不插分页符也不分节，
    所以不会多出空白页——这条前提由 tests/test_meeting_minutes.py::test_nothing_forces_a_blank_page 钉住。
    """
    doc.settings.odd_and_even_pages_header_footer = True
    section = doc.sections[0]
    section.footer_distance = _mm(FOOTER_FROM_BOTTOM_MM)
    _add_page_footer(section.footer, "right", WD_ALIGN_PARAGRAPH.RIGHT)
    _add_page_footer(section.even_page_footer, "left", WD_ALIGN_PARAGRAPH.LEFT)


def build_minutes(data: dict, out_path: str) -> ServiceResult[None]:
    """按纪要格式生成 DOCX 并保存到 out_path。

    版式参数逐条来自 spec §5；层级字体（002）、名单（003）、附件（004）、
    版记（005）、页码（006）各由一条工单落地。
    """
    incomplete = _first_nameless(data)
    if incomplete:
        return ServiceResult.fail(
            ErrorCode.VALIDATION_ERROR,
            _l("%(label)s list entry %(index)s has a unit but no name", label=incomplete[0], index=incomplete[1]),
        )
    doc = Document()
    _apply_page_setup(doc)
    _apply_page_numbers(doc)
    _add_flag_paragraph(doc, f"{data['meet_name']}纪要")
    _add_head_rule(doc)
    for text in data.get("paragraphs", []):
        if text.strip():
            _add_body_paragraph(doc, text.strip())
    attachments = [a.strip().rstrip(NAME_TRAILING_PUNCTUATION) for a in data.get("attachments", []) if a.strip()]
    if attachments:
        _add_blank_line(doc)
        single = len(attachments) == 1
        for i, name in enumerate(attachments, start=1):
            label = f"{ATTACH_LABEL}：" if i == 1 else ""
            number = "" if single else f"{i}. "
            first_chars = FIRST_LINE_CHARS if single or i == 1 else ATTACH_WRAP_CHARS
            wrap_chars = ATTACH_WRAP_CHARS if single else ATTACH_NUMBERED_WRAP_CHARS
            _add_hanging_paragraph(doc, [(f"{label}{number}{name}", FONT["body"])], first_chars, wrap_chars)
    filled = [(label, _roster_names(data.get(key, []))) for key, label in ROSTER_BLOCKS]
    filled = [(label, names) for label, names in filled if names]
    if filled:
        _add_blank_line(doc)
        for label, names in filled:
            _add_roster_paragraph(doc, label, names)
    cc_orgs = [o.strip() for o in data.get("cc_orgs", []) if o.strip()]
    print_org = (data.get("print_org") or "").strip()
    _add_colophon(doc, cc_orgs, print_org, data.get("print_date"))
    doc.save(out_path)
    return ServiceResult.ok(None)
