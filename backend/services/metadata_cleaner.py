"""Metadata cleaner — strip metadata from Office and PDF files."""

import os

from errors import ErrorCode, ServiceResult


def clean_metadata(filepath: str, output_path: str) -> ServiceResult[dict]:
    """Strip all metadata from an Office or PDF file.

    Args:
        filepath: Path to the source document (.docx/.xlsx/.pptx/.pdf).
        output_path: Path to write the cleaned document.

    Returns:
        ServiceResult with dict: format, fields_cleaned, warnings.
    """
    ext = os.path.splitext(filepath)[1].lower()

    try:
        if ext == ".docx":
            return _clean_docx(filepath, output_path)
        elif ext == ".xlsx":
            return _clean_xlsx(filepath, output_path)
        elif ext == ".pptx":
            return _clean_pptx(filepath, output_path)
        elif ext == ".pdf":
            return _clean_pdf(filepath, output_path)
        else:
            return ServiceResult.fail(ErrorCode.UNSUPPORTED_FORMAT, f"Unsupported file format: {ext}")
    except FileNotFoundError:
        return ServiceResult.fail(ErrorCode.VALIDATION_ERROR, "Input file not found")


def _clean_docx(filepath: str, output_path: str) -> ServiceResult[dict]:
    """Strip metadata from a DOCX file."""
    import shutil
    from docx import Document

    shutil.copy2(filepath, output_path)
    doc = Document(output_path)
    cp = doc.core_properties

    fields_cleaned = []
    for attr in ("author", "last_modified_by", "category", "comments", "identifier",
                 "keywords", "language", "revision", "subject", "title", "version"):
        try:
            setattr(cp, attr, "")
            fields_cleaned.append(attr)
        except Exception:
            pass

    doc.save(output_path)
    return ServiceResult.ok({"format": "docx", "fields_cleaned": len(fields_cleaned)})


def _clean_xlsx(filepath: str, output_path: str) -> ServiceResult[dict]:
    """Strip metadata from an XLSX file."""
    import shutil
    from openpyxl import load_workbook

    shutil.copy2(filepath, output_path)
    wb = load_workbook(output_path)
    props = wb.properties
    fields_cleaned = []

    for attr in ("creator", "lastModifiedBy", "title", "description", "subject",
                 "keywords", "category", "identifier", "language", "revision", "version"):
        try:
            setattr(props, attr, "")
            fields_cleaned.append(attr)
        except Exception:
            pass

    wb.save(output_path)
    return ServiceResult.ok({"format": "xlsx", "fields_cleaned": len(fields_cleaned)})


def _clean_pptx(filepath: str, output_path: str) -> ServiceResult[dict]:
    """Strip metadata from a PPTX file."""
    import shutil
    from pptx import Presentation

    shutil.copy2(filepath, output_path)
    prs = Presentation(output_path)
    cp = prs.core_properties
    fields_cleaned = []

    for attr in ("author", "last_modified_by", "category", "comments", "identifier",
                 "keywords", "language", "revision", "subject", "title", "version"):
        try:
            setattr(cp, attr, "")
            fields_cleaned.append(attr)
        except Exception:
            pass

    prs.save(output_path)
    return ServiceResult.ok({"format": "pptx", "fields_cleaned": len(fields_cleaned)})


def _clean_pdf(filepath: str, output_path: str) -> ServiceResult[dict]:
    """Strip metadata from a PDF file."""
    from pypdf import PdfReader, PdfWriter

    try:
        reader = PdfReader(filepath)
    except Exception as e:
        return ServiceResult.fail(ErrorCode.PDF_READ_ERROR, f"Failed to read PDF: {e}")

    writer = PdfWriter()
    fields_cleaned = 0

    for page in reader.pages:
        # Remove metadata from page
        if "/Metadata" in page:
            del page["/Metadata"]
            fields_cleaned += 1
        writer.add_page(page)

    # Remove document-level metadata
    if reader.metadata:
        fields_cleaned += len(reader.metadata)

    with open(output_path, "wb") as f:
        writer.write(f)

    return ServiceResult.ok({
        "format": "pdf",
        "fields_cleaned": fields_cleaned,
        "warning": "Document metadata has been stripped. Some PDF viewers may still show limited info.",
    })
