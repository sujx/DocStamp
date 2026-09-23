"""Data models for task tracking and operation auditing.

Uses raw SQL with parameterized queries — no ORM dependency.
Two tables: task_records (task lifecycle + work queue) and operation_logs (audit trail).

Lightweight SQLite backend with WAL mode, thread-local connections,
and atexit cleanup to prevent connection leaks on shutdown.
"""

import atexit
import sqlite3
import threading
from datetime import datetime, timezone
from typing import Optional

# ── Database Connection ─────────────────────────────────────────────────

_local = threading.local()


def _get_db(db_path: str) -> sqlite3.Connection:
    """Get or create a thread-local SQLite connection (WAL, FK, busy timeout)."""
    if not hasattr(_local, "connections"):
        _local.connections = {}
    if db_path not in _local.connections:
        conn = sqlite3.connect(db_path, timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA busy_timeout=5000")
        _local.connections[db_path] = conn
    return _local.connections[db_path]


def close_db(db_path: str) -> None:
    """Close the thread-local connection for the given database path."""
    conns = getattr(_local, "connections", {})
    conn = conns.pop(db_path, None)
    if conn:
        conn.close()


# ── Schema ──────────────────────────────────────────────────────────────

SCHEMA_SQL = """
-- Schema versioning — allows safe migration in future releases
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS task_records (
    id TEXT PRIMARY KEY,
    task_type TEXT NOT NULL,
    queue TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    progress INTEGER DEFAULT 0,
    progress_message TEXT,
    result_data TEXT,
    error_code TEXT,
    error_message TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS operation_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    operation_type TEXT NOT NULL,
    resource_id TEXT,
    resource_type TEXT,
    file_size INTEGER,
    ip_address TEXT,
    user_agent TEXT,
    status TEXT DEFAULT 'success',
    error_code TEXT,
    duration_ms INTEGER,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_task_records_status ON task_records(status);
CREATE INDEX IF NOT EXISTS idx_task_records_created ON task_records(created_at);
CREATE INDEX IF NOT EXISTS idx_operation_logs_created ON operation_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_operation_logs_type ON operation_logs(operation_type);
"""

CURRENT_SCHEMA_VERSION = 2


def init_db(db_path: str) -> None:
    """Initialize database schema and apply any pending migrations.

    Idempotent — safe to call at every startup. The schema_version table
    tracks which migrations have been applied so we can add tables/columns
    in future releases without breaking existing installations.
    """
    conn = _get_db(db_path)
    conn.executescript(SCHEMA_SQL)

    # Record schema version so future migrations can be selective
    existing = conn.execute(
        "SELECT version FROM schema_version ORDER BY version DESC LIMIT 1"
    ).fetchone()

    if existing is None or existing["version"] < CURRENT_SCHEMA_VERSION:
        conn.execute(
            "INSERT OR REPLACE INTO schema_version (version) VALUES (?)",
            (CURRENT_SCHEMA_VERSION,),
        )
    conn.commit()

    # Register cleanup so connections close properly on process exit
    atexit.register(close_db, db_path)


# ── Base CRUD ───────────────────────────────────────────────────────────

class BaseCRUD:
    """Lightweight CRUD wrapper over raw SQL (no ORM)."""

    def __init__(self, table: str, db_path: str):
        self.table = table
        self.db_path = db_path

    def _conn(self) -> sqlite3.Connection:
        return _get_db(self.db_path)

    def get_by_id(self, id_value) -> Optional[dict]:
        """Get a single row by primary key."""
        with self._conn() as db:
            row = db.execute(
                f"SELECT * FROM {self.table} WHERE id=?", (id_value,)
            ).fetchone()
            return dict(row) if row else None

    def list_by_conditions(
        self, conditions: dict, page: int = 1, size: int = 20
    ) -> list[dict]:
        """List rows matching conditions with pagination."""
        where = " AND ".join(f"{k}=?" for k in conditions)
        sql = f"SELECT * FROM {self.table} WHERE {where} ORDER BY created_at DESC LIMIT ? OFFSET ?"
        with self._conn() as db:
            rows = db.execute(
                sql, (*conditions.values(), size, (page - 1) * size)
            ).fetchall()
            return [dict(r) for r in rows]

    def update_by_id(self, id_value, data: dict) -> None:
        """Update a row by primary key."""
        if not data:
            return
        data["updated_at"] = datetime.now(timezone.utc).isoformat()
        sets = ", ".join(f"{k}=?" for k in data)
        with self._conn() as db:
            db.execute(
                f"UPDATE {self.table} SET {sets} WHERE id=?",
                (*data.values(), id_value),
            )

    def insert(self, data: dict) -> str:
        """Insert a row and return the row ID."""
        columns = ", ".join(data.keys())
        placeholders = ", ".join("?" for _ in data)
        with self._conn() as db:
            cursor = db.execute(
                f"INSERT INTO {self.table} ({columns}) VALUES ({placeholders})",
                tuple(data.values()),
            )
            return str(cursor.lastrowid)


# ── TaskRecord Model ────────────────────────────────────────────────────

class TaskRecord(BaseCRUD):
    """Track task lifecycle: pending → started → progress → success/failure.

    Doubles as the work queue the video worker polls — see next_pending/claim.
    """

    VALID_STATUSES = {"pending", "started", "progress", "success", "failure"}
    # Rows a dead worker left behind mid-flight; recovered on worker startup.
    STALE_STATUSES = ("started", "progress")

    def __init__(self, db_path: str):
        super().__init__("task_records", db_path)

    def create_task(
        self, task_id: str, task_type: str, queue: str, result_data: str = ""
    ) -> dict:
        """Create a new task record with status='pending'.

        result_data carries the job payload until the worker overwrites it with
        the real result — the table has no payload column and the schema is frozen.
        """
        data = {
            "id": task_id,
            "task_type": task_type,
            "queue": queue,
            "status": "pending",
            "progress": 0,
        }
        if result_data:
            data["result_data"] = result_data
        self.insert(data)
        return self.get_by_id(task_id)

    def update_progress(
        self, task_id: str, status: str, progress: int = 0,
        message: str = "", result_data: str = "",
        error_code: str = "", error_message: str = "",
    ) -> None:
        """Update task status and progress atomically."""
        if status not in self.VALID_STATUSES:
            raise ValueError(f"Invalid task status: {status}")
        data = {"status": status, "progress": progress}
        if message:
            data["progress_message"] = message
        if result_data:
            data["result_data"] = result_data
        if error_code:
            data["error_code"] = error_code
        if error_message:
            data["error_message"] = error_message
        self.update_by_id(task_id, data)

    # ── Queue primitives (polled by backend/worker.py) ─────────────

    def next_pending(self, task_type: str = "video_convert") -> Optional[dict]:
        """Oldest claimable row of the given type, or None when the queue is idle."""
        with self._conn() as db:
            row = db.execute(
                """SELECT * FROM task_records
                   WHERE status='pending' AND task_type=?
                   ORDER BY created_at, rowid LIMIT 1""",
                (task_type,),
            ).fetchone()
            return dict(row) if row else None

    def claim(self, task_id: str) -> bool:
        """Atomically move a pending row to 'started'.

        The rowcount is the lock: exactly one caller sees 1, everyone else 0.
        """
        now = datetime.now(timezone.utc).isoformat()
        with self._conn() as db:
            cursor = db.execute(
                """UPDATE task_records
                   SET status='started', progress=0, updated_at=?
                   WHERE id=? AND status='pending'""",
                (now, task_id),
            )
            return cursor.rowcount == 1

    def list_stale(self) -> list[dict]:
        """Rows left in-flight by a worker that died mid-task."""
        placeholders = ", ".join("?" for _ in self.STALE_STATUSES)
        with self._conn() as db:
            rows = db.execute(
                f"SELECT * FROM task_records WHERE status IN ({placeholders})",
                self.STALE_STATUSES,
            ).fetchall()
            return [dict(r) for r in rows]


# ── OperationLog Model ──────────────────────────────────────────────────

class OperationLog(BaseCRUD):
    """Audit trail for document processing operations."""

    def __init__(self, db_path: str):
        super().__init__("operation_logs", db_path)

    def log_operation(
        self, session_id: str, operation_type: str,
        resource_id: str = "", resource_type: str = "",
        file_size: int = 0, ip_address: str = "",
        user_agent: str = "", status: str = "success",
        error_code: str = "", duration_ms: int = 0,
    ) -> str:
        """Record an operation in the audit log."""
        data = {
            "session_id": session_id,
            "operation_type": operation_type,
            "resource_id": resource_id,
            "resource_type": resource_type,
            "file_size": file_size,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "status": status,
            "error_code": error_code,
            "duration_ms": duration_ms,
        }
        return self.insert(data)

    # ── Aggregate queries for the status dashboard ─────────────────

    def _count_all(self) -> int:
        """Total number of operation log rows."""
        with self._conn() as db:
            row = db.execute(
                "SELECT COUNT(*) FROM operation_logs"
            ).fetchone()
            return row[0] if row else 0

    def _by_module(self, since: str) -> list[dict]:
        """Call counts grouped by operation_type since a given timestamp."""
        with self._conn() as db:
            rows = db.execute(
                """SELECT operation_type, COUNT(*) AS cnt
                   FROM operation_logs
                   WHERE created_at >= ?
                   GROUP BY operation_type""",
                (since,),
            ).fetchall()
            return [dict(r) for r in rows]

    def _daily_counts(self, since: str) -> list[dict]:
        """Daily call count for trend chart."""
        with self._conn() as db:
            rows = db.execute(
                """SELECT DATE(created_at) AS date, COUNT(*) AS cnt
                   FROM operation_logs
                   WHERE created_at >= ?
                   GROUP BY DATE(created_at)
                   ORDER BY date""",
                (since,),
            ).fetchall()
            return [dict(r) for r in rows]

    def _count_distinct_ips(self, since: str) -> int:
        """Count unique visitor IPs since a given timestamp."""
        with self._conn() as db:
            row = db.execute(
                """SELECT COUNT(DISTINCT ip_address)
                   FROM operation_logs
                   WHERE created_at >= ? AND ip_address != ''""",
                (since,),
            ).fetchone()
            return row[0] if row else 0
