"""Async task definitions for docStamp.

Task modules:
    video.py       — pdf_queue: MP4 → WMV conversion
    maintenance.py — office_queue: beat tasks, temp file cleanup

Tool work (PDF editing, properties, Excel merge, …) runs synchronously in
request handlers; only long-running jobs belong here.
"""
