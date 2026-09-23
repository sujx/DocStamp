"""Tests for the SQLite-queue task worker.

Covers the queue primitives on TaskRecord (claim atomicity, skipping
non-pending rows, stale recovery), the worker's execution states, and the
API → worker payload handoff.
"""

import json
import os
from datetime import datetime, timedelta, timezone

import pytest

import worker
from errors import ErrorCode, ServiceResult
from models import TaskRecord, init_db


@pytest.fixture
def record(tmp_path):
    db_path = str(tmp_path / "tasks.db")
    init_db(db_path)
    return TaskRecord(db_path)


@pytest.fixture
def upload_dir(tmp_path):
    d = tmp_path / "output"
    d.mkdir()
    return str(d)


def _enqueue(record, task_id="t1", input_name="abc123_clip.mp4", output_name="out1.wmv",
             upload_dir=None):
    """Create a pending row the way the API blueprint does.

    Pass upload_dir to also materialise the source file on disk — the worker
    checks it exists before shelling out to ffmpeg.
    """
    record.create_task(
        task_id, "video_convert", "pdf_queue",
        result_data=json.dumps({"input": input_name, "output": output_name}),
    )
    if upload_dir:
        with open(os.path.join(upload_dir, input_name), "wb") as f:
            f.write(b"source-mp4")
    return task_id


def _fake_ffmpeg(seen=None, payload=b"0123456789"):
    """Build an mp4_to_wmv stub that writes a real output file and succeeds."""
    def stub(input_path, output_path):
        if seen is not None:
            seen.append((input_path, output_path))
        with open(output_path, "wb") as f:
            f.write(payload)
        return ServiceResult.ok({
            "input_size": 10, "output_size": len(payload), "duration_seconds": 1.0,
        })
    return stub


# ── Queue primitives ────────────────────────────────────────────────

class TestNextPending:
    def test_returns_none_when_queue_empty(self, record):
        assert record.next_pending() is None

    def test_returns_the_pending_row(self, record):
        _enqueue(record, "t1")

        row = record.next_pending()

        assert row["id"] == "t1"
        assert row["status"] == "pending"

    def test_returns_oldest_created_first(self, record):
        _enqueue(record, "new")
        _enqueue(record, "old")
        record.update_by_id("old", {"created_at": "2020-01-01 00:00:00"})

        assert record.next_pending()["id"] == "old"

    def test_breaks_same_second_ties_by_insertion_order(self, record):
        """created_at is only second-precise — rowid keeps FIFO deterministic."""
        _enqueue(record, "first")
        _enqueue(record, "second")

        assert record.next_pending()["id"] == "first"

    def test_skips_rows_that_are_not_pending(self, record):
        _enqueue(record, "t-started")
        record.update_progress("t-started", "started")
        _enqueue(record, "t-done")
        record.update_progress("t-done", "success", progress=100)

        assert record.next_pending() is None

    def test_skips_rows_of_other_task_types(self, record):
        record.create_task("t-other", "something_else", "pdf_queue")

        assert record.next_pending() is None


class TestClaim:
    def test_claims_a_pending_row(self, record):
        _enqueue(record, "t1")

        assert record.claim("t1") is True
        assert record.get_by_id("t1")["status"] == "started"

    def test_second_claim_loses(self, record):
        """rowcount is the lock — a row can only be claimed once."""
        _enqueue(record, "t1")

        assert record.claim("t1") is True
        assert record.claim("t1") is False

    def test_claim_of_terminal_row_fails(self, record):
        _enqueue(record, "t1")
        record.update_progress("t1", "failure", error_code="CONVERSION_FAILED")

        assert record.claim("t1") is False

    def test_claim_of_unknown_id_fails(self, record):
        assert record.claim("nope") is False


class TestListStale:
    def test_returns_started_and_progress_rows(self, record):
        _enqueue(record, "t-started")
        record.update_progress("t-started", "started")
        _enqueue(record, "t-progress")
        record.update_progress("t-progress", "progress", progress=20)

        assert {r["id"] for r in record.list_stale()} == {"t-started", "t-progress"}

    def test_ignores_pending_and_terminal_rows(self, record):
        _enqueue(record, "t-pending")
        _enqueue(record, "t-ok")
        record.update_progress("t-ok", "success", progress=100)
        _enqueue(record, "t-bad")
        record.update_progress("t-bad", "failure", error_code="CONVERSION_FAILED")

        assert record.list_stale() == []


class TestRecoverStaleTasks:
    def test_marks_in_flight_rows_failed(self, record):
        _enqueue(record, "t1")
        record.update_progress("t1", "progress", progress=20, message="Converting with ffmpeg...")

        assert worker.recover_stale_tasks(record) == 1

        row = record.get_by_id("t1")
        assert row["status"] == "failure"
        assert row["error_code"] == "TASK_FAILED"
        assert row["error_message"]

    def test_leaves_pending_rows_for_the_next_claim(self, record):
        _enqueue(record, "t1")

        assert worker.recover_stale_tasks(record) == 0
        assert record.get_by_id("t1")["status"] == "pending"

    def test_recovered_row_is_not_claimable(self, record):
        """Otherwise the worker would re-run a task it already gave up on."""
        _enqueue(record, "t1")
        record.update_progress("t1", "started")
        worker.recover_stale_tasks(record)

        assert record.claim("t1") is False


