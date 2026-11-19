"""GB/T 9704—2012 规格符合性断言集（工单 009）。

设计蓝本 §5 版式参数表的每一行在这里都是一条能单独跑、单独红的断言：

    uv run pytest tests/test_minutes_gb_conformance.py -q -k "5.2.3"

失败信息一律以条款号开头，改动后不必回读 spec 就知道违反了哪一条。
一份「填满所有字段」的产物只生成一次（模块级 fixture），15 条断言读它的 XML。
"""

import re
from datetime import date

import pytest

from services.minutes_docx import PAGE_DASH, build_minutes
from tests.helpers_docx import (
    alignment,
    ascii_font,
    attr_of,
    border,
    east_asia_font,
    field_instruction,
    first_run,
    footer_paragraph,
    indent,
    mm,
    open_docx,
    p_child,
    page_setup,
    paragraph_containing,
    paragraphs,
    run_color,
    run_size_pt,
    runs,
    setting_on,
    spacing,
    tab_stops,
    text_of,
)

MEET_NAME = "信息技术中心周例会"
FLAG = f"{MEET_NAME}纪要"

# 每一层都填上：标志、四种层次序号、三段名单、带序号的附件、两个抄送机关、印发机关与日期。
FILLED = {
    "meet_name": MEET_NAME,
    "paragraphs": [
        "本次会议议定了三项工作安排，具体如下。",
        "一、关于卫星业务的年度目标",
        "（一）目标分解到季度",
        "1. 第一季度完成组网验证",
        "（1）验证方案由综合处牵头",
    ],
    "attendees": [{"org": "综合处", "name": "张三"}, {"org": "信息技术中心", "name": "李四"}],
    "leave": [{"org": "信息技术中心", "name": "赵六"}],
    "witness": [{"org": "财务处", "name": "王五"}],
    # 末尾标点由用户手打，7.3.4 要求生成时剥掉——放进输入才验得到。
    "attachments": ["卫星业务年度目标表。", "组网验证方案，"],
    "cc_orgs": ["综合处", "财务处"],
    "print_org": "信息技术中心",
    "print_date": None,  # 由 fixture 填 date(2026, 1, 5)，7.3.5.4 要求不编虚位
}


@pytest.fixture(scope="module")
def filled_doc(tmp_path_factory):
    """填满所有字段的产物，读一次 XML 供 15 条断言共用。"""
    out = str(tmp_path_factory.mktemp("gb") / "filled.docx")
    result = build_minutes({**FILLED, "print_date": date(2026, 1, 5)}, out)
    assert result.success, result.message
    with open(out, "rb") as handle:
        return open_docx(handle.read())


# ── §5 表逐行核对 ───────────────────────────────────────────────────────


def _page(doc) -> None:
    """5.2.1：A4 210×297；天头 37 / 地脚 35 / 订口 28 / 切口 26 → 版心 156×225。"""
    pg_sz, pg_mar = page_setup(doc)
    assert mm(pg_sz, "w:w") == pytest.approx(210, abs=0.1), "页面宽不是 210mm"
    assert mm(pg_sz, "w:h") == pytest.approx(297, abs=0.1), "页面高不是 297mm"
    margins = {attr: mm(pg_mar, attr) for attr in ("w:top", "w:bottom", "w:left", "w:right")}
    assert margins["w:top"] == pytest.approx(37, abs=0.1), margins
    assert margins["w:bottom"] == pytest.approx(35, abs=0.1), margins
    assert margins["w:left"] == pytest.approx(28, abs=0.1), margins
    assert margins["w:right"] == pytest.approx(26, abs=0.1), margins
    assert 210 - margins["w:left"] - margins["w:right"] == pytest.approx(156, abs=0.2), "版心宽不是 156mm"
    assert 297 - margins["w:top"] - margins["w:bottom"] == pytest.approx(225, abs=0.2), "版心高不是 225mm"


