"""Scheduled cleanup of the upload folder.

The upload folder is not only temp files — it also holds the live stats counter
and the .gitkeep that keeps the directory in version control.  Cleanup must
recurse into the per-task output directories several blueprints create
(pdf2img_*, thumbs_*, task-id dirs, properties batch dirs) without touching
those two files.
"""

import os
import time
from datetime import datetime, timedelta, timezone

import pytest

from utils.file_cleanup import cleanup_due, cleanup_temp_files, run_cleanup

OLD_AGE_DAYS = 30


@pytest.fixture
def upload(tmp_path):
    """A fake upload folder with stale and fresh artefacts."""
    return str(tmp_path)


def _age(path: str, days: int = OLD_AGE_DAYS) -> None:
    """Backdate a file or directory so it looks stale."""
    stamp = time.time() - days * 86400
    os.utime(path, (stamp, stamp))


class TestFileCleanup:
    """Baseline file behaviour."""

    def test_stale_files_are_deleted(self, upload):
        stale = os.path.join(upload, "old.pdf")
        with open(stale, "wb") as f:
            f.write(b"x" * 100)
        _age(stale)

        result = cleanup_temp_files(upload, max_age_days=7)

        assert result["deleted_count"] == 1
        assert result["freed_bytes"] == 100
        assert not os.path.exists(stale)

    def test_fresh_files_survive(self, upload):
        fresh = os.path.join(upload, "new.pdf")
        with open(fresh, "wb") as f:
            f.write(b"y" * 50)

        result = cleanup_temp_files(upload, max_age_days=7)

        assert result["deleted_count"] == 0
        assert os.path.exists(fresh)

    def test_missing_folder_is_not_an_error(self, tmp_path):
        result = cleanup_temp_files(str(tmp_path / "nope"), max_age_days=7)
        assert result == {"deleted_count": 0, "freed_bytes": 0, "errors": 0}


class TestDirectoryCleanup:
    """Directories left behind by per-task output code must not accumulate."""

    def test_stale_directory_is_removed_with_its_contents(self, upload):
        stale_dir = os.path.join(upload, "pdf2img_abc123")
        os.makedirs(stale_dir)
        for name in ("page-1.png", "page-2.png"):
            with open(os.path.join(stale_dir, name), "wb") as f:
                f.write(b"z" * 10)
        _age(stale_dir)

        result = cleanup_temp_files(upload, max_age_days=7)

        assert not os.path.exists(stale_dir)
        assert result["freed_bytes"] == 20

    def test_nested_directory_contents_are_counted(self, upload):
        stale_dir = os.path.join(upload, "1234abcd")
        nested = os.path.join(stale_dir, "deep")
        os.makedirs(nested)
        with open(os.path.join(stale_dir, "a.bin"), "wb") as f:
            f.write(b"a" * 5)
        with open(os.path.join(nested, "b.bin"), "wb") as f:
            f.write(b"b" * 7)
        _age(stale_dir)
        _age(nested)

        result = cleanup_temp_files(upload, max_age_days=7)

        assert not os.path.exists(stale_dir)
        assert result["freed_bytes"] == 12

    def test_empty_stale_directory_is_removed(self, upload):
        stale_dir = os.path.join(upload, "thumbs_deadbeef")
        os.makedirs(stale_dir)
        _age(stale_dir)

        cleanup_temp_files(upload, max_age_days=7)

        assert not os.path.exists(stale_dir)

    def test_fresh_directory_survives(self, upload):
        fresh_dir = os.path.join(upload, "thumbs_recent")
        os.makedirs(fresh_dir)
        with open(os.path.join(fresh_dir, "p.png"), "wb") as f:
            f.write(b"p")

        cleanup_temp_files(upload, max_age_days=7)

        assert os.path.isdir(fresh_dir)
        assert os.path.isfile(os.path.join(fresh_dir, "p.png"))

    def test_mixed_files_and_directories(self, upload):
        cases = {
            "old.bin": True,
            "new.bin": False,
            "pdf2img_1": True,
            "pdf2img_2": False,
        }
        for name, stale in cases.items():
            path = os.path.join(upload, name)
            if name.startswith("pdf2img"):
                os.makedirs(path)
                with open(os.path.join(path, "inner.bin"), "wb") as f:
                    f.write(b"i" * 3)
            else:
                with open(path, "wb") as f:
                    f.write(b"f" * 3)
            if stale:
                _age(path)

        cleanup_temp_files(upload, max_age_days=7)

        assert not os.path.exists(os.path.join(upload, "old.bin"))
        assert not os.path.exists(os.path.join(upload, "pdf2img_1"))
        assert os.path.exists(os.path.join(upload, "new.bin"))
        assert os.path.exists(os.path.join(upload, "pdf2img_2"))


