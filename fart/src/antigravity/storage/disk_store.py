"""
Disk-Backed Local Persistence Engine for Antigravity Platform.

Provides SQLite-backed state serialization, file snapshot exports,
service worker task persistence, and model configuration tracking across restarts.
"""

from __future__ import annotations

import json
import os
import sqlite3
import threading
import time
from typing import Any, Dict, List, Optional, Tuple


class DiskStateStore:
    """
    Thread-safe SQLite + File Directory Persistence Engine.
    """

    def __init__(self, db_path: Optional[str] = None) -> None:
        if db_path is None:
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".antigravity", "storage"))
            os.makedirs(base_dir, exist_ok=True)
            db_path = os.path.join(base_dir, "persistence.db")
        else:
            os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)

        self.db_path = db_path
        self._lock = threading.RLock()
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Create a new SQLite connection configured for thread safety."""
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        """Initialize database schema tables if not existing."""
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            # 1. Sandboxes table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sandboxes (
                    sandbox_id TEXT PRIMARY KEY,
                    mode TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    last_active REAL NOT NULL,
                    state_json TEXT NOT NULL,
                    metadata_json TEXT NOT NULL
                )
            """)
            # 2. Snapshots table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS snapshots (
                    snapshot_id TEXT PRIMARY KEY,
                    sandbox_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    state_json TEXT NOT NULL,
                    FOREIGN KEY(sandbox_id) REFERENCES sandboxes(sandbox_id) ON DELETE CASCADE
                )
            """)
            # 3. Tasks table (Service Workers)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    task_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    trigger_type TEXT NOT NULL,
                    trigger_spec TEXT NOT NULL,
                    code TEXT NOT NULL,
                    sandbox_id TEXT,
                    status TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    last_run_at REAL,
                    run_count INTEGER NOT NULL DEFAULT 0,
                    task_json TEXT NOT NULL
                )
            """)
            # 4. Model Registry table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS model_registry (
                    model_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    architecture TEXT NOT NULL,
                    device TEXT NOT NULL,
                    weights_path TEXT,
                    status TEXT NOT NULL,
                    loaded_at REAL NOT NULL,
                    config_json TEXT NOT NULL
                )
            """)
            conn.commit()

    def save_sandbox(
        self,
        sandbox_id: str,
        mode: str,
        status: str,
        state_dict: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        created_at: Optional[float] = None,
    ) -> None:
        """Persist or update sandbox session state."""
        now = time.time()
        created = created_at or now
        meta_json = json.dumps(metadata or {})
        state_json = json.dumps(state_dict, default=str)

        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO sandboxes (sandbox_id, mode, status, created_at, last_active, state_json, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(sandbox_id) DO UPDATE SET
                    mode=excluded.mode,
                    status=excluded.status,
                    last_active=excluded.last_active,
                    state_json=excluded.state_json,
                    metadata_json=excluded.metadata_json
                """,
                (sandbox_id, mode, status, created, now, state_json, meta_json),
            )
            conn.commit()

    def load_sandbox(self, sandbox_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve persisted sandbox state dictionary."""
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM sandboxes WHERE sandbox_id = ?", (sandbox_id,))
            row = cursor.fetchone()
            if row is None:
                return None

            return {
                "sandbox_id": row["sandbox_id"],
                "mode": row["mode"],
                "status": row["status"],
                "created_at": row["created_at"],
                "last_active": row["last_active"],
                "state": json.loads(row["state_json"]),
                "metadata": json.loads(row["metadata_json"]),
            }

    def list_sandboxes(self) -> List[Dict[str, Any]]:
        """List summary of all persisted sandboxes."""
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT sandbox_id, mode, status, created_at, last_active FROM sandboxes ORDER BY last_active DESC")
            rows = cursor.fetchall()
            return [dict(r) for r in rows]

    def delete_sandbox(self, sandbox_id: str) -> bool:
        """Delete sandbox record and associated snapshots."""
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM snapshots WHERE sandbox_id = ?", (sandbox_id,))
            cursor.execute("DELETE FROM sandboxes WHERE sandbox_id = ?", (sandbox_id,))
            deleted = cursor.rowcount > 0
            conn.commit()
            return deleted

    def save_snapshot(
        self,
        snapshot_id: str,
        sandbox_id: str,
        name: str,
        state_dict: Dict[str, Any],
        timestamp: Optional[float] = None,
    ) -> None:
        """Persist snapshot state vector."""
        ts = timestamp or time.time()
        state_json = json.dumps(state_dict, default=str)

        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO snapshots (snapshot_id, sandbox_id, name, timestamp, state_json)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(snapshot_id) DO UPDATE SET
                    name=excluded.name,
                    timestamp=excluded.timestamp,
                    state_json=excluded.state_json
                """,
                (snapshot_id, sandbox_id, name, ts, state_json),
            )
            conn.commit()

    def load_snapshot(self, snapshot_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve snapshot by ID."""
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM snapshots WHERE snapshot_id = ?", (snapshot_id,))
            row = cursor.fetchone()
            if row is None:
                return None

            return {
                "snapshot_id": row["snapshot_id"],
                "sandbox_id": row["sandbox_id"],
                "name": row["name"],
                "timestamp": row["timestamp"],
                "state": json.loads(row["state_json"]),
            }

    def list_snapshots(self, sandbox_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List snapshots for a given sandbox or all sandboxes."""
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            if sandbox_id:
                cursor.execute(
                    "SELECT snapshot_id, sandbox_id, name, timestamp FROM snapshots WHERE sandbox_id = ? ORDER BY timestamp DESC",
                    (sandbox_id,),
                )
            else:
                cursor.execute(
                    "SELECT snapshot_id, sandbox_id, name, timestamp FROM snapshots ORDER BY timestamp DESC"
                )
            rows = cursor.fetchall()
            return [dict(r) for r in rows]

    def delete_snapshot(self, snapshot_id: str) -> bool:
        """Delete a snapshot by ID."""
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM snapshots WHERE snapshot_id = ?", (snapshot_id,))
            deleted = cursor.rowcount > 0
            conn.commit()
            return deleted

    def save_task(self, task_dict: Dict[str, Any]) -> None:
        """Persist service worker task state."""
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO tasks (task_id, name, trigger_type, trigger_spec, code, sandbox_id, status, created_at, last_run_at, run_count, task_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(task_id) DO UPDATE SET
                    name=excluded.name,
                    status=excluded.status,
                    last_run_at=excluded.last_run_at,
                    run_count=excluded.run_count,
                    task_json=excluded.task_json
                """,
                (
                    task_dict["task_id"],
                    task_dict.get("name", ""),
                    task_dict.get("trigger_type", "timer"),
                    task_dict.get("trigger_spec", ""),
                    task_dict.get("code", ""),
                    task_dict.get("sandbox_id"),
                    task_dict.get("status", "scheduled"),
                    task_dict.get("created_at", time.time()),
                    task_dict.get("last_run_at"),
                    task_dict.get("run_count", 0),
                    json.dumps(task_dict, default=str),
                ),
            )
            conn.commit()

    def list_tasks(self) -> List[Dict[str, Any]]:
        """List all persisted service worker tasks."""
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT task_json FROM tasks ORDER BY created_at DESC")
            rows = cursor.fetchall()
            return [json.loads(r["task_json"]) for r in rows]

    def register_model(
        self,
        model_id: str,
        name: str,
        architecture: str,
        device: str,
        status: str = "active",
        weights_path: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Register local model runner instance metadata."""
        now = time.time()
        config_json = json.dumps(config or {})

        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO model_registry (model_id, name, architecture, device, weights_path, status, loaded_at, config_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(model_id) DO UPDATE SET
                    name=excluded.name,
                    architecture=excluded.architecture,
                    device=excluded.device,
                    weights_path=excluded.weights_path,
                    status=excluded.status,
                    loaded_at=excluded.loaded_at,
                    config_json=excluded.config_json
                """,
                (model_id, name, architecture, device, weights_path, status, now, config_json),
            )
            conn.commit()

    def list_models(self) -> List[Dict[str, Any]]:
        """List registered local models."""
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM model_registry ORDER BY loaded_at DESC")
            rows = cursor.fetchall()
            res = []
            for r in rows:
                item = dict(r)
                item["config"] = json.loads(item.pop("config_json", "{}"))
                res.append(item)
            return res


class PersistenceManager:
    """High-level singleton manager for local disk persistence."""

    _instance: Optional["PersistenceManager"] = None
    _lock = threading.RLock()

    def __init__(self, db_path: Optional[str] = None) -> None:
        self.store = DiskStateStore(db_path=db_path)

    @classmethod
    def get_instance(cls, db_path: Optional[str] = None) -> "PersistenceManager":
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls(db_path=db_path)
            return cls._instance
