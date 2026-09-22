"""Tests for Celery task-record tracking hooks and beat schedule wiring."""

import os
import sys
from pathlib import Path

import pytest

# backend/tasks/* use 'backend.xxx' absolute imports → need the repo root importable
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from backend.models import TaskRecord, init_db  # noqa: E402


@pytest.fixture
def tracked(monkeypatch, tmp_path):
    """The video task module with its TaskRecord pointed at a throwaway DB."""
    import backend.tasks.video as video

    db_path = str(tmp_path / "tasks.db")
    init_db(db_path)
    monkeypatch.setattr(video._record, "db_path", db_path)
    return video


@pytest.fixture
def record(tracked):
    return TaskRecord(tracked._record.db_path)


class TestTrackedTaskHooks:
    """The lifecycle hooks must actually persist — they are the SSE data source."""

    def test_on_success_marks_success(self, tracked, record):
        record.create_task("t-ok", "video_convert", "pdf_queue")

        tracked.TrackedTask().on_success(None, "t-ok", (), {})

        row = record.get_by_id("t-ok")
        assert row["status"] == "success"
        assert row["progress"] == 100

    def test_on_success_keeps_task_reported_failure(self, tracked, record):
        """Task bodies report failures by writing a terminal record, not by raising."""
        record.create_task("t-fail", "video_convert", "pdf_queue")
        record.update_progress(
            "t-fail", "failure", error_code="CONVERSION_FAILED", error_message="boom",
        )

        tracked.TrackedTask().on_success({"error": "boom"}, "t-fail", (), {})

        row = record.get_by_id("t-fail")
        assert row["status"] == "failure"
        assert row["error_code"] == "CONVERSION_FAILED"
        assert row["error_message"] == "boom"

    def test_on_failure_records_error(self, tracked, record):
        record.create_task("t-raise", "video_convert", "pdf_queue")

        tracked.TrackedTask().on_failure(
            RuntimeError("ffmpeg died"), "t-raise", (), {}, None,
        )

        row = record.get_by_id("t-raise")
        assert row["status"] == "failure"
        assert row["error_code"] == "TASK_FAILED"
        assert "ffmpeg died" in row["error_message"]

    def test_on_retry_sets_progress_message(self, tracked, record):
        record.create_task("t-retry", "video_convert", "pdf_queue")

        tracked.TrackedTask().on_retry(
            RuntimeError("transient"), "t-retry", (), {}, None,
        )

        row = record.get_by_id("t-retry")
        assert row["status"] == "progress"
        assert "transient" in row["progress_message"]


class TestCeleryConfig:
    def test_beat_schedule_targets_registered_tasks(self):
        import backend.tasks.maintenance  # noqa: F401 — registers the cleanup task
        from backend.celery_app import celery

        for entry_name, entry in celery.conf.beat_schedule.items():
            assert entry["task"] in celery.tasks, (
                f"beat entry '{entry_name}' points at unregistered task '{entry['task']}'"
            )

    def test_result_expiry_uses_the_real_celery_key(self):
        from backend.celery_app import celery

        assert celery.conf.result_expires
        assert "result_expire" not in celery.conf


class TestTaskModuleRegistration:
    """Every module the worker imports must be driven by something.

    A task module kept in `include=` after its dispatcher disappeared keeps
    importing stale paths and drifts out of sync with the services it calls —
    nothing fails until a worker actually starts.
    """

    @staticmethod
    def _driver_sources() -> str:
        """Backend sources outside tasks/ that can dispatch or schedule work."""
        backend = Path(__file__).resolve().parents[1]
        skip = {"tasks", "tests"}
        return "\n".join(
            path.read_text(encoding="utf-8")
            for path in backend.rglob("*.py")
            if path.name != "celery_app.py"
            and not (skip & set(path.relative_to(backend).parts))
        )

    def test_every_included_module_is_dispatched_or_scheduled(self):
        from backend.celery_app import celery

        drivers = self._driver_sources()
        scheduled = " ".join(e["task"] for e in celery.conf.beat_schedule.values())

        orphans = [
            module
            for module in celery.conf.include
            if module not in drivers and module not in scheduled
        ]
        assert not orphans, f"worker imports modules nothing dispatches: {orphans}"

    def test_task_routes_target_modules_the_worker_imports(self):
        from backend.celery_app import celery

        imported = set(celery.conf.include)
        orphans = [
            pattern
            for pattern in celery.conf.task_routes
            if pattern.removesuffix(".*") not in imported
        ]
        assert not orphans, f"routes target modules never imported: {orphans}"

    def test_included_modules_import_and_register_tasks(self):
        """A broken `include` entry only shows up when the worker container boots."""
        import importlib

        from backend.celery_app import celery

        for module_path in celery.conf.include:
            importlib.import_module(module_path)

        registered = set(celery.tasks)
        for module_path in celery.conf.include:
            assert any(
                name.startswith(f"{module_path}.") for name in registered
            ), f"'{module_path}' is imported by the worker but registers no task"