# ── Execution ───────────────────────────────────────────────────────

class TestExecuteTask:
    def test_success_writes_the_result_payload(self, record, upload_dir, monkeypatch):
        monkeypatch.setattr(worker, "mp4_to_wmv", _fake_ffmpeg())
        _enqueue(record, "t1", upload_dir=upload_dir)
        record.claim("t1")

        worker.execute_task(record, "t1", upload_dir)

        row = record.get_by_id("t1")
        assert row["status"] == "success"
        assert row["progress"] == 100
        assert json.loads(row["result_data"]) == {
            "filename": "abc123_clip.wmv",
            "download_id": "out1.wmv",
            "size": 10,
        }

    def test_passes_paths_inside_the_upload_folder(self, record, upload_dir, monkeypatch):
        seen = []
        monkeypatch.setattr(worker, "mp4_to_wmv", _fake_ffmpeg(seen=seen))
        _enqueue(record, "t1", upload_dir=upload_dir)
        record.claim("t1")

        worker.execute_task(record, "t1", upload_dir)

        assert seen == [
            (os.path.join(upload_dir, "abc123_clip.mp4"), os.path.join(upload_dir, "out1.wmv"))
        ]

    def test_reports_progress_while_converting(self, record, upload_dir, monkeypatch):
        """The SSE stream is the only progress UI — these states must be written."""
        observed = {}

        def stub(input_path, output_path):
            observed.update(record.get_by_id("t1"))
            with open(output_path, "wb") as f:
                f.write(b"x")
            return ServiceResult.ok({})

        monkeypatch.setattr(worker, "mp4_to_wmv", stub)
        _enqueue(record, "t1", upload_dir=upload_dir)
        record.claim("t1")

        worker.execute_task(record, "t1", upload_dir)

        assert observed["status"] == "progress"
        assert observed["progress"] == 20
        assert observed["progress_message"] == "Converting with ffmpeg..."

    def test_service_failure_records_conversion_failed(self, record, upload_dir, monkeypatch):
        monkeypatch.setattr(
            worker, "mp4_to_wmv",
            lambda i, o: ServiceResult.fail(ErrorCode.CONVERSION_FAILED, "ffmpeg error: boom"),
        )
        _enqueue(record, "t1", upload_dir=upload_dir)
        record.claim("t1")

        worker.execute_task(record, "t1", upload_dir)

        row = record.get_by_id("t1")
        assert row["status"] == "failure"
        assert row["error_code"] == "CONVERSION_FAILED"
        assert "boom" in row["error_message"]

    def test_unexpected_exception_records_task_failed(self, record, upload_dir, monkeypatch):
        def boom(input_path, output_path):
            raise RuntimeError("ffmpeg died")

        monkeypatch.setattr(worker, "mp4_to_wmv", boom)
        _enqueue(record, "t1", upload_dir=upload_dir)
        record.claim("t1")

        worker.execute_task(record, "t1", upload_dir)

        row = record.get_by_id("t1")
        assert row["status"] == "failure"
        assert row["error_code"] == "TASK_FAILED"
        assert "ffmpeg died" in row["error_message"]

    def test_missing_input_file_records_failure(self, record, upload_dir, monkeypatch):
        """Uploads age out of the folder independently of their task rows."""
        monkeypatch.setattr(worker, "mp4_to_wmv", _fake_ffmpeg())
        _enqueue(record, "t1", input_name="gone.mp4")
        record.claim("t1")

        worker.execute_task(record, "t1", upload_dir)

        row = record.get_by_id("t1")
        assert row["status"] == "failure"
        assert row["error_code"] == "CONVERSION_FAILED"

    def test_unparsable_payload_does_not_raise(self, record, upload_dir, monkeypatch):
        """A poison row must terminate, not wedge the poll loop."""
        monkeypatch.setattr(worker, "mp4_to_wmv", _fake_ffmpeg())
        record.create_task("t1", "video_convert", "pdf_queue", result_data="not json")
        record.claim("t1")

        worker.execute_task(record, "t1", upload_dir)

        assert record.get_by_id("t1")["status"] == "failure"


class TestRunPendingOnce:
    def test_processes_every_pending_row(self, record, upload_dir, monkeypatch):
        monkeypatch.setattr(worker, "mp4_to_wmv", _fake_ffmpeg())
        _enqueue(record, "t1", output_name="o1.wmv", upload_dir=upload_dir)
        _enqueue(record, "t2", output_name="o2.wmv", upload_dir=upload_dir)

        assert worker.run_pending_once(record, upload_dir) == 2
        assert record.get_by_id("t1")["status"] == "success"
        assert record.get_by_id("t2")["status"] == "success"

    def test_returns_zero_when_idle(self, record, upload_dir):
        assert worker.run_pending_once(record, upload_dir) == 0

    def test_one_bad_row_does_not_block_the_next(self, record, upload_dir, monkeypatch):
        def selective(input_path, output_path):
            if os.path.basename(input_path) == "bad.mp4":
                raise RuntimeError("nope")
            with open(output_path, "wb") as f:
                f.write(b"x")
            return ServiceResult.ok({})

        monkeypatch.setattr(worker, "mp4_to_wmv", selective)
        _enqueue(record, "t-bad", input_name="bad.mp4", upload_dir=upload_dir)
        _enqueue(record, "t-ok", input_name="ok.mp4", upload_dir=upload_dir)

        assert worker.run_pending_once(record, upload_dir) == 2
        assert record.get_by_id("t-bad")["status"] == "failure"
        assert record.get_by_id("t-ok")["status"] == "success"


