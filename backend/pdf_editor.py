"""PDF page manipulation — delete or insert pages and regenerate a PDF.

Supports:
- Deleting specified pages (by page number, 1-indexed)
- Inserting pages from another PDF at a specified position
- Reordering pages
"""

from pypdf import PdfReader, PdfWriter


def pdf_delete_pages(input_path: str, output_path: str, pages_to_delete: list) -> dict:
    """Remove specified pages from a PDF.

    Args:
        input_path: Path to the source PDF file.
        output_path: Path to write the output PDF.
        pages_to_delete: List of 1-indexed page numbers to remove.

    Returns:
        dict with keys: original_pages, deleted_pages, remaining_pages.

    Raises:
        ValueError: If pages_to_delete is empty or contains invalid pages.
    """
    if not pages_to_delete:
        raise ValueError("No pages specified for deletion")

    try:
        reader = PdfReader(input_path)
    except Exception as e:
        raise ValueError(f"Failed to read PDF: {e}")

    total = len(reader.pages)
    if total == 0:
        raise ValueError("PDF has no pages")

    # Validate page numbers
    for p in pages_to_delete:
        if p < 1 or p > total:
            raise ValueError(f"Page number {p} out of range (1-{total})")

    delete_set = set(pages_to_delete)
    writer = PdfWriter()
    kept = 0

    for i in range(total):
        page_num = i + 1  # 1-indexed
        if page_num not in delete_set:
            writer.add_page(reader.pages[i])
            kept += 1

    with open(output_path, "wb") as f:
        writer.write(f)

    return {
        "original_pages": total,
        "deleted_pages": len(delete_set),
        "remaining_pages": kept,
    }


def pdf_insert_pages(
    input_path: str,
    insert_path: str,
    output_path: str,
    at_position: int,
    pages_to_insert: list = None,
) -> dict:
    """Insert pages from another PDF into the source PDF.

    Args:
        input_path: Path to the source PDF.
        insert_path: Path to the PDF whose pages will be inserted.
        output_path: Path to write the output PDF.
        at_position: 1-indexed position to insert at (0 = at beginning,
                     插入到第N页之后, 0 = 最前面, -1 = 最后面).
        pages_to_insert: List of 1-indexed pages from the insert PDF
                         (None = all pages).

    Returns:
        dict with keys: original_pages, inserted_pages, final_pages.

    Raises:
        ValueError: If position is invalid.
    """
    try:
        reader = PdfReader(input_path)
        insert_reader = PdfReader(insert_path)
    except Exception as e:
        raise ValueError(f"Failed to read PDF: {e}")

    total = len(reader.pages)
    insert_total = len(insert_reader.pages)

    if insert_total == 0:
        raise ValueError("Insert PDF has no pages")

    if at_position < 0:
        at_position = total  # Insert at end if negative

    if at_position > total:
        raise ValueError(
            f"Insert position {at_position} out of range (0-{total})"
        )

    if pages_to_insert is None:
        pages_to_insert = list(range(1, insert_total + 1))

    # Validate insert pages
    for p in pages_to_insert:
        if p < 1 or p > insert_total:
            raise ValueError(
                f"Insert page {p} out of range (1-{insert_total})"
            )

    writer = PdfWriter()

    # Copy pages up to insertion point
    for i in range(at_position):
        writer.add_page(reader.pages[i])

    # Insert specified pages
    for p in pages_to_insert:
        writer.add_page(insert_reader.pages[p - 1])

    # Copy remaining pages
    for i in range(at_position, total):
        writer.add_page(reader.pages[i])

    with open(output_path, "wb") as f:
        writer.write(f)

    return {
        "original_pages": total,
        "inserted_pages": len(pages_to_insert),
        "final_pages": total + len(pages_to_insert),
    }


def pdf_reorder_pages(input_path: str, output_path: str, new_order: list) -> dict:
    """Reorder pages of a PDF.

    Args:
        input_path: Path to the source PDF.
        output_path: Path to write the output PDF.
        new_order: New page order as list of 1-indexed page numbers.
                   Must include every page exactly once.

    Returns:
        dict with keys: total_pages.

    Raises:
        ValueError: If the order is invalid.
    """
    try:
        reader = PdfReader(input_path)
    except Exception as e:
        raise ValueError(f"Failed to read PDF: {e}")

    total = len(reader.pages)
    if total == 0:
        raise ValueError("PDF has no pages")

    if sorted(new_order) != list(range(1, total + 1)):
        raise ValueError(
            f"Order must contain all pages 1-{total} exactly once"
        )

    writer = PdfWriter()
    for p in new_order:
        writer.add_page(reader.pages[p - 1])

    with open(output_path, "wb") as f:
        writer.write(f)

    return {"total_pages": total}
