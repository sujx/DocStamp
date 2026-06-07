"""Document format conversion — DOCX→PDF, HTML→PDF."""

import os
import subprocess

from errors import ErrorCode, ServiceResult


def convert_document(filepath: str, output_path: str, target_format: str) -> ServiceResult[None]:
    """Convert a document to a different format.

    Supported conversions:
      - .docx → pdf (via LibreOffice headless)
      - .html/.htm → pdf (via WeasyPrint)

    Args:
        filepath: Path to the source document.
        output_path: Path to write the converted document.
        target_format: Target format (currently only "pdf").

    Returns:
        ServiceResult with None on success.
    """
    if target_format != "pdf":
        return ServiceResult.fail(ErrorCode.VALIDATION_ERROR, f"Unsupported target format: {target_format}")

    ext = os.path.splitext(filepath)[1].lower()

    if ext == ".docx":
        return _docx_to_pdf(filepath, output_path)
    elif ext in (".html", ".htm"):
        return _html_to_pdf(filepath, output_path)
    else:
        return ServiceResult.fail(ErrorCode.UNSUPPORTED_FORMAT, f"Cannot convert {ext} to {target_format}")


def _docx_to_pdf(filepath: str, output_path: str) -> ServiceResult[None]:
    """Convert DOCX to PDF using LibreOffice headless."""
    output_dir = os.path.dirname(output_path)

    try:
        result = subprocess.run(
            ["libreoffice", "--headless", "--convert-to", "pdf",
             "--outdir", output_dir, filepath],
            capture_output=True, timeout=120, text=True,
        )
        if result.returncode != 0:
            return ServiceResult.fail(
                ErrorCode.CONVERSION_FAILED,
                f"LibreOffice conversion failed: {result.stderr.strip()}",
            )

        # LibreOffice outputs <basename>.pdf in the output directory
        basename = os.path.splitext(os.path.basename(filepath))[0]
        generated_pdf = os.path.join(output_dir, f"{basename}.pdf")

        if not os.path.isfile(generated_pdf):
            return ServiceResult.fail(ErrorCode.CONVERSION_FAILED, "Conversion produced no output file")

        # Rename to expected output path if different
        if generated_pdf != output_path:
            os.rename(generated_pdf, output_path)

        return ServiceResult.ok(None)
    except FileNotFoundError:
        return ServiceResult.fail(
            ErrorCode.TOOL_NOT_AVAILABLE,
            "LibreOffice not found. Install: apt install libreoffice-core",
        )
    except subprocess.TimeoutExpired:
        return ServiceResult.fail(ErrorCode.CONVERSION_FAILED, "Conversion timed out after 120s")


def _html_to_pdf(filepath: str, output_path: str) -> ServiceResult[None]:
    """Convert HTML to PDF using WeasyPrint."""
    try:
        from weasyprint import HTML
    except (ImportError, OSError) as e:
        return ServiceResult.fail(
            ErrorCode.TOOL_NOT_AVAILABLE,
            f"WeasyPrint not available: {e}. Install system deps: apt install libpango-1.0-0 libgdk-pixbuf2.0-0",
        )

    try:
        HTML(filename=filepath).write_pdf(output_path)
        return ServiceResult.ok(None)
    except Exception as e:
        return ServiceResult.fail(ErrorCode.CONVERSION_FAILED, f"HTML to PDF conversion failed: {e}")