class TestLiveDataProtection:
    """The upload folder doubles as a home for live state — never delete it."""

    def test_stats_counter_survives_cleanup(self, upload):
        stats = os.path.join(upload, ".stats")
        with open(stats, "w") as f:
            f.write('{"total_conversions": 14}')
        _age(stats)

        result = cleanup_temp_files(upload, max_age_days=7)

        assert os.path.isfile(stats)
        assert result["deleted_count"] == 0

    def test_gitkeep_survives_cleanup(self, upload):
        gitkeep = os.path.join(upload, ".gitkeep")
        open(gitkeep, "wb").close()
        _age(gitkeep)

        cleanup_temp_files(upload, max_age_days=7)

        assert os.path.isfile(gitkeep)


class TestCleanupScheduling:
    """The daily cadence: gunicorn's master starts a daemon thread that runs
    cleanup when the stamp file says the last run is over 24h ago."""

    def test_due_when_never_run(self, tmp_path):
        assert cleanup_due(tmp_path / "stamp", datetime.now(timezone.utc)) is True

    def test_not_due_when_just_run(self, tmp_path):
        stamp = tmp_path / "stamp"
        run_cleanup(str(tmp_path), stamp, now=datetime.now(timezone.utc))

        assert cleanup_due(stamp, datetime.now(timezone.utc)) is False

    def test_due_when_last_run_over_a_day_ago(self, tmp_path):
        stamp = tmp_path / "stamp"
        run_cleanup(str(tmp_path), stamp,
                    now=datetime.now(timezone.utc) - timedelta(hours=25))

        assert cleanup_due(stamp, datetime.now(timezone.utc)) is True

    def test_due_when_stamp_is_corrupt(self, tmp_path):
        stamp = tmp_path / "stamp"
        stamp.write_text("garbage", encoding="utf-8")

        assert cleanup_due(stamp, datetime.now(timezone.utc)) is True

    def test_run_cleanup_deletes_aged_files_and_stamps(self, tmp_path, monkeypatch):
        calls = {}

        def fake_cleanup(folder, max_age_days=7):
            calls["args"] = (folder, max_age_days)
            return {"deleted_count": 2, "freed_bytes": 99, "errors": 0}

        import utils.file_cleanup as fc
        monkeypatch.setattr(fc, "cleanup_temp_files", fake_cleanup)

        stamp = tmp_path / "stamp"
        now = datetime.now(timezone.utc)

        fc.run_cleanup(str(tmp_path), stamp, now=now)

        assert calls["args"] == (str(tmp_path), 7)
        assert fc.cleanup_due(stamp, now) is False

    def test_run_cleanup_skips_a_missing_folder(self, tmp_path, monkeypatch):
        called = []
        import utils.file_cleanup as fc
        monkeypatch.setattr(fc, "cleanup_temp_files",
                            lambda *a, **k: called.append(a) or {})

        fc.run_cleanup(str(tmp_path / "nope"), tmp_path / "stamp")

        assert called == []
