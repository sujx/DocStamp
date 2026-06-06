"""pdf_queue tasks: PDF watermark, print split, page editing, img2pdf, pdf2img.

These tasks are I/O and CPU intensive and routed to pdf_queue to avoid
competing with conversion and office operations.
"""

import json
import os
import uuid

from celery import Task

from backend.celery_app import celery
from backend.models import TaskRecord


def _get_db_path():
    from backend.config import Config
    return Config().TASK_DB_PATH


_record = TaskRecord(_get_db_path())


class TrackedTask(Task):
    abstract = True

    def on_success(self, retval, task_id, args, kwargs):
        _record.update_progress(task_id, "success", progress=100)

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        _record.update_progress(
            task_id, "failure", error_code="TASK_FAILED", error_message=str(exc),
        )


# ── Watermark ─────────────────────────────────────────────────────────

@celery.task(base=TrackedTask, bind=True, queue="pdf_queue")
def add_watermark_async(self, filepath: str, output_path: str, params: dict,
                        image_filepath: str = None):
    """Asynchronously add a watermark to a document."""
    _record.create_task(self.request.id, "watermark_add", "pdf_queue")
    _record.update_progress(self.request.id, "started", progress=0,
                           progress_message="正在添加水印...")

    from backend.watermark import add_watermark
    add_watermark(filepath, output_path, params, image_filepath)

    _record.update_progress(self.request.id, "success", progress=100,
                           progress_message="水印添加完成")

    return {"status": "ok"}


@celery.task(base=TrackedTask, bind=True, queue="pdf_queue")
def remove_watermark_async(self, filepath: str, output_path: str):
    """Asynchronously remove watermarks from a document."""
    _record.create_task(self.request.id, "watermark_remove", "pdf_queue")
    _record.update_progress(self.request.id, "started", progress=0,
                           progress_message="正在去除水印...")

    from backend.watermark import remove_watermark
    result = remove_watermark(filepath, output_path)

    _record.update_progress(self.request.id, "success", progress=100,
                           progress_message=f"水印已去除 ({result['method']})")

    return {"status": "ok", "method": result["method"]}


# ── Print Split ──────────────────────────────────────────────────────

@celery.task(base=TrackedTask, bind=True, queue="pdf_queue")
def split_pdf_async(self, filepath: str, output_dir: str, batch_size: int):
    """Asynchronously split a PDF into print batches."""
    _record.create_task(self.request.id, "print_split", "pdf_queue")
    _record.update_progress(self.request.id, "started", progress=0,
                           progress_message="正在拆分 PDF...")

    from backend.print_split import split_pdf
    batches = split_pdf(filepath, output_dir, batch_size)

    _record.update_progress(
        self.request.id, "success", progress=100,
        progress_message=f"已拆分为 {len(batches)} 个批次",
        result_data=json.dumps({"batch_count": len(batches)}),
    )

    return {"batch_count": len(batches), "batches": batches}


# ── PDF Editor ───────────────────────────────────────────────────────

@celery.task(base=TrackedTask, bind=True, queue="pdf_queue")
def pdf_delete_async(self, filepath: str, output_path: str, pages: list[int]):
    """Asynchronously delete pages from a PDF."""
    _record.create_task(self.request.id, "pdf_delete", "pdf_queue")
    _record.update_progress(self.request.id, "started", progress=0,
                           progress_message=f"正在删除 {len(pages)} 页...")

    from backend.pdf_editor import pdf_delete_pages
    result = pdf_delete_pages(filepath, output_path, pages)

    _record.update_progress(self.request.id, "success", progress=100,
                           progress_message=f"已删除 {result['deleted_pages']} 页")

    return result


@celery.task(base=TrackedTask, bind=True, queue="pdf_queue")
def pdf_insert_async(self, filepath: str, insert_path: str, output_path: str,
                     at_position: int, insert_pages: list[int] | None):
    """Asynchronously insert pages into a PDF."""
    _record.create_task(self.request.id, "pdf_insert", "pdf_queue")
    _record.update_progress(self.request.id, "started", progress=0,
                           progress_message="正在插入页面...")

    from backend.pdf_editor import pdf_insert_pages
    result = pdf_insert_pages(filepath, insert_path, output_path, at_position, insert_pages)

    _record.update_progress(self.request.id, "success", progress=100,
                           progress_message=f"已插入 {result['inserted_pages']} 页")

    return result


@celery.task(base=TrackedTask, bind=True, queue="pdf_queue")
def pdf_reorder_async(self, filepath: str, output_path: str, new_order: list[int]):
    """Asynchronously reorder pages of a PDF."""
    _record.create_task(self.request.id, "pdf_reorder", "pdf_queue")
    _record.update_progress(self.request.id, "started", progress=0,
                           progress_message="正在重排页面...")

    from backend.pdf_editor import pdf_reorder_pages
    result = pdf_reorder_pages(filepath, output_path, new_order)

    _record.update_progress(self.request.id, "success", progress=100,
                           progress_message=f"已重排 {result['total_pages']} 页")

    return result


# ── Image ↔ PDF ──────────────────────────────────────────────────────

@celery.task(base=TrackedTask, bind=True, queue="pdf_queue")
def images_to_pdf_async(self, image_paths: list[str], output_path: str, page_size: str):
    """Asynchronously merge images into a PDF."""
    _record.create_task(self.request.id, "img2pdf", "pdf_queue")
    _record.update_progress(self.request.id, "started", progress=0,
                           progress_message="正在合并图片...")

    from backend.img2pdf_handler import images_to_pdf
    total = len(image_paths)

    for i in range(total):
        progress = int((i + 1) / total * 90)
        _record.update_progress(
            self.request.id, "progress", progress=progress,
            progress_message=f"正在处理第 {i+1}/{total} 张图片",
        )

    images_to_pdf(image_paths, output_path, page_size)

    _record.update_progress(self.request.id, "success", progress=100,
                           progress_message=f"已合并 {total} 张图片为 PDF")

    return {"status": "ok", "image_count": total}


@celery.task(base=TrackedTask, bind=True, queue="pdf_queue")
def pdf_to_images_async(self, filepath: str, output_dir: str, fmt: str = "png",
                        dpi: int = 200, pages: list[int] | None = None):
    """Asynchronously convert PDF pages to images."""
    _record.create_task(self.request.id, "pdf2img", "pdf_queue")
    _record.update_progress(self.request.id, "started", progress=0,
                           progress_message="正在转换 PDF 为图片...")

    from backend.pdf_to_images import pdf_to_images
    result = pdf_to_images(filepath, output_dir, fmt=fmt, dpi=dpi, pages=pages)

    _record.update_progress(
        self.request.id, "success", progress=100,
        progress_message=f"已转换 {result['converted']} 页",
        result_data=json.dumps({"converted": result["converted"], "files": result["files"]}),
    )

    return result
