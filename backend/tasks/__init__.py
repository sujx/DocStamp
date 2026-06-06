"""Async task definitions for docStamp.

Sub-packages:
    convert.py   — convert_queue: MD → DOCX, DOCX formatting
    pdf.py       — pdf_queue: watermark, print split, PDF editor, img2pdf, pdf2img
    office.py    — office_queue: properties modification, Excel merge
    maintenance.py — beat tasks: temp file cleanup
"""
