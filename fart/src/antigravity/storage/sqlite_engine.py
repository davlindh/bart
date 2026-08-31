"""SQLite database engine with WAL mode, foreign keys, thread-safety, and migrations."""

from __future__ import annotations

import logging
import os
import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Generator, List, Optional, Tuple, Union

from .models import StorageConfig, StorageError

logger = logging.getLogger("antigravity.storage.sqlite_engine")

SCHEMA_VERSION = "1.0.0"

SCHEMA_SQL = """
-- 1. Metadata and Version Tracking
CREATE TABLE IF NOT EXISTS schema_meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at REAL NOT NULL
);

-- 2. Sandboxes Session Registry
CREATE TABLE IF NOT EXISTS sandboxes (
    sandbox_id TEXT PRIMARY KEY,
    mode TEXT NOT NULL DEFAULT 'local',
    status TEXT NOT NULL DEFAULT 'running',
    config_json TEXT NOT NULL,
    work_dir TEXT,
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL,
    last_active_at REAL NOT NULL,
    current_branch_id TEXT,
    metadata_json TEXT DEFAULT '{}'
);

-- 3. Sandbox Variables (Active REPL Namespace)
CREATE TABLE IF NOT EXISTS sandbox_variables (
    var_id TEXT PRIMARY KEY,
    sandbox_id TEXT NOT NULL,
    name TEXT NOT NULL,
    type_name TEXT NOT NULL,
    repr_str TEXT,
    codec TEXT NOT NULL,
    inline_data TEXT,
    blob_hash TEXT,
    size_bytes INTEGER NOT NULL DEFAULT 0,
    is_restorable INTEGER NOT NULL DEFAULT 1,
    updated_at REAL NOT NULL,
    FOREIGN KEY (sandbox_id) REFERENCES sandboxes(sandbox_id) ON DELETE CASCADE,
    UNIQUE(sandbox_id, name)
);

-- 4. Multi-Branch Snapshots (State Vector DAG)
CREATE TABLE IF NOT EXISTS snapshots (
    snapshot_id TEXT PRIMARY KEY,
    sandbox_id TEXT NOT NULL,
    name TEXT NOT NULL,
    parent_snapshot_id TEXT,
    branch_name TEXT NOT NULL DEFAULT 'main',
    created_at REAL NOT NULL,
    state_vector_json TEXT NOT NULL,
    blob_manifest_json TEXT NOT NULL,
    variable_count INTEGER NOT NULL DEFAULT 0,
    metadata_json TEXT DEFAULT '{}',
    FOREIGN KEY (sandbox_id) REFERENCES sandboxes(sandbox_id) ON DELETE CASCADE,
    FOREIGN KEY (parent_snapshot_id) REFERENCES snapshots(snapshot_id) ON DELETE SET NULL
);

-- 5. Scheduled Worker Tasks
CREATE TABLE IF NOT EXISTS scheduled_tasks (
    task_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    trigger_type TEXT NOT NULL,
    trigger_spec TEXT NOT NULL,
    code TEXT NOT NULL,
    sandbox_id TEXT,
    status TEXT NOT NULL DEFAULT 'scheduled',
    created_at REAL NOT NULL,
    next_run_at REAL,
    last_run_at REAL,
    run_count INTEGER NOT NULL DEFAULT 0,
    max_runs INTEGER,
    timeout REAL NOT NULL DEFAULT 60.0,
    metadata_json TEXT DEFAULT '{}',
    updated_at REAL NOT NULL,
    FOREIGN KEY (sandbox_id) REFERENCES sandboxes(sandbox_id) ON DELETE SET NULL
);

-- 6. Task Execution Records & Audit Logs
CREATE TABLE IF NOT EXISTS task_execution_records (
    execution_id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL,
    started_at REAL NOT NULL,
    finished_at REAL,
    duration_ms REAL NOT NULL DEFAULT 0.0,
    exit_code INTEGER NOT NULL DEFAULT 0,
    stdout TEXT DEFAULT '',
    stderr TEXT DEFAULT '',
    result_repr TEXT,
    error TEXT,
    artifacts_json TEXT DEFAULT '[]',
    state_json TEXT DEFAULT '{}',
    sandbox_backend TEXT NOT NULL DEFAULT 'local',
    created_at REAL NOT NULL,
    FOREIGN KEY (task_id) REFERENCES scheduled_tasks(task_id) ON DELETE CASCADE
);

-- 7. Model Configurations & Inference Metadata
CREATE TABLE IF NOT EXISTS model_configurations (
    model_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    architecture TEXT NOT NULL,
    model_path TEXT NOT NULL,
    tokenizer_path TEXT,
    device TEXT NOT NULL DEFAULT 'cpu',
    dtype TEXT NOT NULL DEFAULT 'float32',
    quantization TEXT,
    context_window INTEGER NOT NULL DEFAULT 4096,
    generation_params_json TEXT DEFAULT '{}',
    metadata_json TEXT DEFAULT '{}',
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL
);

-- 8. Content-Addressed Blob Registry
CREATE TABLE IF NOT EXISTS blob_registry (
    blob_hash TEXT PRIMARY KEY,
    relative_path TEXT NOT NULL,
    size_bytes INTEGER NOT NULL,
    mime_type TEXT NOT NULL DEFAULT 'application/octet-stream',
    ref_count INTEGER NOT NULL DEFAULT 1,
    created_at REAL NOT NULL
);

-- Indexes for high-frequency queries
CREATE INDEX IF NOT EXISTS idx_sandboxes_status ON sandboxes(status);
CREATE INDEX IF NOT EXISTS idx_sandbox_vars_sb ON sandbox_variables(sandbox_id);
CREATE INDEX IF NOT EXISTS idx_snapshots_sb ON snapshots(sandbox_id);
CREATE INDEX IF NOT EXISTS idx_snapshots_parent ON snapshots(parent_snapshot_id);
CREATE INDEX IF NOT EXISTS idx_snapshots_branch ON snapshots(sandbox_id, branch_name);
CREATE INDEX IF NOT EXISTS idx_tasks_status_next ON scheduled_tasks(status, next_run_at);
CREATE INDEX IF NOT EXISTS idx_exec_records_task_time ON task_execution_records(task_id, started_at DESC);
CREATE INDEX IF NOT EXISTS idx_models_arch ON model_configurations(architecture);
"""


