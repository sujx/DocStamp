"""会议纪要生成（第 16 个工具）后端回归。

工单 001 覆盖示踪弹：会议名称 + 正文 → 一份骨架合规的 DOCX，响应结束即删。
层级字体（002）、名单（003）、附件（004）、版记（005）、页码（006）各自一条工单。
"""

import os
from urllib.parse import unquote

import pytest

from tests.helpers_docx import (
    alignment,
    ascii_font,
    attr_of,
    border,
    east_asia_font,
    field_instruction,
    first_run,
    footer_paragraph,
    forced_page_breaks,
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

ENDPOINT = "/api/v1/meeting-minutes"
MEET_NAME = "信息技术中心例会"
FLAG = "信息技术中心例会纪要"
BODY = "本次会议议定了三项工作。"


def _payload(meet_name=MEET_NAME, body=(BODY,), rosters=None, attachments=None, colophon=None):
    return {
        "meet_name": meet_name,
        "paragraphs": list(body),
        **({"attachments": list(attachments)} if attachments else {}),
        **(rosters or {}),
        **(colophon or {}),
    }


def _doc(client, **kwargs):
    """提交一次生成请求，返回读自响应字节的 Document。"""
    return open_docx(client.post(ENDPOINT, json=_payload(**kwargs)).data)


def _post(client, payload, lang="zh-CN,zh;q=0.9,en;q=0.8"):
    """带 Accept-Language 提交一次生成请求；payload 覆盖在合法样例之上。"""
    return client.post(ENDPOINT, json={**_payload(), **payload}, headers={"Accept-Language": lang})


def _msg(r) -> str:
    """错误响应里的消息：全局 handler 用 msg，蓝图出口用 error。"""
    body = r.get_json() or {}
    return body.get("msg") or body.get("error") or ""


def _rule(doc):
    """带下分隔线的那个段落（版头红线）。"""
    for p in paragraphs(doc):
        if border(p, "w:bottom", "w:val") is not None:
            return p
    raise AssertionError("产物里没有带下分隔线的段落")


class TestTracerBullet:
    def test_valid_request_returns_an_openable_docx(self, client):
        r = client.post(ENDPOINT, json=_payload())
        assert r.status_code == 200
        assert any(p.text for p in open_docx(r.data).paragraphs)

    def test_download_name_is_meeting_minutes_not_uuid(self, client):
        r = client.post(ENDPOINT, json=_payload(meet_name=MEET_NAME))
        assert "信息技术中心例会纪要.docx" in unquote(r.headers["Content-Disposition"])

    def test_artifact_is_gone_once_the_response_is_back(self, app, client):
        r = client.post(ENDPOINT, json=_payload())
        assert r.status_code == 200
        docx_leftovers = [f for f in os.listdir(app.config["UPLOAD_FOLDER"]) if f.endswith(".docx")]
        assert docx_leftovers == []


class TestPageSetup:
    """5.2.1：A4，天头 37 / 地脚 35 / 订口 28 / 切口 26 mm → 版心 156×225 mm。"""

    def test_a4_sheet(self, client):
        pg_sz, _pg_mar = page_setup(_doc(client))
        assert mm(pg_sz, "w:w") == pytest.approx(210, abs=0.1)
        assert mm(pg_sz, "w:h") == pytest.approx(297, abs=0.1)

    @pytest.mark.parametrize(
        "attr,expected",
        [("w:top", 37), ("w:bottom", 35), ("w:left", 28), ("w:right", 26)],
    )
    def test_margins(self, client, attr, expected):
        _pg_sz, pg_mar = page_setup(_doc(client))
        assert mm(pg_mar, attr) == pytest.approx(expected, abs=0.1)


class TestHeadRule:
    """D6：标志下空二行，接一条与版心等宽的红色分隔线。

    10.3 未规定这条线，但 7.1 用「公文首页红色分隔线」划分版头与主体；国标也未定线粗，
    按钉死值取单位样例的 2.25 磅（sz=18，1/8 磅计）。
    """

    def test_rule_follows_the_flag_after_two_blank_lines(self, client):
        doc = _doc(client)
        ps = paragraphs(doc)
        assert ps.index(_rule(doc)) == ps.index(paragraph_containing(doc, FLAG)) + 1
        assert spacing(_rule(doc), "w:beforeLines") == 200
        assert spacing(_rule(doc), "w:before") == 1160  # 二行 = 2 × 29 磅 × 20

    def test_rule_is_a_single_red_2_25pt_line(self, client):
        p = _rule(_doc(client))
        assert border(p, "w:bottom", "w:val") == "single"
        assert border(p, "w:bottom", "w:sz") == "18"
        assert border(p, "w:bottom", "w:color") == "FF0000"
        assert border(p, "w:bottom", "w:space") == "0"

    def test_rule_has_no_side_indent_so_it_spans_the_core_area(self, client):
        p = _rule(_doc(client))
        for attr in ("w:left", "w:right", "w:leftChars", "w:rightChars"):
            assert indent(p, attr) is None


class TestBodyTypography:
    """5.2.2 / 5.2.3 / 7.3.3：3 号仿宋、固定 29 磅行距、左空二字且回行顶格。"""

    def test_body_uses_size_three_fangsong(self, client):
        run = first_run(paragraph_containing(_doc(client), BODY))
        assert east_asia_font(run) == "仿宋_GB2312"
        assert run_size_pt(run) == 16

    def test_body_line_spacing_is_fixed_29pt(self, client):
        p = paragraph_containing(_doc(client), BODY)
        assert spacing(p, "w:line") == 580  # 29pt × 20
        assert attr_of(p_child(p, "w:spacing"), "w:lineRule") == "exact"

    def test_body_is_justified(self, client):
        assert alignment(paragraph_containing(_doc(client), BODY)) == "both"

    def test_first_line_indents_two_chars_without_left_indent(self, client):
        """7.3.3「每个自然段左空二字，回行顶格」——只能用 firstLineChars，用 w:left 就是回行也缩进。"""
        p = paragraph_containing(_doc(client), BODY)
        assert indent(p, "w:firstLineChars") == 200
        assert indent(p, "w:left") is None
        assert indent(p, "w:leftChars") is None

    def test_blank_paragraphs_are_not_typeset(self, client):
        """空行不占行：产物里只有标志段 + 红线段 + 两个有内容的自然段。"""
        doc = _doc(client, body=("一、完成平台联调。", "", "   ", BODY))
        assert len(paragraphs(doc)) == 4


class TestMinutesFlag:
    """10.3 纪要格式第 1 条：标志 =「会议名称 + 纪要」，居中、红色小标宋，上边缘距版心上边缘 35mm。

    国标未规定标志字号，取二号（22 磅）小标宋 —— 与单位两份样例、`formatter.py` 的标题一致，
    属钉死值（D3 与 §7.3），故在此断言而不是任其随默认样式。
    """

    def test_flag_text_is_meeting_name_plus_minutes(self, client):
        p = paragraph_containing(_doc(client, meet_name="信息技术中心例会"), "信息技术中心例会纪要")
        assert text_of(p) == "信息技术中心例会纪要"

    def test_flag_is_red_xbs_at_size_two(self, client):
        run = first_run(paragraph_containing(_doc(client), FLAG))
        assert east_asia_font(run) == "方正小标宋简体"
        assert run_color(run) == "FF0000"
        assert run_size_pt(run) == 22

    def test_flag_is_centered(self, client):
        assert alignment(paragraph_containing(_doc(client), FLAG)) == "center"

    def test_flag_top_edge_sits_35mm_below_the_core_area(self, client):
        """D2：按 10.3 字面读法「上边缘至版心上边缘为 35mm」，即距页边 37 + 35 = 72mm。"""
        p = paragraph_containing(_doc(client), FLAG)
        assert mm(p_child(p, "w:spacing"), "w:before") == pytest.approx(35, abs=0.05)


class TestHierarchyFonts:
    """7.3.3 层次序号：一、→黑体，（一）→楷体，1./（1）→仿宋，均三号。"""

    def test_first_level_number_is_heiti(self, client):
        doc = _doc(client, body=("一、完成平台联调。",))
        run = first_run(paragraph_containing(doc, "一、完成平台联调。"))
        assert east_asia_font(run) == "黑体"
        assert run_size_pt(run) == 16

    def test_second_level_number_is_kaiti(self, client):
        doc = _doc(client, body=("（一）完成平台联调。",))
        run = first_run(paragraph_containing(doc, "（一）完成平台联调。"))
        assert east_asia_font(run) == "楷体_GB2312"
        assert run_size_pt(run) == 16

    def test_third_and_fourth_level_numbers_are_fangsong_in_their_own_run(self, client):
        """7.3.3 的「1./（1）→仿宋三号」：字体不变，但序号仍是独立 run。"""
        doc = _doc(client, body=("1. 完成平台联调。", "（1）编制值班表。"))
        for text in ("1. 完成平台联调。", "（1）编制值班表。"):
            para = paragraph_containing(doc, text)
            assert len(runs(para)) == 2, text
            assert [east_asia_font(r) for r in runs(para)] == ["仿宋_GB2312", "仿宋_GB2312"]
            assert [run_size_pt(r) for r in runs(para)] == [16, 16]

    def test_item_text_after_a_number_is_still_fangsong(self, client):
        doc = _doc(client, body=("一、完成平台联调。",))
        para = paragraph_containing(doc, "一、完成平台联调。")
        assert east_asia_font(runs(para)[-1]) == "仿宋_GB2312"
        assert text_of(runs(para)[-1]) == "完成平台联调。"

    def test_plain_paragraph_is_one_fangsong_run(self, client):
        doc = _doc(client, body=(BODY,))
        para = paragraph_containing(doc, BODY)
        assert [east_asia_font(r) for r in runs(para)] == ["仿宋_GB2312"]


ATTENDEE = [{"org": "信息技术中心", "name": "张三"}]


class TestRosters:
    """10.3 第 2、3 条：出席 / 请假 / 列席三块名单的行款。"""

    def test_attendee_line_hangs_so_wraps_align_after_the_colon(self, client):
        """回行顶格到「冒号后首字」= 左空二字 + 标签二字 + 全角冒号一字 = leftChars 500，首行回退 300。"""
        doc = _doc(client, rosters={"attendees": ATTENDEE})
        p = paragraph_containing(doc, "出席：")
        assert indent(p, "w:leftChars") == 500
        assert indent(p, "w:hangingChars") == 300

    def test_label_run_is_heiti_with_fullwidth_colon_and_names_run_is_fangsong(self, client):
        doc = _doc(client, rosters={"attendees": ATTENDEE})
        p = paragraph_containing(doc, "出席：")
        assert [east_asia_font(r) for r in runs(p)] == ["黑体", "仿宋_GB2312"]
        assert [text_of(r) for r in runs(p)] == ["出席：", "信息技术中心 张三"]

    def test_three_blocks_follow_standard_order_after_a_blank_line(self, client):
        doc = _doc(client, rosters={
            "attendees": ATTENDEE,
            "leave": [{"org": "综合处", "name": "李四"}],
            "witness": [{"org": "", "name": "王五"}],
        })
        texts = [text_of(p) for p in paragraphs(doc)]
        lines = [t for t in texts if t.startswith(("出席：", "请假：", "列席："))]
        assert lines == ["出席：信息技术中心 张三", "请假：综合处 李四", "列席：王五"]
        assert texts[texts.index(lines[0]) - 1] == ""

    def test_empty_roster_lists_produce_no_lines(self, client):
        """spec §6「留空即不排」：三块全空时一个名单段都不产出。"""
        doc = _doc(client)
        assert [t for t in map(text_of, paragraphs(doc)) if t[:2] in ("出席", "请假", "列席")] == []


class TestAttachments:
    """7.3.4：正文下空一行左空二字编排「附件：」，名称后不加标点，回行与名称首字对齐。"""

    def test_single_attachment_is_unnumbered_and_has_no_trailing_punctuation(self, client):
        doc = _doc(client, attachments=["某某统计表。"])
        p = paragraph_containing(doc, "附件：某某统计表")
        assert text_of(p) == "附件：某某统计表"
        assert indent(p, "w:leftChars") == 500
        assert indent(p, "w:hangingChars") == 300

    def test_multiple_attachments_are_numbered_once(self, client):
        """7.3.4 的写法：顺序号顶在「附件：」后首行的位置，后续行不重复「附件：」。"""
        doc = _doc(client, attachments=["某某统计表", "另一份清单"])
        texts = [text_of(p) for p in paragraphs(doc)]
        assert [t for t in texts if t.startswith(("附件", "2."))] == ["附件：1. 某某统计表", "2. 另一份清单"]
        assert indent(paragraph_containing(doc, "附件：1. 某某统计表"), "w:leftChars") == 700
        assert indent(paragraph_containing(doc, "附件：1. 某某统计表"), "w:hangingChars") == 500
        assert indent(paragraph_containing(doc, "2. 另一份清单"), "w:hangingChars") == 200

    def test_roster_block_yields_to_the_attachment_list(self, client):
        """10.3「在正文**或附件说明**下空一行」：有附件时名单块排在附件说明之下。"""
        doc = _doc(client, attachments=["某某统计表"], rosters={"attendees": ATTENDEE})
        raw = list(map(text_of, paragraphs(doc)))
        assert [t for t in raw if t] == [FLAG, BODY, "附件：某某统计表", "出席：信息技术中心 张三"]
        assert raw[raw.index("附件：某某统计表") - 1] == ""
        assert raw[raw.index("出席：信息技术中心 张三") - 1] == ""


CC_ORGS = ["综合处", "信息技术中心"]
PRINT_ORG = "信息技术中心综合处"
FOUR_PT = 14  # 4 号字（7.4.2 / 7.4.3）
CORE_WIDTH_MM = 156  # 5.2.1 版心宽 = 210 − 28 − 26


def _colophon_rules(doc):
    """版记的分隔线段落（黑线，w:color=auto），按文档顺序；版头那条红线不在此列。"""
    return [p for p in paragraphs(doc) if border(p, "w:bottom", "w:color") == "auto"]


class TestColophon:
    """7.4 版记：抄送机关 + 印发机关与印发日期，夹在三条分隔线之间。"""

    def test_cc_line_is_size_four_fangsong_and_ends_with_a_period(self, client):
        """7.4.2：4 号仿宋，最后一个抄送机关名称后标句号。"""
        doc = _doc(client, colophon={"cc_orgs": CC_ORGS})
        p = paragraph_containing(doc, "抄送：综合处、信息技术中心。")
        assert text_of(p) == "抄送：综合处、信息技术中心。"
        assert east_asia_font(first_run(p)) == "仿宋_GB2312"
        assert run_size_pt(first_run(p)) == 14

    def test_cc_block_is_one_char_in_on_both_sides_and_wraps_after_the_colon(self, client):
        """7.4.2「左右各空一字」+「回行时与冒号后的首字对齐」：400 = 1 空 + 抄送 2 + 冒号 1。"""
        p = paragraph_containing(_doc(client, colophon={"cc_orgs": CC_ORGS}), "抄送：")
        assert indent(p, "w:leftChars") == 400
        assert indent(p, "w:rightChars") == 100
        assert indent(p, "w:hangingChars") == 300

    def test_first_rule_sits_above_the_first_colophon_element_and_spans_the_core(self, client):
        """7.4.1：首条分隔线位于版记第一个要素之上，粗线 0.35mm（sz=8）、非红色；无缩进即与版心等宽。"""
        doc = _doc(client, colophon={"cc_orgs": CC_ORGS})
        ps = paragraphs(doc)
        rule = ps[ps.index(paragraph_containing(doc, "抄送：")) - 1]
        assert border(rule, "w:bottom", "w:sz") == "8"
        assert border(rule, "w:bottom", "w:color") == "auto"
        assert indent(rule, "w:left") is None
        assert indent(rule, "w:right") is None

    def test_print_line_is_size_four_and_appends_the_word_print(self, client):
        """7.4.3：印发机关与印发日期同段、4 号仿宋，日期后加「印发」二字。"""
        doc = _doc(client, colophon={"print_org": PRINT_ORG, "print_date": "2026-01-05"})
        p = paragraph_containing(doc, PRINT_ORG)
        assert text_of(p) == f"{PRINT_ORG}2026年1月5日印发"
        assert east_asia_font(first_run(p)) == "仿宋_GB2312"
        assert run_size_pt(first_run(p)) == 14

    def test_print_line_uses_tab_stops_not_hard_spaces(self, client):
        """7.4.3 的「左右各空一字」由制表位撑出：左停在一字位、右停在版心宽减一字位；段内无连续空格。"""
        doc = _doc(client, colophon={"print_org": PRINT_ORG, "print_date": "2026-01-05"})
        p = paragraph_containing(doc, PRINT_ORG)
        one_char = FOUR_PT * 20  # 4 号字宽，twips
        core_width = round(CORE_WIDTH_MM * 1440 / 25.4)
        assert tab_stops(p) == [("left", one_char), ("right", core_width - one_char)]
        assert "  " not in text_of(p)

    @pytest.mark.parametrize(
        "iso,expected",
        [("2026-01-05", "2026年1月5日"), ("2026-10-23", "2026年10月23日")],
    )
    def test_print_date_uses_arabic_digits_without_padded_month_or_day(self, client, iso, expected):
        """7.3.5.4：年月日用阿拉伯数字标全，月、日不编虚位（1 不编为 01）。"""
        doc = _doc(client, colophon={"print_org": PRINT_ORG, "print_date": iso})
        assert text_of(paragraph_containing(doc, PRINT_ORG)) == f"{PRINT_ORG}{expected}印发"

    def test_rules_bracket_the_elements_thick_thin_thick(self, client):
        """7.4.1：首条线在第一个要素之上、末条线在末要素之下，中间要素间一条细线。"""
        doc = _doc(client, colophon={"cc_orgs": CC_ORGS, "print_org": PRINT_ORG, "print_date": "2026-01-05"})
        assert [border(p, "w:bottom", "w:sz") for p in _colophon_rules(doc)] == ["8", "6", "8"]
        texts = list(map(text_of, paragraphs(doc)))
        assert texts[-5:] == ["", "抄送：综合处、信息技术中心。", "", f"{PRINT_ORG}2026年1月5日印发", ""]


class TestPageNumbers:
    """7.5：4 号半角宋体页码、数字左右各一条一字线、单页码居右空一字、双页码居左空一字。"""

    def test_odd_and_even_headers_switch_is_on(self, client):
        """奇偶页脚分开排的前提是 settings.xml 打开 w:evenAndOddHeaders。"""
        assert setting_on(_doc(client), "w:evenAndOddHeaders")

    def test_odd_page_number_sits_right_and_even_sits_left(self, client):
        """7.5：单页码居右空一字、双页码居左空一字。"""
        doc = _doc(client)
        odd, even = footer_paragraph(doc, "odd"), footer_paragraph(doc, "even")
        assert alignment(odd) == "right"
        assert indent(odd, "w:rightChars") == 100
        assert alignment(even) == "left"
        assert indent(even, "w:leftChars") == 100

    def test_page_number_is_a_field_between_two_one_char_dashes(self, client):
        """7.5：数字左右各放一条一字线，数字由 PAGE 域给出而不是手打的「1」。"""
        p = footer_paragraph(_doc(client), "odd")
        assert field_instruction(p) == "PAGE"
        assert text_of(p).count("—") == 2
        assert not any(ch.isdigit() for ch in text_of(p))

    def test_page_number_runs_are_size_four_song_with_halfwidth_digits(self, client):
        """7.5：页码整体 4 号——数字走半角西文字体，一字线与中文走宋体。"""
        for kind in ("odd", "even"):
            for run in runs(footer_paragraph(_doc(client), kind)):
                assert run_size_pt(run) == FOUR_PT
                assert ascii_font(run) == "Times New Roman"
                assert east_asia_font(run) == "宋体"

    def test_dashes_start_seven_mm_below_the_body(self, client):
        """7.5：一字线上距版心下边缘 7mm。

        「页脚距边界」量到页脚底边，一字线在这一行的中间，故期望值 = 地脚 35 − 7 − 半个 4 号字高
        （14pt = 4.94mm）= 25.53mm，手算自国标条文而不是从代码反推。
        """
        _, pg_mar = page_setup(_doc(client))
        assert mm(pg_mar, "w:footer") == pytest.approx(25.53, abs=0.02)

    def test_nothing_forces_a_blank_page(self, client):
        """7.5 不给空白页编页码；本产物不插分页符也不分节，故页码恒等于页序——钉住这个前提。"""
        doc = _doc(
            client,
            body=("一、议定事项。" * 30,) * 4,
            attachments=["信息技术中心统计表", "二、另表"],
            colophon={"cc_orgs": CC_ORGS, "print_org": PRINT_ORG, "print_date": "2026-01-05"},
        )
        assert forced_page_breaks(doc) == []


class TestValidation:
    """工单 007：非法输入挡在 422/400，且中文客户端看到的是中文。"""

    def test_blank_meeting_name_is_rejected_in_chinese(self, client):
        """会议名称空或全空格都不许生成——全空格剥掉后要一起挡掉。"""
        for name in ("", "   "):
            r = _post(client, {"meet_name": name})
            assert r.status_code == 422, name
            assert "为空" in _msg(r) or "不能为空" in _msg(r)
            assert _msg(r) != "Meeting name is required"
            assert r.headers["X-Request-Id"]

    def test_empty_body_is_rejected_in_chinese(self, client):
        """一段正文都没有（连空行也不算）就不能成文——10.3 的纪要必有正文要素。"""
        for body in ([], ["   ", "  "]):
            r = _post(client, {"paragraphs": body})
            assert r.status_code == 422, body
            assert "正文" in _msg(r)

    def test_overlong_meeting_name_is_rejected_with_the_limit(self, client):
        """标志一行放不下就把名称挡掉，并把上限一起回给用户，不用他猜。"""
        r = _post(client, {"meet_name": "会" * 51})
        assert r.status_code == 422
        assert "会议名称" in _msg(r) and "50" in _msg(r)

    def test_oversized_roster_is_rejected_with_the_limit(self, client):
        """名单长到四位数只可能是误粘贴——连单位一起挡在 DTO，不进服务层。"""
        people = [{"org": "综合处", "name": f"张三{i}"} for i in range(101)]
        r = _post(client, {"attendees": people, "leave": people, "witness": people})
        assert r.status_code == 422
        assert "名单" in _msg(r) and "100" in _msg(r)

    def test_roster_entry_without_a_name_is_rejected_in_chinese(self, client):
        """10.3 要「标注出席人单位、姓名」：只填单位排不出姓名，业务层直接拒。"""
        r = _post(client, {"attendees": [{"org": "综合处", "name": ""}]})
        assert r.status_code == 400
        assert "出席" in _msg(r) and "姓名" in _msg(r)
        assert r.headers["X-Request-Id"]

    def test_out_of_range_print_date_is_rejected_in_chinese(self, client):
        """月/日越界的日期在类型转换处就挡下，但回的是一句中文，不是 pydantic 的英文长句。"""
        for bad in ("2026-13-45", "not-a-date"):
            r = _post(client, {"print_date": bad})
            assert r.status_code == 422, bad
            assert "印发日期" in _msg(r)

    def test_unknown_field_is_rejected_instead_of_silently_dropped(self, client):
        """字段名是前后端的一对一约定：`witness` 拼错不得变成「列席块静默不排」。

        pydantic 默认忽略未知键，所以这条断言钉的是 `extra="forbid"` 还开着。
        """
        r = _post(client, {"witnesss": [{"org": "综合处", "name": "张三"}]})
        assert r.status_code == 422, _msg(r)
        # 回的是 pydantic 原话（字段名只在 loc 里，全局 handler 不取）：这条面向的是
        # 改前后端约定的开发者，不是表单用户——用户能碰到的非法输入都有中文词条。
        assert _msg(r) == "Extra inputs are not permitted"

    def test_english_client_gets_the_msgid_back(self, client):
        """同一批校验消息在 en 客户端回英文原句——词条只影响 zh。"""
        r = _post(client, {"meet_name": ""}, lang="en")
        assert r.status_code == 422
        assert _msg(r) == "Meeting name is required"


class TestStatsRegistration:
    """工单 008：新工具要在 /status 的「按模块调用量」里数得出来。"""

    def test_a_generation_shows_up_in_module_counts(self, client):
        """MODULE_NAMES 少一项，审计行就被 aggregate_by_module 静默丢弃。

        从 HTTP 两端一起验，顺带钉住 app.py 的 operation_type 确实取自 URL 第 3 段。
        """
        assert client.post(ENDPOINT, json=_payload()).status_code == 200
        by_module = client.get("/api/v1/stats/overview").get_json()["data"]["by_module"]
        matched = [m for m in by_module if m["module"] == "meeting-minutes"]
        assert matched, by_module
        assert matched[0]["label"] == "会议纪要整理"
        assert matched[0]["count"] >= 1
