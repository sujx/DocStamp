"""Data models for task tracking and operation auditing.

Uses raw SQL with parameterized queries — no ORM dependency.
Two tables: task_records (Celery task lifecycle) and operation_logs (audit trail).

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

CREATE TABLE IF NOT EXISTS company_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    website TEXT NOT NULL,
    source TEXT DEFAULT 'web',
    confirmed_at TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_company_name ON company_records(name);
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


# ── CompanyRecord Model ──────────────────────────────────────────────────

class CompanyRecord(BaseCRUD):
    """Local database of confirmed company name → website mappings.

    Serves as the primary lookup source. Web search results are only
    stored after the user confirms they are correct.
    """

    def __init__(self, db_path: str):
        super().__init__("company_records", db_path)

    def find_by_name(self, name: str) -> Optional[dict]:
        """Exact name match (case-insensitive via normalized name)."""
        normalized = _normalize_company_name(name)
        with self._conn() as db:
            row = db.execute(
                "SELECT * FROM company_records WHERE name=?",
                (normalized,),
            ).fetchone()
            return dict(row) if row else None

    def search_by_name(self, keyword: str) -> list[dict]:
        """Fuzzy search by name LIKE %keyword%."""
        normalized = _normalize_company_name(keyword)
        with self._conn() as db:
            rows = db.execute(
                "SELECT * FROM company_records WHERE name LIKE ? ORDER BY name LIMIT 50",
                (f"%{normalized}%",),
            ).fetchall()
            return [dict(r) for r in rows]

    def upsert(self, name: str, website: str, source: str = "web") -> dict:
        """Insert or update a company record. Returns the saved record."""
        normalized = _normalize_company_name(name)
        existing = self.find_by_name(normalized)
        now = datetime.now(timezone.utc).isoformat()
        if existing:
            data = {"website": website, "source": source, "updated_at": now}
            self.update_by_id(existing["id"], data)
            return {**existing, **data}
        else:
            data = {
                "name": normalized,
                "website": website,
                "source": source,
                "confirmed_at": now,
                "created_at": now,
                "updated_at": now,
            }
            self.insert(data)
            return self.find_by_name(normalized)

    def confirm(self, name: str, website: str, source: str = "web") -> None:
        """Mark a record as user-confirmed with timestamp.

        If the website differs from what's stored, update it too.
        """
        normalized = _normalize_company_name(name)
        now = datetime.now(timezone.utc).isoformat()
        existing = self.find_by_name(normalized)
        if existing:
            data = {
                "website": website,
                "source": source,
                "confirmed_at": now,
                "updated_at": now,
            }
            self.update_by_id(existing["id"], data)
        else:
            data = {
                "name": normalized,
                "website": website,
                "source": source,
                "confirmed_at": now,
                "created_at": now,
                "updated_at": now,
            }
            self.insert(data)

    def count(self) -> int:
        """Total number of company records in local DB."""
        with self._conn() as db:
            row = db.execute("SELECT COUNT(*) FROM company_records").fetchone()
            return row[0] if row else 0

    def list_all(self, page: int = 1, size: int = 50) -> list[dict]:
        """List all records with pagination, newest first."""
        with self._conn() as db:
            rows = db.execute(
                "SELECT * FROM company_records ORDER BY updated_at DESC LIMIT ? OFFSET ?",
                (size, (page - 1) * size),
            ).fetchall()
            return [dict(r) for r in rows]

    def export_all(self) -> list[dict]:
        """Return all confirmed records for export."""
        with self._conn() as db:
            rows = db.execute(
                "SELECT name, website, source, confirmed_at, created_at "
                "FROM company_records ORDER BY updated_at DESC"
            ).fetchall()
            return [dict(r) for r in rows]

    def import_batch(self, records: list[dict]) -> dict:
        """Batch upsert records. Returns {imported, skipped, errors}.

        Auto-corrects common URL mistakes:
        - Prepends https:// to bare domains (www.example.com → https://www.example.com)
        - Strips leading/trailing whitespace
        """
        from urllib.parse import urlparse

        imported = 0
        skipped = 0
        errors: list[str] = []

        for i, rec in enumerate(records):
            name = (rec.get("name") or "").strip()
            website = (rec.get("website") or "").strip()
            if not name or not website:
                errors.append(f"Row {i + 1}: missing name or website")
                skipped += 1
                continue

            # Auto-prepend https:// to bare domains
            if "://" not in website:
                website = "https://" + website.lstrip("/")

            # Validate the resulting URL has a valid hostname
            try:
                parsed = urlparse(website)
                if not parsed.hostname or "." not in parsed.hostname:
                    errors.append(f"Row {i + 1}: invalid domain for '{name}' — '{website}'")
                    skipped += 1
                    continue
            except Exception:
                errors.append(f"Row {i + 1}: cannot parse URL for '{name}'")
                skipped += 1
                continue

            try:
                self.upsert(name, website, source=rec.get("source", "import"))
                imported += 1
            except Exception as e:
                errors.append(f"Row {i + 1} ({name}): {e}")
                skipped += 1

        return {"imported": imported, "skipped": skipped, "errors": errors}


def _normalize_company_name(name: str) -> str:
    """Normalize company name for consistent lookup.

    - Lowercase
    - Strip whitespace
    - Remove parenthetical annotations: 腾讯科技（深圳）→ 腾讯科技
    - Remove common suffixes like 有限公司, Inc., Ltd., etc.
    """
    import re
    name = name.strip().lower()
    # Remove parenthetical annotations: （xxx）, (xxx), [xxx]
    name = re.sub(r"[（(]\s*[^）)]*\s*[）)]", "", name)
    name = re.sub(r"\[[^\]]*\]", "", name)
    # Remove common company suffixes for matching flexibility
    suffixes = [
        r"有限公司", r"股份有限公司", r"有限责任公司",
        r"inc\.?$", r"ltd\.?$", r"llc\.?$", r"corp\.?$",
        r"corporation\.?$", r"incorporated\.?$", r"limited\.?$",
        r"co\.?$", r"co\.,?\s*ltd\.?$",
    ]
    for suffix in suffixes:
        name = re.sub(suffix, "", name).strip()
    return name