class SQLiteEngine:
    """
    SQLite connection manager and database execution engine with WAL mode,
    foreign keys, busy timeouts, and thread-safe connection handling.
    """

    def __init__(self, config: Optional[StorageConfig] = None) -> None:
        self.config = config or StorageConfig()
        self.db_path = self.config.get_db_path()
        self._local = threading.local()
        self._lock = threading.RLock()
        self._open_connections: List[sqlite3.Connection] = []

        # Ensure parent directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize_schema()

    def _create_connection(self) -> sqlite3.Connection:
        """Create and configure a new SQLite connection."""
        conn = sqlite3.connect(
            str(self.db_path),
            timeout=float(self.config.busy_timeout_ms) / 1000.0,
            check_same_thread=False,
            isolation_level=None,  # Autocommit mode by default; manual transactions via BEGIN
        )
        conn.row_factory = sqlite3.Row
        
        # Configure PRAGMAs
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA busy_timeout = {self.config.busy_timeout_ms};")
        cursor.execute("PRAGMA foreign_keys = ON;")
        if self.config.wal_mode:
            cursor.execute("PRAGMA journal_mode = WAL;")
            cursor.execute("PRAGMA synchronous = NORMAL;")
        cursor.close()

        with self._lock:
            self._open_connections.append(conn)

        return conn

    def _get_connection(self) -> sqlite3.Connection:
        """Retrieve or create thread-local database connection."""
        conn = getattr(self._local, "conn", None)
        if conn is None:
            conn = self._create_connection()
            self._local.conn = conn
        return conn

    def initialize_schema(self) -> None:
        """Initialize all 8 tables and indices if not already present."""
        with self._lock:
            conn = self._get_connection()
            with conn:
                conn.executescript(SCHEMA_SQL)
                # Check / set schema version
                cursor = conn.cursor()
                cursor.execute("SELECT value FROM schema_meta WHERE key = 'version'")
                row = cursor.fetchone()
                import time
                if row is None:
                    cursor.execute(
                        "INSERT INTO schema_meta (key, value, updated_at) VALUES ('version', ?, ?)",
                        (SCHEMA_VERSION, time.time()),
                    )
                cursor.close()

    @contextmanager
    def connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Context manager yielding the active connection."""
        conn = self._get_connection()
        yield conn

    @contextmanager
    def transaction(self) -> Generator[sqlite3.Cursor, None, None]:
        """
        Context manager for atomic transaction execution (BEGIN IMMEDIATE).
        Rolls back automatically on exception, commits on successful block exit.
        """
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("BEGIN IMMEDIATE")
            try:
                yield cursor
                conn.execute("COMMIT")
            except Exception:
                conn.execute("ROLLBACK")
                raise
            finally:
                cursor.close()

    def execute_query(self, sql: str, params: Union[tuple, dict] = ()) -> List[sqlite3.Row]:
        """Execute a SELECT query and return all matching rows."""
        with self.connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(sql, params)
                return cursor.fetchall()
            finally:
                cursor.close()

    def execute_single(self, sql: str, params: Union[tuple, dict] = ()) -> Optional[sqlite3.Row]:
        """Execute a SELECT query and return the first matching row, or None."""
        with self.connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(sql, params)
                return cursor.fetchone()
            finally:
                cursor.close()

    def execute_non_query(self, sql: str, params: Union[tuple, dict] = ()) -> int:
        """Execute an INSERT, UPDATE, or DELETE query outside explicit transaction."""
        with self._lock:
            with self.connection() as conn:
                cursor = conn.cursor()
                try:
                    cursor.execute(sql, params)
                    return cursor.rowcount
                finally:
                    cursor.close()

    def close(self) -> None:
        """Close all open connections held by this engine instance."""
        with self._lock:
            for conn in self._open_connections:
                try:
                    conn.close()
                except Exception:
                    pass
            self._open_connections.clear()
            if hasattr(self._local, "conn"):
                self._local.conn = None