def _default_font(doc) -> None:
    """5.2.2：默认字体 3 号仿宋体——正文每个 run 都显式带 eastAsia 字体与 16pt。"""
    body = paragraph_containing(doc, "本次会议议定了三项工作安排")
    for run in runs(body):
        assert east_asia_font(run) == "仿宋_GB2312", f"正文 run 字体不是仿宋：{east_asia_font(run)}"
        assert run_size_pt(run) == 16, f"正文 run 字号不是 3 号：{run_size_pt(run)}pt"


def _line_spacing(doc) -> None:
    """5.2.3：一般每面排 22 行 → 版心高 225mm ÷ 22 = 固定 29 磅行距（w:line=580 + exact）。

    逐个有文字的段落都读，不只读第一段——「正文行距对了、名单行距漏了」这种改动
    在本文件里必须红。不带文字的分隔线段落不在这条范围内：版记三条只撑 1 磅，
    免得一条线多吃一个 29 磅行（工单 005）。
    """
    texted = [p for p in paragraphs(doc) if text_of(p)]
    for para in texted:
        head = text_of(para)[:12]
        assert spacing(para, "w:line") == 580, f"「{head}…」行距不是 29 磅：{spacing(para, 'w:line')}"
        assert attr_of(p_child(para, "w:spacing"), "w:lineRule") == "exact", f"「{head}…」不是固定行距而是倍数"


def _black_except_flag(doc) -> None:
    """5.2.4：全黑，只有纪要标志是红——除标志段外，任何 run 都不许带 w:color。

    这条是「不复用 formatter.py」（它会删掉 w:color）的长期保险：
    哪天有人把上色逻辑挪进公共助手，这里先红。
    """
    colored = [
        (text_of(p)[:20], run_color(run))
        for p in paragraphs(doc)
        if text_of(p) != FLAG
        for run in runs(p)
        if run_color(run) is not None
    ]
    assert colored == [], f"标志之外还有带颜色的 run：{colored}"


def _flag(doc) -> None:
    """10.3 + D2：标志是「×××纪要」，居中、二号红色小标宋，上边缘距版心 35mm。"""
    para = paragraph_containing(doc, FLAG)
    assert text_of(para) == FLAG, f"标志文本不止「{FLAG}」：{text_of(para)!r}"
    assert alignment(para) == "center", "标志没居中"
    run = first_run(para)
    assert east_asia_font(run) == "方正小标宋简体", east_asia_font(run)
    assert run_size_pt(run) == 22, f"标志不是二号：{run_size_pt(run)}pt"
    assert run_color(run) == "FF0000", f"标志不是红色：{run_color(run)}"
    assert mm(p_child(para, "w:spacing"), "w:before") == pytest.approx(35, abs=0.1), "标志上边缘距版心不是 35mm"


def _head_rule(doc) -> None:
    """D6：标志下空二行接一条与版心等宽的红色分隔线，2.25 磅（w:sz 以 1/8 磅计 = 18）。"""
    rules = [p for p in paragraphs(doc) if p_child(p, "w:pBdr") is not None]
    rule = rules[0]
    assert border(rule, "w:bottom", "w:val") == "single", "版头线不是单线"
    assert border(rule, "w:bottom", "w:sz") == "18", "版头线不是 2.25 磅"
    assert border(rule, "w:bottom", "w:color") == "FF0000", "版头线不是红色"
    assert p_child(rule, "w:ind") is None, "版头线有缩进就不与版心等宽"
    assert spacing(rule, "w:beforeLines") == 200, "标志与版头线之间不是空二行"


# 正文的五个自然段，覆盖四个层次序号层级；按全文精确匹配定位，不靠段落序号。
BODY_TEXTS = [
    "本次会议议定了三项工作安排，具体如下。",
    "一、关于卫星业务的年度目标",
    "（一）目标分解到季度",
    "1. 第一季度完成组网验证",
    "（1）验证方案由综合处牵头",
]

# 版记两行的整段文本（印发行的制表符不进 w:t，故机关与日期直接相连）。
CC_TEXT = "抄送：综合处、财务处。"
PRINT_TEXT = "信息技术中心2026年1月5日印发"

