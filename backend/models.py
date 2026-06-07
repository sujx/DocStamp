"""Data models for task tracking and operation auditing.

Uses raw SQL with parameterized queries — no ORM dependency.
Two tables: task_records (Celery task lifecycle) and operation_logs (audit trail).

Lightweight SQLite backend; the BaseCRUD class provides reusable patterns.
"""

import sqlite3
import threading
from datetime import datetime, timezone
from typing import Optional

# ── Database Connection ─────────────────────────────────────────────────

_local = threading.local()


def _get_db(db_path: str) -> sqlite3.Connection:
    """Get a thread-local SQLite connection."""
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


# ── Schema ──────────────────────────────────────────────────────────────

SCHEMA_SQL = """
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


def init_db(db_path: str) -> None:
    """Initialize the database schema (idempotent)."""
    conn = _get_db(db_path)
    conn.executescript(SCHEMA_SQL)
    conn.commit()


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
    """Track Celery task lifecycle: pending → started → progress → success/failure."""

    VALID_STATUSES = {"pending", "started", "progress", "success", "failure"}

    def __init__(self, db_path: str):
        super().__init__("task_records", db_path)

    def create_task(self, task_id: str, task_type: str, queue: str) -> dict:
        """Create a new task record with status='pending'."""
        data = {
            "id": task_id,
            "task_type": task_type,
            "queue": queue,
            "status": "pending",
            "progress": 0,
        }
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
