"""PDF print batch splitting.

Splits a multi-page PDF into numbered batches for controlled printing.
"""

import os

from pypdf import PdfReader, PdfWriter

from errors import ErrorCode, ServiceResult


def split_pdf(filepath: str, output_dir: str, batch_size: int) -> ServiceResult[list]:
    """Split a PDF into batches of pages.

    Args:
        filepath: Path to the source PDF file.
        output_dir: Directory to write batch PDF files.
        batch_size: Number of pages per batch.

    Returns:
        ServiceResult with list of batch dicts:
        [{"batch_no": 1, "pages": 60, "filename": "batch_001.pdf",
          "page_range": "1-60"}, ...]
    """
    if batch_size < 1:
        return ServiceResult.fail(ErrorCode.VALIDATION_ERROR, "Batch size must be at least 1")

    try:
        reader = PdfReader(filepath)
    except Exception as e:
        return ServiceResult.fail(ErrorCode.PDF_READ_ERROR, f"Failed to read PDF: {e}")

    total_pages = len(reader.pages)
    if total_pages == 0:
        return ServiceResult.fail(ErrorCode.PDF_EMPTY, "PDF has no pages")

    batch_count = (total_pages + batch_size - 1) // batch_size
    batches = []

    for i in range(batch_count):
        start_page = i * batch_size
        end_page = min(start_page + batch_size, total_pages)

        writer = PdfWriter()
        for page_idx in range(start_page, end_page):
            writer.add_page(reader.pages[page_idx])

        batch_no = i + 1
        filename = f"batch_{batch_no:03d}.pdf"
        output_path = os.path.join(output_dir, filename)

        with open(output_path, "wb") as f:
            writer.write(f)

        batches.append({
            "batch_no": batch_no,
            "pages": end_page - start_page,
            "filename": filename,
            "page_range": f"{start_page + 1}-{end_page}",
        })

    return ServiceResult.ok(batches)
