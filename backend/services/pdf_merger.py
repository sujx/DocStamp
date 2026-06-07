"""PDF merge: combine multiple PDF files into a single PDF."""

from pypdf import PdfReader, PdfWriter

from errors import ErrorCode, ServiceResult


def merge_pdfs(filepaths: list[str], output_path: str) -> ServiceResult[int]:
    """Merge multiple PDF files into one.

    Args:
        filepaths: Ordered list of paths to source PDFs.
        output_path: Path to write the merged PDF.

    Returns:
        ServiceResult with total page count on success.
    """
    if not filepaths:
        return ServiceResult.fail(ErrorCode.VALIDATION_ERROR, "At least one PDF file is required")

    writer = PdfWriter()

    for fp in filepaths:
        try:
            reader = PdfReader(fp)
        except Exception as e:
            return ServiceResult.fail(ErrorCode.PDF_READ_ERROR, f"Failed to read PDF: {e}")

        for page in reader.pages:
            writer.add_page(page)

    with open(output_path, "wb") as f:
        writer.write(f)

    return ServiceResult.ok(len(writer.pages))