# 7.3.3 层次序号 → 序号 run 的字体（条目剩余部分一律回到仿宋）。
LEVEL_NUMBER_FONTS = [
    ("一、", "黑体"),
    ("（一）", "楷体_GB2312"),
    ("1.", "仿宋_GB2312"),
    ("（1）", "仿宋_GB2312"),
]


def _index_of(doc, text: str) -> int:
    """整段文本等于 text 的段落序号；读不到直接失败，断言不许静默跳过。"""
    for i, para in enumerate(paragraphs(doc)):
        if text_of(para) == text:
            return i
    raise AssertionError(f"产物里没有整段文本等于 {text!r} 的段落")


def _by_text(doc, text: str):
    """整段文本等于 text 的段落元素。"""
    return paragraphs(doc)[_index_of(doc, text)]


def _body(doc) -> None:
    """7.3.3：每个自然段首行左空二字（200），回行顶格——靠全程不写 w:left/w:leftChars。"""
    for text in BODY_TEXTS:
        para = _by_text(doc, text)
        assert indent(para, "w:firstLineChars") == 200, f"{text[:12]}… 首行不是左空二字"
        assert indent(para, "w:left") is None, f"{text[:12]}… 写了 w:left，回行就不顶格"
        assert indent(para, "w:leftChars") is None, f"{text[:12]}… 写了 w:leftChars，回行就不顶格"
        assert alignment(para) == "both", f"{text[:12]}… 不是两端对齐"


def _level_fonts(doc) -> None:
    """7.3.3：一、→黑体，（一）→楷体，1. 与（1）→仿宋；序号之后的文字仍是 3 号仿宋。"""
    for number, font in LEVEL_NUMBER_FONTS:
        text = next(t for t in BODY_TEXTS if t.startswith(number))
        para = _by_text(doc, text)
        head = runs(para)[0]
        assert text_of(head) == number, f"{number} 的序号 run 文本被改动：{text_of(head)!r}"
        assert east_asia_font(head) == font, f"{number} 的序号字体不是 {font}：{east_asia_font(head)}"
        assert east_asia_font(runs(para)[1]) == "仿宋_GB2312", f"{number} 之后的条目正文不是仿宋"
        for run in runs(para):
            assert run_size_pt(run) == 16, f"{number} 所在段出现非 3 号 run：{run_size_pt(run)}pt"


def _blank_line_above(doc, index: int, label: str) -> None:
    """国标多处「××下空一行」：被标注段之前必须是一个空段，且高度等于一个正文行。

    这里刻意不写死 580——行距的绝对值归 5.2.3 那条断言，本条只管「确实空了一整行」。
    """
    prev = paragraphs(doc)[index - 1]
    assert text_of(prev) == "", f"{label} 之前不是空行，而是 {text_of(prev)!r}"
    body = _by_text(doc, BODY_TEXTS[0])
    blank, texted = spacing(prev, "w:line"), spacing(body, "w:line")
    assert blank == texted, f"{label} 之前的空行没占满一个正文行：{blank} vs {texted}"


def _rosters(doc) -> None:
    """10.3 + D3：出席/请假/列席各一段，标签 3 号黑体带全角冒号，名单 3 号仿宋。

    行款顺序固定出席→请假→列席；首行左空二字由 leftChars−hangingChars 得到，
    回行落在五字位（左空二字 + 标签二字 + 全角冒号一字），于是与冒号后首字对齐。
    """
    blocks = [
        ("出席：", "综合处 张三、信息技术中心 李四"),
        ("请假：", "信息技术中心 赵六"),
        ("列席：", "财务处 王五"),
    ]
    indexes = []
    for label, names in blocks:
        text = f"{label}{names}"
        index = _index_of(doc, text)
        indexes.append(index)
        para = paragraphs(doc)[index]
        head = runs(para)[0]
        assert text_of(head) == label, f"{label} 的标签 run 不止三个字：{text_of(head)!r}"
        assert east_asia_font(head) == "黑体", f"{label} 标签不是黑体：{east_asia_font(head)}"
        assert east_asia_font(runs(para)[1]) == "仿宋_GB2312", f"{names[:6]}… 名单不是仿宋"
        assert indent(para, "w:leftChars") == 500, f"{label} 回行不在五字位"
        assert indent(para, "w:hangingChars") == 300, f"{label} 首行没回退到二字位"
    # 「正文下空一行」管的是整块名单之前，三段名单之间不空行。
    _blank_line_above(doc, indexes[0], "出席/请假/列席")
    assert indexes == sorted(indexes), "名单行款顺序不是出席→请假→列席"


