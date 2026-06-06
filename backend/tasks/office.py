"""office_queue tasks: Office document property modification and Excel merge.

These tasks involve ZIP manipulation and spreadsheet processing,
routed to office_queue to avoid competing with conversion and PDF operations.
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


@celery.task(base=TrackedTask, bind=True, queue="office_queue")
def modify_properties_async(self, filepath: str, output_path: str, props: dict,
                           unify_time: bool = False):
    """Asynchronously modify Office document properties."""
    _record.create_task(self.request.id, "properties_modify", "office_queue")
    _record.update_progress(self.request.id, "started", progress=0,
                           progress_message="正在修改文档属性...")

    from backend.properties import _resolve_time_props, modify_properties
    resolved = _resolve_time_props(props, unify_time)
    modify_properties(filepath, output_path, resolved)

    _record.update_progress(self.request.id, "success", progress=100,
                           progress_message="属性修改完成")

    return {"status": "ok"}


@celery.task(base=TrackedTask, bind=True, queue="office_queue")
def batch_properties_async(self, filepaths: list[str], output_dir: str, props: dict,
                          unify_time: bool = False):
    """Asynchronously batch modify Office document properties."""
    _record.create_task(self.request.id, "properties_batch", "office_queue")
    total = len(filepaths)
    _record.update_progress(self.request.id, "started", progress=0,
                           progress_message=f"正在批量修改 {total} 个文件的属性...")

    from backend.properties import batch_modify_properties
    results = batch_modify_properties(filepaths, output_dir, props, unify_time)
    success_count = sum(1 for r in results if r["success"])

    _record.update_progress(
        self.request.id, "success", progress=100,
        progress_message=f"已完成 {success_count}/{total} 个文件",
        result_data=json.dumps({"success_count": success_count, "total": total}),
    )

    return results


@celery.task(base=TrackedTask, bind=True, queue="office_queue")
def merge_excel_async(self, filepaths: list[str], output_path: str):
    """Asynchronously merge Excel/CSV files."""
    _record.create_task(self.request.id, "excel_merge", "office_queue")
    _record.update_progress(self.request.id, "started", progress=0,
                           progress_message="正在合并表格...")

    from backend.excel_merger import merge_excel_files
    result = merge_excel_files(filepaths, output_path)

    _record.update_progress(
        self.request.id, "success", progress=100,
        progress_message=f"已合并 {result['file_count']} 个文件，共 {result['total_rows']} 行",
        result_data=json.dumps(result),
    )

    return result
