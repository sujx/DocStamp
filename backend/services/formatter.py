"""DOCX official document formatter per GB/T 9704-2012.

Post-processes a Pandoc-generated DOCX file to apply Chinese government
document formatting standards: page margins, fonts, line spacing, heading
detection, and page numbers.
"""

import re
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

from errors import ServiceResult


# ── Font configuration ──────────────────────────────────────────────
FONT_CONFIG = {
    "title": "方正小标宋简体",
    "heading1": "黑体",
    "heading2": "楷体_GB2312",
    "heading3": "仿宋_GB2312",
    "heading4": "仿宋_GB2312",
    "body": "仿宋_GB2312",
    "ascii": "Times New Roman",
    "page_num": "宋体",
}

# ── Font sizes in Pt ─────────────────────────────────────────────────
FONT_SIZES = {
    "title": Pt(22),         # 二号
    "heading": Pt(16),       # 三号
    "body": Pt(16),          # 三号
    "page_num": Pt(14),      # 四号
}

# ── Line spacing (fixed value in Pt) ────────────────────────────────
LINE_SPACING = Pt(28.6)

# ── Page margins in Cm ───────────────────────────────────────────────
PAGE_MARGINS = {
    "top": Cm(3.7),
    "bottom": Cm(3.5),
    "left": Cm(2.8),
    "right": Cm(2.6),
}

# ── Heading detection patterns ───────────────────────────────────────
HEADING_PATTERNS = [
    (re.compile(r"^[一二三四五六七八九十]{1,2}、"), "heading1"),
    (re.compile(r"^（[一二三四五六七八九十]{1,2}）"), "heading2"),
    (re.compile(r"^\d+[.．]"), "heading3"),
    (re.compile(r"^（\d+）"), "heading4"),
]

# ── Appendix detection ───────────────────────────────────────────────
APPENDIX_PATTERN = re.compile(r"^附件[:：]")


def _set_run_font(run, font_name: str, size: Pt, bold: bool = False):
    """Set font properties for a run, including East-Asian font."""
    run.font.name = font_name
    run.font.size = size
    run.bold = bold
    # Set East-Asian font
    rPr = run._element.get_or_add_rPr()
    # Remove any explicit color (from Pandoc styles or direct formatting)
    for color_elem in rPr.findall(qn("w:color")):
        rPr.remove(color_elem)
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = OxmlElement("w:rFonts")
        rPr.insert(0, rFonts)
    rFonts.set(qn("w:eastAsia"), font_name)
    rFonts.set(qn("w:ascii"), FONT_CONFIG["ascii"])
    rFonts.set(qn("w:hAnsi"), FONT_CONFIG["ascii"])


def _set_line_spacing(paragraph):
    """Set paragraph line spacing to fixed 28.6pt."""
    pPr = paragraph._element.get_or_add_pPr()
    spacing = pPr.find(qn("w:spacing"))
    if spacing is None:
        spacing = OxmlElement("w:spacing")
        pPr.append(spacing)
    spacing.set(qn("w:lineRule"), "exact")
    spacing.set(
        qn("w:line"),
        str(int(LINE_SPACING.pt * 20)),  # twips
    )


def _classify_paragraph(text: str) -> str:
    """Classify a paragraph by matching its text against heading patterns.

    Args:
        text: The paragraph text, stripped.

    Returns:
        One of 'heading1', 'heading2', 'heading3', 'heading4', or 'body'.
    """
    if not text:
        return "body"
    for pattern, level in HEADING_PATTERNS:
        if pattern.match(text):
            return level
    return "body"


def _add_page_field(run):
    """Append a PAGE field to a run."""
    fld_begin = OxmlElement("w:fldChar")
    fld_begin.set(qn("w:fldCharType"), "begin")
    run._element.append(fld_begin)

    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = " PAGE "
    run._element.append(instr)

    fld_end = OxmlElement("w:fldChar")
    fld_end.set(qn("w:fldCharType"), "end")
    run._element.append(fld_end)