def _attachments(doc) -> None:
    """7.3.4：多个附件走「附件：1. ×××」，名称后的标点被剥掉，回行落在七字位。"""
    first_text = "附件：1. 卫星业务年度目标表"
    first = _by_text(doc, first_text)
    second = _by_text(doc, "2. 组网验证方案")
    assert indent(first, "w:leftChars") == 700, "首条附件回行不在七字位"
    assert indent(first, "w:hangingChars") == 500, "首条附件首行没回退到二字位"
    assert indent(second, "w:leftChars") == 700, "次条附件回行不在七字位"
    assert text_of(runs(first)[0]).startswith("附件："), "首条缺「附件：」标签"
    assert not text_of(second).startswith("附件"), "「附件：」标签重复出现在次条"
    for para in (first, second):
        assert text_of(para)[-1] not in "。；，、.;,", f"附件名称后带了标点：{text_of(para)!r}"
    _blank_line_above(doc, _index_of(doc, first_text), "附件")


def _print_date_digits(doc) -> None:
    """7.3.5.4：成文日期用阿拉伯数字标全，月与日不编虚位——2026 年 1 月 5 日写成「2026年1月5日」。"""
    text = text_of(paragraph_containing(doc, "印发"))
    match = re.search(r"(\d+)年(\d+)月(\d+)日", text)
    assert match, f"产物里没有阿拉伯数字式的成文日期：{text!r}"
    assert match.groups() == ("2026", "1", "5"), f"年月日不是标全且不编虚位：{match.groups()}"
    assert not re.search(r"年0\d月|月0\d日", text), f"月或日编了虚位：{text!r}"


def _colophon_rules(doc) -> None:
    """7.4.1：版记首末粗线、中间细线，全部与版心等宽、黑色。

    线厚国标按毫米给（0.35 / 0.25），`w:sz` 以 1/8 磅计故是 8 与 6。
    「末条线与版心下边缘重合」在 XML 里断不了——版记按文档流排在主体末尾，
    这条偏差已写进 SPEC v3.14.0，不在这里放宽。
    """
    rules = [p for p in paragraphs(doc) if p_child(p, "w:pBdr") is not None]
    colophon = rules[1:]
    assert len(colophon) == 3, f"版记分隔线不是粗-细-粗三条：{[border(p, 'w:bottom', 'w:sz') for p in colophon]}"
    assert [border(p, "w:bottom", "w:sz") for p in colophon] == ["8", "6", "8"], "版记线厚不是 0.35mm / 0.25mm / 0.35mm"
    for para in colophon:
        color = border(para, "w:bottom", "w:color")
        assert border(para, "w:bottom", "w:val") == "single", "版记线不是单线"
        assert color == "auto", f"版记线上了色，5.2.4 要求黑色：{color}"
        assert p_child(para, "w:ind") is None, "版记线有缩进就不与版心等宽"


def _cc(doc) -> None:
    """7.4.2：抄送 4 号仿宋，左右各空一字，回行与冒号后首字对齐，末名后句号。"""
    para = _by_text(doc, CC_TEXT)
    assert border(para, "w:bottom", "w:sz") is None, "抄送段自己带了边框"
    for run in runs(para):
        assert east_asia_font(run) == "仿宋_GB2312", f"抄送不是仿宋：{east_asia_font(run)}"
        assert run_size_pt(run) == 14, f"抄送不是 4 号：{run_size_pt(run)}pt"
    assert indent(para, "w:leftChars") == 400, "抄送回行不在四字位"
    assert indent(para, "w:hangingChars") == 300, "抄送首行没回退到一字位"
    assert indent(para, "w:rightChars") == 100, "抄送没有右空一字"
    assert _index_of(doc, CC_TEXT) < _index_of(doc, PRINT_TEXT), "抄送不在印发行之下"


