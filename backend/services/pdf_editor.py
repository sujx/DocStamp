"""PDF page manipulation — delete, insert, reorder pages."""

from pypdf import PdfReader, PdfWriter

from errors import ErrorCode, ServiceResult
from flask_babel import lazy_gettext as _l


def pdf_delete_pages(input_path: str, output_path: str, pages_to_delete: list) -> ServiceResult[dict]:
    """Remove specified pages from a PDF.

    Args:
        input_path: Path to the source PDF file.
        output_path: Path to write the output PDF.
        pages_to_delete: List of 1-indexed page numbers to remove.

    Returns:
        ServiceResult with dict: original_pages, deleted_pages, remaining_pages.
    """
    if not pages_to_delete:
        return ServiceResult.fail(ErrorCode.PDF_NO_PAGES_SPECIFIED, _l("No pages specified for deletion"))

    try:
        reader = PdfReader(input_path)
    except Exception as e:
        return ServiceResult.fail(ErrorCode.PDF_READ_ERROR, _l("Failed to read PDF: %(e)s", e=e))

    total = len(reader.pages)
    if total == 0:
        return ServiceResult.fail(ErrorCode.PDF_EMPTY, _l("PDF has no pages"))

    for p in pages_to_delete:
        if p < 1 or p > total:
            return ServiceResult.fail(ErrorCode.PDF_PAGE_OUT_OF_RANGE, _l("Page number %(p)s out of range (1-%(total)s)", p=p, total=total))

    delete_set = set(pages_to_delete)
    writer = PdfWriter()
    kept = 0

    for i in range(total):
        page_num = i + 1
        if page_num not in delete_set:
            writer.add_page(reader.pages[i])
            kept += 1

    with open(output_path, "wb") as f:
        writer.write(f)

    return ServiceResult.ok({
        "original_pages": total,
        "deleted_pages": len(delete_set),
        "remaining_pages": kept,
    })


def pdf_insert_pages(
    input_path: str,
    insert_path: str,
    output_path: str,
    at_position: int,
    pages_to_insert: list = None,
) -> ServiceResult[dict]:
    """Insert pages from another PDF into the source PDF.

    Args:
        input_path: Path to the source PDF.
        insert_path: Path to the PDF whose pages will be inserted.
        output_path: Path to write the output PDF.
        at_position: 1-indexed position to insert after (0 = at beginning).
        pages_to_insert: List of 1-indexed pages from the insert PDF (None = all).

    Returns:
        ServiceResult with dict: original_pages, inserted_pages, final_pages.
    """
    try:
        reader = PdfReader(input_path)
        insert_reader = PdfReader(insert_path)
    except Exception as e:
        return ServiceResult.fail(ErrorCode.PDF_READ_ERROR, _l("Failed to read PDF: %(e)s", e=e))

    total = len(reader.pages)
    insert_total = len(insert_reader.pages)

    if insert_total == 0:
        return ServiceResult.fail(ErrorCode.PDF_EMPTY, _l("Insert PDF has no pages"))

    if at_position < 0:
        at_position = total
    if at_position > total:
        return ServiceResult.fail(
            ErrorCode.PDF_PAGE_OUT_OF_RANGE,
            _l("Insert position %(at_position)s out of range (0-%(total)s)", at_position=at_position, total=total),
        )

    if pages_to_insert is None:
        pages_to_insert = list(range(1, insert_total + 1))

    for p in pages_to_insert:
        if p < 1 or p > insert_total:
            return ServiceResult.fail(
                ErrorCode.PDF_PAGE_OUT_OF_RANGE,
                _l("Insert page %(p)s out of range (1-%(insert_total)s)", p=p, insert_total=insert_total),
            )

    writer = PdfWriter()

    for i in range(at_position):
        writer.add_page(reader.pages[i])

    for p in pages_to_insert:
        writer.add_page(insert_reader.pages[p - 1])

    for i in range(at_position, total):
        writer.add_page(reader.pages[i])

    with open(output_path, "wb") as f:
        writer.write(f)

    return ServiceResult.ok({
        "original_pages": total,
        "inserted_pages": len(pages_to_insert),
        "final_pages": total + len(pages_to_insert),
    })


def pdf_reorder_pages(input_path: str, output_path: str, new_order: list) -> ServiceResult[dict]:
    """Reorder pages of a PDF.

    Args:
        input_path: Path to the source PDF.
        output_path: Path to write the output PDF.
        new_order: New page order as list of 1-indexed page numbers.

    Returns:
        ServiceResult with dict: total_pages.
    """
    try:
        reader = PdfReader(input_path)
    except Exception as e:
        return ServiceResult.fail(ErrorCode.PDF_READ_ERROR, _l("Failed to read PDF: %(e)s", e=e))

    total = len(reader.pages)
    if total == 0:
        return ServiceResult.fail(ErrorCode.PDF_EMPTY, _l("PDF has no pages"))

    if sorted(new_order) != list(range(1, total + 1)):
        return ServiceResult.fail(
            ErrorCode.VALIDATION_ERROR,
            _l("Order must contain all pages 1-%(total)s exactly once", total=total),
        )

    writer = PdfWriter()
    for p in new_order:
        writer.add_page(reader.pages[p - 1])

    with open(output_path, "wb") as f:
        writer.write(f)

    return ServiceResult.ok({"total_pages": total})
