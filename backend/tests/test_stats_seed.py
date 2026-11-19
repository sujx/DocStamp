"""Seed data has to land spread across the past two weeks.

seed_test_data() computed a random backdated timestamp and then dropped it:
log_operation() had no created_at parameter, so every seeded row took the
column default datetime('now') and the /status trend chart showed a single
spike instead of 14 days.  Pinned here: seeded rows carry their own timestamp,
the backdating survives the dashboard's window filter, and a row inserted
without created_at still falls back to the column default.
"""

import sqlite3
from datetime import UTC, datetime, timedelta

import pytest

import models
from config import Config
from services import stats

# The format the column default datetime('now') produces — no 'T', no offset.
DB_TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"


@pytest.fixture
def seed_db(tmp_path, monkeypatch):
    """A private task DB: seeding ~100 rows must not leak into other tests."""
    db_path = str(tmp_path / "tasks.db")
    monkeypatch.setattr(Config, "TASK_DB_PATH", db_path)
    # The service caches an OperationLog on first use.
    monkeypatch.setattr(stats, "_op_log", None)
    models.init_db(db_path)
    yield db_path
    models.close_db(db_path)


def _timestamps(db_path: str) -> list[str]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute("SELECT created_at FROM operation_logs").fetchall()
    finally:
        conn.close()
    return [r["created_at"] for r in rows]


class TestSeedTimestamps:

    def test_seeded_rows_are_backdated_within_fortnight(self, seed_db):
        result = stats.seed_test_data()
        assert result["skipped"] is False

        stamps = _timestamps(seed_db)
        assert len(stamps) == result["seeded"]
        assert all(s is not None for s in stamps)

        moments = [
            datetime.strptime(s, DB_TIMESTAMP_FORMAT).replace(tzinfo=UTC)
            for s in stamps
        ]
        now = datetime.now(UTC)
        assert all(m <= now for m in moments)
        assert all(now - m <= timedelta(days=15) for m in moments)

    def test_seeded_rows_span_more_than_one_day(self, seed_db):
        stats.seed_test_data()

        days = {s.split(" ")[0] for s in _timestamps(seed_db)}
        assert len(days) > 1

    def test_backdating_is_visible_through_the_window_filter(self, seed_db):
        result = stats.seed_test_data()

        since = (datetime.now(UTC) - timedelta(days=2)).isoformat()
        inside = sum(m["count"] for m in stats.aggregate_by_module(since))

        assert 0 < inside < result["seeded"]

    def test_omitting_created_at_still_uses_the_column_default(self, seed_db):
        op_log = stats._get_op_log()
        op_log.log_operation(session_id="probe", operation_type="convert")

        conn = sqlite3.connect(seed_db)
        conn.row_factory = sqlite3.Row
        try:
            row = conn.execute(
                "SELECT created_at FROM operation_logs WHERE session_id = 'probe'"
            ).fetchone()
        finally:
            conn.close()

        assert row["created_at"] is not None
        datetime.strptime(row["created_at"], DB_TIMESTAMP_FORMAT)