def format_docx(docx_path: str) -> ServiceResult[None]:
    """Apply GB/T 9704-2012 formatting to a DOCX file in-place.

    Modifies the document at docx_path:
    - Page margins (3.7/3.5/2.8/2.6 cm)
    - Heading detection and font application
    - Body font (仿宋_GB2312, 16pt, first-line indent 2 chars)
    - Line spacing (fixed 28.6pt)
    - Text alignment (title centered, body justified)
    - Appendix (附件) detection with spacing
    - Page numbers with em-dash (一字线), odd/even alignment

    Args:
        docx_path: Path to the .docx file to format.

    Returns:
        ServiceResult with None on success.
    """
    doc = Document(docx_path)

    # ── 1. Set page margins for all sections ───────────────────────
    for section in doc.sections:
        section.top_margin = PAGE_MARGINS["top"]
        section.bottom_margin = PAGE_MARGINS["bottom"]
        section.left_margin = PAGE_MARGINS["left"]
        section.right_margin = PAGE_MARGINS["right"]

        # Document grid: 28 chars/line, 22 lines/page
        doc_grid = OxmlElement("w:docGrid")
        doc_grid.set(qn("w:type"), "linesAndChars")
        doc_grid.set(qn("w:linePitch"), "580")
        doc_grid.set(qn("w:charSpace"), "316")
        section._sectPr.append(doc_grid)

    # ── 2. Process paragraphs ──────────────────────────────────────
    paragraphs = list(doc.paragraphs)
    is_first_body = True

    for para in paragraphs:
        text = para.text.strip()

        # Skip empty paragraphs
        if not text:
            p_element = para._element
            p_element.getparent().remove(p_element)
            continue

        # Set line spacing
        _set_line_spacing(para)

        # ── Appendix detection ───────────────────────────────────
        if APPENDIX_PATTERN.match(text):
            # Insert an empty paragraph before appendix (空一行)
            p_element = para._element
            parent = p_element.getparent()
            empty_p = OxmlElement("w:p")
            parent.insert(list(parent).index(p_element), empty_p)

        # Classify the paragraph
        level = _classify_paragraph(text)

        # Determine if this is the document title
        is_title = is_first_body and level == "body"
        if is_first_body:
            is_first_body = False

        # Apply formatting based on classification
        if is_title:
            # Remove paragraph style so Pandoc's Heading1 style (with blue
            # color) does not leak through — all formatting is set directly.
            pPr = para._element.get_or_add_pPr()
            for pStyle in pPr.findall(qn("w:pStyle")):
                pPr.remove(pStyle)
            para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for run in para.runs:
                _set_run_font(
                    run, FONT_CONFIG["title"], FONT_SIZES["title"],
                    bold=False,
                )
        elif level and level.startswith("heading"):
            # Remove Pandoc heading style to prevent blue color leakage
            pPr = para._element.get_or_add_pPr()
            for pStyle in pPr.findall(qn("w:pStyle")):
                pPr.remove(pStyle)
            para.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            font_key = FONT_CONFIG.get(level, FONT_CONFIG["body"])
            size_key = FONT_SIZES["heading"] if level != "heading4" else FONT_SIZES["body"]
            is_bold = level != "heading4"
            for run in para.runs:
                _set_run_font(run, font_key, size_key, bold=is_bold)
        else:
            # Body text
            para.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            for run in para.runs:
                _set_run_font(
                    run, FONT_CONFIG["body"], FONT_SIZES["body"],
                    bold=False,
                )

        # Set first-line indent for body paragraphs (2 chars ≈ 32pt)
        if level == "body" and not is_title:
            para.paragraph_format.first_line_indent = Pt(32)

    # ── 3. Page numbers with em-dash (— PAGE —), odd/even ─────────
    for section in doc.sections:
        sect_pr = section._sectPr
        section.different_odd_and_even_pages = True

        # ── Odd pages (right) — 右空一字 ──────────────────────────
        footer_odd = section.footer
        footer_odd.is_linked_to_previous = False
        _clear_footer(footer_odd)
        _build_page_footer(footer_odd, WD_ALIGN_PARAGRAPH.RIGHT, Pt(14))

        # ── Even pages (left) — 左空一字 ──────────────────────────
        # python-docx Section lacks even_footer property;
        # use the underlying FooterPart via sectPr XML
        footer_even = _get_or_create_footer(doc, sect_pr, "even")
        _clear_footer(footer_even)
        _build_page_footer(footer_even, WD_ALIGN_PARAGRAPH.LEFT, -Pt(14))

    # ── 4. Save ───────────────────────────────────────────────────
    doc.save(docx_path)
    return ServiceResult.ok(None)


def _get_or_create_footer(doc, sect_pr, footer_type):
    """Get or create a footer part for odd/even/first pages.

    python-docx only exposes section.footer (the default/odd footer).
    For even/first footers, we must manipulate the XML and OPC parts
    directly.

    Args:
        doc: The Document object.
        sect_pr: The section's sectPr XML element.
        footer_type: "even" or "first".

    Returns:
        A Footer object (python-docx SectionFooter-like wrapper).
    """
    from docx.parts.hdrftr import FooterPart
    from docx.section import _Footer

    FOOTER_RT = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer"

    # Map footer_type string to WD_HEADER_FOOTER enum
    from docx.enum.section import WD_HEADER_FOOTER
    idx_map = {"even": WD_HEADER_FOOTER.EVEN_PAGE,
               "first": WD_HEADER_FOOTER.FIRST_PAGE}

    # Look for existing footerReference of this type
    for ref in sect_pr.findall(qn("w:footerReference")):
        if ref.get(qn("w:type")) == footer_type:
            r_id = ref.get(qn("r:id"))
            return _Footer(sect_pr, doc.part, idx_map[footer_type])

    # Create a new footer part
    footer_part = FooterPart.new(doc.part.package)
    r_id = doc.part.relate_to(footer_part, FOOTER_RT)

    # Add footerReference to sectPr
    ref = OxmlElement("w:footerReference")
    ref.set(qn("w:type"), footer_type)
    ref.set(qn("r:id"), r_id)
    sect_pr.append(ref)

    return _Footer(sect_pr, doc.part, idx_map[footer_type])


def _clear_footer(footer):
    """Remove all content from a footer."""
    for p in footer.paragraphs:
        p.clear()


def _build_page_footer(footer, alignment, indent):
    """Build a footer paragraph with em-dash wrapped page number.

    Format: "— PAGE —" (4号宋体, 一字线 + 数字 + 一字线)

    Args:
        footer: The footer object to modify.
        alignment: Paragraph alignment (odd=RIGHT, even=LEFT).
        indent: Right indent (positive) for odd pages,
                negative left indent for even pages.
    """
    para = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
    para.alignment = alignment

    if indent > 0:
        para.paragraph_format.right_indent = indent
    else:
        para.paragraph_format.left_indent = indent

    # Em-dash before page number
    run_dash1 = para.add_run()
    _set_run_font(run_dash1, FONT_CONFIG["page_num"], FONT_SIZES["page_num"])
    run_dash1.text = "— "

    # Page number field
    run_page = para.add_run()
    _set_run_font(run_page, FONT_CONFIG["page_num"], FONT_SIZES["page_num"])
    _add_page_field(run_page)

    # Em-dash after page number
    run_dash2 = para.add_run()
    _set_run_font(run_dash2, FONT_CONFIG["page_num"], FONT_SIZES["page_num"])
    run_dash2.text = " —"