# ── Daily cleanup scheduling ────────────────────────────────────────

class TestCleanupScheduling:
    def test_due_when_never_run(self, tmp_path):
        assert worker.cleanup_due(tmp_path / "stamp", datetime.now(timezone.utc)) is True

    def test_not_due_when_just_run(self, tmp_path):
        stamp = tmp_path / "stamp"
        worker._write_stamp(stamp, datetime.now(timezone.utc))

        assert worker.cleanup_due(stamp, datetime.now(timezone.utc)) is False

    def test_due_when_last_run_over_a_day_ago(self, tmp_path):
        stamp = tmp_path / "stamp"
        worker._write_stamp(stamp, datetime.now(timezone.utc) - timedelta(hours=25))

        assert worker.cleanup_due(stamp, datetime.now(timezone.utc)) is True

    def test_due_when_stamp_is_corrupt(self, tmp_path):
        stamp = tmp_path / "stamp"
        stamp.write_text("garbage", encoding="utf-8")

        assert worker.cleanup_due(stamp, datetime.now(timezone.utc)) is True

    def test_run_cleanup_deletes_aged_files_and_stamps(self, tmp_path, monkeypatch):
        calls = {}

        def fake_cleanup(folder, max_age_days=7):
            calls["args"] = (folder, max_age_days)
            return {"deleted_count": 2, "freed_bytes": 99, "errors": 0}

        monkeypatch.setattr(worker, "cleanup_temp_files", fake_cleanup)
        stamp = tmp_path / "stamp"
        now = datetime.now(timezone.utc)

        worker.run_cleanup(str(tmp_path), stamp, now=now)

        assert calls["args"] == (str(tmp_path), 7)
        assert worker.cleanup_due(stamp, now) is False

    def test_run_cleanup_skips_a_missing_folder(self, tmp_path, monkeypatch):
        called = []
        monkeypatch.setattr(
            worker, "cleanup_temp_files", lambda *a, **k: called.append(a) or {}
        )

        worker.run_cleanup(str(tmp_path / "nope"), tmp_path / "stamp")

        assert called == []


# ── API → worker handoff ────────────────────────────────────────────

@pytest.fixture
def isolated_db(monkeypatch, tmp_path):
    """Point the app at a throwaway DB before create_app() snapshots Config.

    Keeps the test suite off backend/tasks.db, which holds real usage stats.
    """
    from config import Config

    db_path = str(tmp_path / "tasks.db")
    init_db(db_path)
    monkeypatch.setattr(Config, "TASK_DB_PATH", db_path)
    return db_path


class TestApiToWorkerHandoff:
    """The payload the route writes must be exactly what the worker reads."""

    def test_post_enqueues_a_pending_task(self, isolated_db, app, client):
        import io

        resp = client.post(
            "/api/v1/video-convert",
            data={"file": (io.BytesIO(b"not really a video"), "clip.mp4")},
            content_type="multipart/form-data",
        )

        assert resp.status_code == 200, resp.get_data(as_text=True)
        task_id = resp.get_json()["task_id"]

        row = TaskRecord(isolated_db).get_by_id(task_id)
        assert row["status"] == "pending"
        assert row["task_type"] == "video_convert"
        payload = json.loads(row["result_data"])
        assert payload["output"] == f"{task_id}.wmv"
        assert os.path.isfile(os.path.join(app.config["UPLOAD_FOLDER"], payload["input"]))

    def test_queued_task_runs_to_success(self, isolated_db, app, client, monkeypatch):
        import io

        monkeypatch.setattr(worker, "mp4_to_wmv", _fake_ffmpeg())
        upload_dir = app.config["UPLOAD_FOLDER"]
        resp = client.post(
            "/api/v1/video-convert",
            data={"file": (io.BytesIO(b"not really a video"), "clip.mp4")},
            content_type="multipart/form-data",
        )
        task_id = resp.get_json()["task_id"]

        record = TaskRecord(isolated_db)
        assert worker.run_pending_once(record, upload_dir) == 1

        row = record.get_by_id(task_id)
        assert row["status"] == "success"
        result = json.loads(row["result_data"])
        assert result["download_id"] == f"{task_id}.wmv"
        assert result["filename"].endswith(".wmv")
        assert result["size"] == 10
        assert os.path.isfile(os.path.join(upload_dir, result["download_id"]))

    def test_no_file_still_returns_400(self, isolated_db, client):
        resp = client.post("/api/v1/video-convert", data={})

        assert resp.status_code == 400
