"""PDF redaction: pixelate marked regions and delete the text underneath.

Uses PyMuPDF (AGPL-3.0) for redaction and Pillow for the mosaic. The pipeline
keeps the text layer intact outside the marked regions, so the output stays
searchable where nothing was hidden.

Region-level image pixelation is *not* something PyMuPDF can do: its
`PDF_REDACT_IMAGE_PIXELS` only acts on images fully inside the rectangle, and
then it resamples the whole image. So each mark is handled locally instead —
render the clip, mosaic it, delete the text under it, paste the mosaic back.
"""

import io
import os
import re

from errors import ErrorCode, ServiceResult

DEFAULT_MOSAIC_BLOCK = 8

#: Refuse anything larger: rendering every page of a huge scan exceeds both the
#: gunicorn timeout and a 2 GB box.
MAX_PAGES = 100

#: The mosaic patch is rendered at this resolution before being downsampled by
#: `mosaic_block`, so the blocks stay crisp when the result is viewed at 100%.
RENDER_DPI = 200

#: Keyword search is a convenience, not a data-mining tool: cap both the pattern
#: and the result set so a greedy regex cannot flood the UI.
MAX_PATTERN_LENGTH = 200
MAX_MATCHES = 500


def pixelate(img, block: int = DEFAULT_MOSAIC_BLOCK):
    """Return `img` with its detail reduced to blocks of `block` pixels."""
    from PIL import Image

    block = max(2, int(block))
    small = img.resize(
        (max(1, img.width // block), max(1, img.height // block)),
        Image.NEAREST,
    )
    return small.resize(img.size, Image.NEAREST)


def mark_to_page_rect(mark: dict, page_rect) -> "object":
    """Map a normalized top-left mark onto a page rectangle.

    The frontend sends fractions of the rendered page, which sidesteps zoom,
    device pixel ratio and page rotation — all of them already baked into what
    the browser measured. Values outside the page are clamped, so a drag that
    started off-page still yields a usable rectangle.
    """
    x, y = float(mark["x"]), float(mark["y"])
    w, h = float(mark["w"]), float(mark["h"])
    rect = type(page_rect)(
        page_rect.x0 + x * page_rect.width,
        page_rect.y0 + y * page_rect.height,
        page_rect.x0 + (x + w) * page_rect.width,
        page_rect.y0 + (y + h) * page_rect.height,
    )
    return rect.normalize() & page_rect


def region_text(page, rect) -> str:
    """Text still extractable from `rect` — empty means the region is clean."""
    if rect.is_empty:
        return ""
    return " ".join(word[4] for word in page.get_text("words", clip=rect))


def _normalize_rect(rect, page_rect) -> dict | None:
    """Inverse of mark_to_page_rect: page points back to top-left fractions."""
    if rect.is_empty or page_rect.width <= 0 or page_rect.height <= 0:
        return None

    def clamp(value: float) -> float:
        return max(0.0, min(1.0, value))

    left = clamp((rect.x0 - page_rect.x0) / page_rect.width)
    top = clamp((rect.y0 - page_rect.y0) / page_rect.height)
    right = clamp((rect.x1 - page_rect.x0) / page_rect.width)
    bottom = clamp((rect.y1 - page_rect.y0) / page_rect.height)
    if right <= left or bottom <= top:
        return None
    return {"x": left, "y": top, "w": right - left, "h": bottom - top}


_ENCRYPTED_MESSAGE = "This PDF is encrypted — decrypt it first, then upload it again"


def _encrypted_error(doc) -> ServiceResult | None:
    """A failure result if the document needs a password, otherwise None."""
    if doc.needs_pass or doc.is_encrypted:
        return ServiceResult.fail(ErrorCode.VALIDATION_ERROR, _ENCRYPTED_MESSAGE)
    return None


def inspect_pdf(filepath: str, max_pages: int = MAX_PAGES) -> ServiceResult[dict]:
    """Report page count and per-page size, rejecting what the tool cannot handle.

    Args:
        filepath: Path to the uploaded PDF.
        max_pages: Upper bound on page count.

    Returns:
        ServiceResult with dict keys: page_count, pages[{page_no,width,height}].
    """
    if not os.path.isfile(filepath):
        return ServiceResult.fail(ErrorCode.FILE_NOT_FOUND, f"File not found: {filepath}")

    import pymupdf

    try:
        doc = pymupdf.open(filepath)
    except Exception as e:
        return ServiceResult.fail(ErrorCode.PDF_READ_ERROR, f"Failed to read PDF: {e}")

    try:
        encrypted = _encrypted_error(doc)
        if encrypted:
            return encrypted

        page_count = doc.page_count
        if page_count == 0:
            return ServiceResult.fail(ErrorCode.PDF_EMPTY, "The PDF has no pages")
        if page_count > max_pages:
            return ServiceResult.fail(
                ErrorCode.VALIDATION_ERROR,
                f"The PDF has {page_count} pages; this tool accepts up to {max_pages}",
            )

        pages = [
            {"page_no": i + 1, "width": doc[i].rect.width, "height": doc[i].rect.height}
            for i in range(page_count)
        ]
        return ServiceResult.ok({"page_count": page_count, "pages": pages})
    finally:
        doc.close()


def find_text_matches(
    filepath: str,
    pattern: str,
    regex: bool = False,
    pages: list[int] | None = None,
    max_matches: int = MAX_MATCHES,
) -> ServiceResult[dict]:
    """Locate a keyword or regex and return boxes the UI can turn into marks.

    Literal searches go through the PDF text engine, which handles a phrase split
    across spans. Regexes run line by line over the word list, and each hit is
    boxed by the union of the words it covers — one rectangle per hit, however
    many words it spans.

    Args:
        filepath: Source PDF.
        pattern: Keyword, or a regular expression when `regex` is set.
        regex: Treat `pattern` as a regular expression.
        pages: 1-indexed pages to scan (None = all).
        max_matches: Stop after this many hits.

    Returns:
        ServiceResult with dict keys: matches[{page,x,y,w,h,text}], truncated,
        no_text_pages (searched pages whose text layer is empty). Boxes are
        normalized top-left fractions.
    """
    if not os.path.isfile(filepath):
        return ServiceResult.fail(ErrorCode.FILE_NOT_FOUND, f"File not found: {filepath}")

    if not isinstance(pattern, str) or not pattern.strip():
        return ServiceResult.fail(
            ErrorCode.VALIDATION_ERROR, "Enter a keyword or pattern to search for"
        )
    if len(pattern) > MAX_PATTERN_LENGTH:
        return ServiceResult.fail(
            ErrorCode.VALIDATION_ERROR,
            f"The pattern is too long (limit {MAX_PATTERN_LENGTH} characters)",
        )

    compiled = None
    if regex:
        try:
            compiled = re.compile(pattern)
        except re.error as e:
            return ServiceResult.fail(ErrorCode.VALIDATION_ERROR, f"Invalid regular expression: {e}")

    import pymupdf

    try:
        doc = pymupdf.open(filepath)
    except Exception as e:
        return ServiceResult.fail(ErrorCode.PDF_READ_ERROR, f"Failed to read PDF: {e}")

    try:
        encrypted = _encrypted_error(doc)
        if encrypted:
            return encrypted

        page_count = doc.page_count
        if pages:
            for p in pages:
                if not 1 <= int(p) <= page_count:
                    return ServiceResult.fail(
                        ErrorCode.PDF_PAGE_OUT_OF_RANGE,
                        f"Page {p} out of range (1-{page_count})",
                    )
            targets = [int(p) for p in pages]
        else:
            targets = list(range(1, page_count + 1))

        matches: list[dict] = []
        #: Pages the search covered that carry no text at all — keyword search
        #: cannot help there, so the UI has to say so instead of "no matches".
        no_text_pages: list[int] = []
        truncated = False
        for page_no in targets:
            page = doc[page_no - 1]
            if not page.get_text().strip():
                no_text_pages.append(page_no)
            hits = (
                _line_hits(page, compiled)
                if compiled is not None
                else [(rect, pattern) for rect in page.search_for(pattern)]
            )
            for rect, text in hits:
                if len(matches) >= max_matches:
                    truncated = True
                    break
                box = _normalize_rect(rect, page.rect)
                if box:
                    matches.append({"page": page_no, "text": text, **box})
            if truncated:
                break
    except Exception as e:
        return ServiceResult.fail(ErrorCode.PDF_READ_ERROR, f"Failed to search the PDF: {e}")
    finally:
        doc.close()

    return ServiceResult.ok({
        "matches": matches,
        "truncated": truncated,
        "no_text_pages": no_text_pages,
    })


def _line_hits(page, compiled) -> list[tuple]:
    """Regex hits on one page, each boxed by the words the match covers."""
    import pymupdf

    lines: dict[tuple, list] = {}
    for word in page.get_text("words"):
        lines.setdefault((word[5], word[6]), []).append(word)

    hits: list[tuple] = []
    for key in sorted(lines):
        words = sorted(lines[key], key=lambda w: w[7])
        text = ""
        starts: list[int] = []
        for word in words:
            starts.append(len(text))
            text += (" " if text else "") + word[4]

        for match in compiled.finditer(text):
            if not match.group().strip():
                continue
            covered = [
                words[i]
                for i, start in enumerate(starts)
                if match.start() < start + len(words[i][4]) and match.end() > start
            ]
            if not covered:
                continue
            rect = pymupdf.Rect(covered[0][:4])
            for word in covered[1:]:
                rect = rect | pymupdf.Rect(word[:4])
            hits.append((rect, match.group()))
    return hits


def redact_pdf(
    filepath: str,
    output_path: str,
    marks: list[dict],
    mosaic_block: int = DEFAULT_MOSAIC_BLOCK,
) -> ServiceResult[dict]:
    """Write a redacted copy of `filepath` to `output_path`.

    Each mark is a dict of normalized top-left fractions:
    `{"page": 1, "x": 0.1, "y": 0.2, "w": 0.3, "h": 0.05}`.

    Args:
        filepath: Source PDF (never modified).
        output_path: Where to write the redacted PDF.
        marks: Regions to hide.
        mosaic_block: Mosaic block size in pixels of the rendered patch.

    Returns:
        ServiceResult with dict keys: output, page_count, total_marks, applied,
        image_marks, leftover_regions[{mark,page}].
    """
    if not os.path.isfile(filepath):
        return ServiceResult.fail(ErrorCode.FILE_NOT_FOUND, f"File not found: {filepath}")
    if not marks:
        return ServiceResult.fail(ErrorCode.VALIDATION_ERROR, "No regions were marked")

    import pymupdf
    from PIL import Image

    try:
        doc = pymupdf.open(filepath)
    except Exception as e:
        return ServiceResult.fail(ErrorCode.PDF_READ_ERROR, f"Failed to read PDF: {e}")

    try:
        encrypted = _encrypted_error(doc)
        if encrypted:
            return encrypted

        page_count = doc.page_count
        for index, mark in enumerate(marks):
            try:
                page_no = int(mark["page"])
            except (KeyError, TypeError, ValueError):
                return ServiceResult.fail(
                    ErrorCode.VALIDATION_ERROR, f"Mark {index + 1}: invalid page number"
                )
            if not 1 <= page_no <= page_count:
                return ServiceResult.fail(
                    ErrorCode.VALIDATION_ERROR,
                    f"Mark {index + 1}: page {page_no} is out of range (1-{page_count})",
                )

        # Recorded before anything is written: the mosaic patches we insert are
        # images too, and would otherwise be counted as pre-existing content.
        image_pages = {p for p in range(1, page_count + 1) if doc[p - 1].get_images()}

        applied = 0
        for mark in marks:
            page = doc[int(mark["page"]) - 1]
            rect = mark_to_page_rect(mark, page.rect)
            if rect.is_empty:
                continue

            clip = page.get_pixmap(clip=rect, dpi=RENDER_DPI)
            patch = pixelate(Image.open(io.BytesIO(clip.tobytes("png"))).convert("RGB"), mosaic_block)
            buf = io.BytesIO()
            patch.save(buf, format="PNG")

            # Delete the text under the region but leave images untouched — the
            # mosaic covers them, and pixelating a whole scan would be worse.
            page.add_redact_annot(rect)
            page.apply_redactions(images=pymupdf.PDF_REDACT_IMAGE_NONE)
            page.insert_image(rect, stream=buf.getvalue(), overlay=True)
            applied += 1

        purge_document_residue(doc)
        doc.save(output_path, garbage=4, deflate=True)
    except Exception as e:
        return ServiceResult.fail(ErrorCode.CONVERSION_FAILED, f"Failed to redact PDF: {e}")
    finally:
        doc.close()

    leftover = _leftovers(output_path, marks)
    return ServiceResult.ok({
        "output": output_path,
        "page_count": page_count,
        "total_marks": len(marks),
        "applied": applied,
        "image_marks": sum(1 for m in marks if int(m["page"]) in image_pages),
        "leftover_regions": leftover,
    })


def purge_document_residue(doc) -> None:
    """Drop metadata, attachments and unused objects from an open document."""
    for name in list(doc.embfile_names()):
        try:
            doc.embfile_del(name)
        except Exception:
            pass
    doc.set_metadata({})
    doc.scrub()


def _leftovers(output_path: str, marks: list[dict]) -> list[dict]:
    """Re-open a redacted file and report marks whose region still yields text.

    This is the tool's own honesty check: redaction that silently failed to
    remove the text is worse than no redaction, so the caller must be told.
    """
    import pymupdf

    found = []
    doc = pymupdf.open(output_path)
    try:
        for index, mark in enumerate(marks):
            page = doc[int(mark["page"]) - 1]
            rect = mark_to_page_rect(mark, page.rect)
            if region_text(page, rect).strip():
                found.append({"mark": index + 1, "page": int(mark["page"])})
    finally:
        doc.close()
    return found
