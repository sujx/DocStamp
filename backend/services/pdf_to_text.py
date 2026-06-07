"""PDF text extraction using pdfminer.six.

Supports extracting text from PDF files with optional page range selection.
"""

from pdfminer.high_level import extract_text
from pdfminer.layout import LAParams
from pypdf import PdfReader

from errors import ErrorCode, ServiceResult


def extract_pdf_text(filepath: str, page_numbers: list[int] | None = None) -> ServiceResult[str]:
    """Extract plain text from a PDF file.

    Args:
        filepath: Path to the source PDF.
        page_numbers: Optional 1-indexed list of pages to extract.
                      None or empty = all pages.

    Returns:
        ServiceResult with extracted text string on success.
    """
    laparams = LAParams(
        line_margin=0.5,
        char_margin=2.0,
        word_margin=0.1,
        boxes_flow=0.5,
        detect_vertical=True,
        all_texts=True,
    )

    try:
        text = extract_text(filepath, laparams=laparams, page_numbers=page_numbers)
    except Exception as e:
        return ServiceResult.fail(ErrorCode.PDF_READ_ERROR, f"PDF text extraction failed: {e}")

    if not text or not text.strip():
        return ServiceResult.fail(ErrorCode.PDF_EMPTY, "No extractable text found in this PDF")

    return ServiceResult.ok(text)


def get_pdf_page_count(filepath: str) -> ServiceResult[int]:
    """Get total page count of a PDF."""
    try:
        return ServiceResult.ok(len(PdfReader(filepath).pages))
    except Exception as e:
        return ServiceResult.fail(ErrorCode.PDF_READ_ERROR, f"Failed to read PDF: {e}")