def _print_line(doc) -> None:
    """7.4.3：印发机关左空一字、印发日期右空一字，用段内制表位而不是空格或右对齐。

    4 号字一字 = 14pt = 280 twips；版心宽 156mm = 8844 twips，故右制表位在 8564。
    """
    para = _by_text(doc, PRINT_TEXT)
    assert tab_stops(para) == [("left", 280), ("right", 8564)], f"制表位不是「左一字 / 右减一字」：{tab_stops(para)}"
    assert alignment(para) is None, "整段右对齐会把印发机关一起推走"
    assert text_of(runs(para)[0]) == "信息技术中心", "印发机关不在第一个要素位"
    assert text_of(runs(para)[1]).endswith("印发"), "印发日期后没有「印发」二字"
    for run in runs(para):
        assert east_asia_font(run) == "仿宋_GB2312", f"印发行不是仿宋：{east_asia_font(run)}"
        assert run_size_pt(run) == 14, f"印发行不是 4 号：{run_size_pt(run)}pt"


def _page_number(doc) -> None:
    """7.5：页码 4 号半角宋体，左右各一条一字线；单页码居右空一字、双页码居左空一字。

    「一字线上距版心下边缘 7mm」在 XML 里只能验到 `w:pgMar/@w:footer`——Word 量的是
    页脚**底边**到页面底边，故落点是 35 − 7 − 半个 4 号字高 = 25.53mm；LibreOffice
    实测墨迹上缘距版心下边缘 6.48mm，残余来自本机字体替换，须在 Word / WPS 复验。
    """
    assert setting_on(doc, "w:evenAndOddHeaders"), "没开奇偶页脚，双页码无从居左"
    _, pg_mar = page_setup(doc)
    assert mm(pg_mar, "w:footer") == pytest.approx(25.53, abs=0.05), "页脚底边距页面底不是 25.53mm"
    for kind, place, side in (("odd", "right", "w:rightChars"), ("even", "left", "w:leftChars")):
        para = footer_paragraph(doc, kind)
        assert alignment(para) == place, f"{kind} 页码没有居{place}"
        assert indent(para, side) == 100, f"{kind} 页码没有空一字"
        assert field_instruction(para) == "PAGE", f"{kind} 页码不是 PAGE 域"
        text = text_of(para)
        assert text.count(PAGE_DASH) == 2, f"{kind} 页码两侧不各有一条一字线：{text!r}"
        assert not any(ch.isdigit() for ch in text), f"{kind} 页码被缓存成了字面量：{text!r}"
        for run in runs(para):
            assert east_asia_font(run) == "宋体", f"{kind} 页码不是宋体：{east_asia_font(run)}"
            assert ascii_font(run) == "Times New Roman", f"{kind} 页码数字不是半角西文字体：{ascii_font(run)}"
            assert run_size_pt(run) == 14, f"{kind} 页码不是 4 号：{run_size_pt(run)}pt"


CHECKS = [
    ("5.2.1 页面", _page),
    ("5.2.2 默认字体", _default_font),
    ("5.2.3 行距", _line_spacing),
    ("5.2.4 文字颜色", _black_except_flag),
    ("10.3 纪要标志", _flag),
    ("D6 版头分隔线", _head_rule),
    ("7.3.3 正文左空二字、回行顶格", _body),
    ("7.3.3 层次序号字体", _level_fonts),
    ("10.3 出席/请假/列席", _rosters),
    ("7.3.4 附件说明", _attachments),
    ("7.3.5.4 成文日期数字", _print_date_digits),
    ("7.4.1 版记分隔线", _colophon_rules),
    ("7.4.2 抄送机关", _cc),
    ("7.4.3 印发机关与印发日期", _print_line),
    ("7.5 页码", _page_number),
]


@pytest.mark.parametrize("clause,check", CHECKS, ids=[clause for clause, _ in CHECKS])
def test_gb_conformance(clause, check, filled_doc):
    try:
        check(filled_doc)
    except AssertionError as error:
        raise AssertionError(f"{clause}（GB/T 9704—2012）：{error}") from error
