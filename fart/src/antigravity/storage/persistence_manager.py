"""Unified high-level PersistenceManager orchestrating SQLite database, disk store, and variable serialization."""

from __future__ import annotations

import json
import logging
import time
import uuid
from typing import Any, Dict, List, Optional, Tuple, Union

from .disk_store import DiskStateStore
from .models import (
    CodecType,
    PersistedModelConfig,
    PersistedSandboxRecord,
    PersistedSnapshotRecord,
    StateVectorManifest,
    StorageConfig,
    StorageError,
    StorageNotFoundError,
    VariableDescriptor,
)
from .serializer import VariableSerializer
from .sqlite_engine import SQLiteEngine

# Scheduler models for typing & reconstruction
try:
    from antigravity.scheduler.models import (
        ScheduledTask,
        TaskExecutionRecord,
        TaskStatus,
        TaskTriggerType,
    )
except ImportError:
    ScheduledTask = None
    TaskExecutionRecord = None
    TaskStatus = None
    TaskTriggerType = None

# Sandbox models for typing & restoration
try:
    from antigravity.sandbox.base import BaseSandbox
    from antigravity.sandbox.local_sandbox import LocalSandbox
except ImportError:
    BaseSandbox = None
    LocalSandbox = None

logger = logging.getLogger("antigravity.storage.persistence_manager")


class PersistenceManager:
    """
    Unified disk persistence orchestrator managing sandboxes, multi-branch snapshot DAGs,
    scheduled task registries, execution history logs, and model configurations across process boundaries.
    """

    def __init__(
        self,
        config: Optional[StorageConfig] = None,
        base_dir: Optional[str] = None,
    ) -> None:
        if config is not None:
            self.config = config
        elif base_dir is not None:
            self.config = StorageConfig(base_dir=base_dir)
        else:
            self.config = StorageConfig()

        self.disk_store = DiskStateStore(self.config)
        self.engine = SQLiteEngine(self.config)
        self.serializer = VariableSerializer(
            self.disk_store, max_inline_bytes=self.config.max_inline_bytes
        )

    # -------------------------------------------------------------------------
    # Sandbox Session Persistence & Process Boundary Restoration
    # -------------------------------------------------------------------------

    def save_sandbox(
        self,
        sandbox_or_id: Union[Any, str],
        mode: str = "local",
        env: Optional[Dict[str, str]] = None,
        variables: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        work_dir: Optional[str] = None,
        branch_name: str = "main",
    ) -> PersistedSandboxRecord:
        """
        Export sandbox variables, serialize state vector to disk, and persist session in SQLite.
        Supports passing either a BaseSandbox instance or explicit sandbox parameters.
        """
        now = time.time()
        config_data: Dict[str, Any] = {}

        # 1. Inspect if sandbox instance is passed
        if hasattr(sandbox_or_id, "sandbox_id"):
            sb = sandbox_or_id
            sandbox_id = getattr(sb, "sandbox_id")
            mode_val = getattr(sb, "mode", "local")
            mode_str = mode_val.value if hasattr(mode_val, "value") else str(mode_val)
            status_val = getattr(sb, "status", "running")
            status_str = status_val.value if hasattr(status_val, "value") else str(status_val)
            work_dir = getattr(sb, "work_dir", work_dir)
            sb_env = getattr(sb, "_env", {})
            config_data["env"] = sb_env
            config_data["timeout"] = getattr(sb, "_timeout", 300.0)
            config_data["authorized_imports"] = getattr(sb, "_authorized_imports", [])

            if variables is None and hasattr(sb, "export_state"):
                try:
                    variables = sb.export_state()
                except Exception as e:
                    logger.warning("Failed exporting state from sandbox %s: %s", sandbox_id, e)
                    variables = {}
            elif variables is None:
                variables = {}
        else:
            sandbox_id = str(sandbox_or_id)
            mode_str = mode.value if hasattr(mode, "value") else str(mode)
            status_str = "running"
            config_data["env"] = env or {}
            variables = variables or {}

        metadata_dict = metadata or {}
        config_json = json.dumps(config_data, ensure_ascii=False)
        meta_json = json.dumps(metadata_dict, ensure_ascii=False)

        # 2. Serialize variables into StateVectorManifest
        manifest = self.serializer.serialize_namespace(variables, sandbox_id=sandbox_id)
        var_count = len(manifest.variables)

        # 3. Store in SQLite in transaction
        with self.engine.transaction() as cur:
            # Check existing sandbox
            cur.execute("SELECT created_at, current_branch_id FROM sandboxes WHERE sandbox_id = ?", (sandbox_id,))
            existing = cur.fetchone()
            if existing:
                created_at = existing["created_at"]
                current_branch_id = existing["current_branch_id"]
                cur.execute(
                    """
                    UPDATE sandboxes
                    SET mode = ?, status = ?, config_json = ?, work_dir = ?, updated_at = ?, last_active_at = ?, metadata_json = ?
                    WHERE sandbox_id = ?
                    """,
                    (mode_str, status_str, config_json, work_dir, now, now, meta_json, sandbox_id),
                )
            else:
                created_at = now
                current_branch_id = None
                cur.execute(
                    """
                    INSERT INTO sandboxes (sandbox_id, mode, status, config_json, work_dir, created_at, updated_at, last_active_at, current_branch_id, metadata_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (sandbox_id, mode_str, status_str, config_json, work_dir, created_at, now, now, current_branch_id, meta_json),
                )

            # Clean and insert variables
            cur.execute("DELETE FROM sandbox_variables WHERE sandbox_id = ?", (sandbox_id,))
            for var_name, descriptor in manifest.variables.items():
                var_id = f"{sandbox_id}:{var_name}"
                cur.execute(
                    """
                    INSERT INTO sandbox_variables (var_id, sandbox_id, name, type_name, repr_str, codec, inline_data, blob_hash, size_bytes, is_restorable, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        var_id,
                        sandbox_id,
                        descriptor.name,
                        descriptor.type_name,
                        descriptor.repr_str,
                        descriptor.encoding,
                        descriptor.inline_data,
                        descriptor.blob_hash,
                        descriptor.size_bytes,
                        1 if descriptor.is_restorable else 0,
                        now,
                    ),
                )

        return PersistedSandboxRecord(
            sandbox_id=sandbox_id,
            mode=mode_str,
            status=status_str,
            config_json=config_json,
            work_dir=work_dir,
            created_at=created_at,
            updated_at=now,
            last_active_at=now,
            current_branch_id=current_branch_id,
            variable_count=var_count,
            metadata=metadata_dict,
        )

    def load_sandbox(self, sandbox_id: str) -> Optional[Tuple[PersistedSandboxRecord, Dict[str, Any]]]:
        """
        Load sandbox metadata and deserialize all stored session variables.
        Returns (PersistedSandboxRecord, variables_dict) or None.
        """
        row = self.engine.execute_single("SELECT * FROM sandboxes WHERE sandbox_id = ?", (sandbox_id,))
        if row is None:
            return None

        # Load variables
        var_rows = self.engine.execute_query(
            "SELECT * FROM sandbox_variables WHERE sandbox_id = ?", (sandbox_id,)
        )
        variables_manifest: Dict[str, VariableDescriptor] = {}
        for vr in var_rows:
            desc = VariableDescriptor(
                name=vr["name"],
                type_name=vr["type_name"],
                codec=vr["codec"],
                inline_data=vr["inline_data"],
                blob_hash=vr["blob_hash"],
                size_bytes=vr["size_bytes"],
                repr_str=vr["repr_str"] or "",
                is_restorable=bool(vr["is_restorable"]),
            )
            variables_manifest[vr["name"]] = desc

        manifest = StateVectorManifest(
            sandbox_id=sandbox_id,
            timestamp=row["updated_at"],
            variables=variables_manifest,
        )
        deserialized_vars = self.serializer.deserialize_namespace(manifest)

        meta = json.loads(row["metadata_json"] or "{}")
        record = PersistedSandboxRecord(
            sandbox_id=row["sandbox_id"],
            mode=row["mode"],
            status=row["status"],
            config_json=row["config_json"],
            work_dir=row["work_dir"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            last_active_at=row["last_active_at"],
            current_branch_id=row["current_branch_id"],
            variable_count=len(variables_manifest),
            metadata=meta,
        )
        return record, deserialized_vars

    def restore_sandbox(self, sandbox_id: str, auto_start: bool = True) -> Any:
        """
        Load sandbox metadata from disk and spin up a fully hydrated LocalSandbox in current process.
        """
        loaded = self.load_sandbox(sandbox_id)
        if loaded is None:
            raise StorageNotFoundError(f"Persisted sandbox '{sandbox_id}' not found in storage.")

        record, variables = loaded
        config_data = json.loads(record.config_json or "{}")
        env = config_data.get("env", {})
        timeout = float(config_data.get("timeout", 300.0))
        authorized_imports = config_data.get("authorized_imports", [])

        from antigravity.sandbox.local_sandbox import LocalSandbox

        sandbox = LocalSandbox(
            sandbox_id=record.sandbox_id,
            timeout=timeout,
            env=env,
            authorized_imports=authorized_imports,
            work_dir=record.work_dir,
            auto_start=auto_start,
        )

        if auto_start and variables:
            sandbox.hydrate_state(variables)

        return sandbox

    def list_persisted_sandboxes(self) -> List[PersistedSandboxRecord]:
        """List all persisted sandbox sessions in storage."""
        rows = self.engine.execute_query(
            """
            SELECT s.*, COUNT(v.var_id) as var_count
            FROM sandboxes s
            LEFT JOIN sandbox_variables v ON s.sandbox_id = v.sandbox_id
            GROUP BY s.sandbox_id
            ORDER BY s.updated_at DESC
            """
        )
        records: List[PersistedSandboxRecord] = []
        for r in rows:
            meta = json.loads(r["metadata_json"] or "{}")
            records.append(
                PersistedSandboxRecord(
                    sandbox_id=r["sandbox_id"],
                    mode=r["mode"],
                    status=r["status"],
                    config_json=r["config_json"],
                    work_dir=r["work_dir"],
                    created_at=r["created_at"],
                    updated_at=r["updated_at"],
                    last_active_at=r["last_active_at"],
                    current_branch_id=r["current_branch_id"],
                    variable_count=r["var_count"],
                    metadata=meta,
                )
            )
        return records

    def delete_persisted_sandbox(self, sandbox_id: str) -> bool:
        """Delete persisted sandbox session, variables, and snapshots from storage."""
        with self.engine.transaction() as cur:
            cur.execute("DELETE FROM sandboxes WHERE sandbox_id = ?", (sandbox_id,))
            return cur.rowcount > 0

    # -------------------------------------------------------------------------
    # Multi-Branch Snapshot State Vector DAG
    # -------------------------------------------------------------------------

    def save_snapshot(
        self,
        sandbox_id: str,
        snapshot_id: Optional[str] = None,
        name: Optional[str] = None,
        variables: Optional[Dict[str, Any]] = None,
        parent_snapshot_id: Optional[str] = None,
        parent_id: Optional[str] = None,
        branch_name: str = "main",
        description: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> PersistedSnapshotRecord:
        """
        Capture and persist a snapshot state vector for multi-branch exploration.
        """
        now = time.time()
        parent_snap = parent_snapshot_id or parent_id
        snap_id = snapshot_id or f"snap_{uuid.uuid4().hex[:12]}"
        snap_name = name or snapshot_id or f"checkpoint_{snap_id[:8]}"

        # If variables are not explicitly supplied, extract from sandbox table or load
        if variables is None:
            loaded = self.load_sandbox(sandbox_id)
            if loaded is not None:
                variables = loaded[1]
            else:
                variables = {}

        manifest = self.serializer.serialize_namespace(variables, sandbox_id=sandbox_id)
        blob_manifest = {
            k: v.blob_hash for k, v in manifest.variables.items() if v.blob_hash is not None
        }

        manifest_json = json.dumps(manifest.to_dict(), ensure_ascii=False)
        blob_manifest_json = json.dumps(blob_manifest, ensure_ascii=False)
        meta_dict = metadata or {}
        if description:
            meta_dict["description"] = description
        meta_json = json.dumps(meta_dict, ensure_ascii=False)

        with self.engine.transaction() as cur:
            # Ensure sandbox exists in sandboxes table
            cur.execute("SELECT sandbox_id FROM sandboxes WHERE sandbox_id = ?", (sandbox_id,))
            if not cur.fetchone():
                cur.execute(
                    """
                    INSERT INTO sandboxes (sandbox_id, mode, status, config_json, created_at, updated_at, last_active_at)
                    VALUES (?, 'local', 'running', '{}', ?, ?, ?)
                    """,
                    (sandbox_id, now, now, now),
                )

            # Insert snapshot
            cur.execute(
                """
                INSERT OR REPLACE INTO snapshots (
                    snapshot_id, sandbox_id, name, parent_snapshot_id, branch_name,
                    created_at, state_vector_json, blob_manifest_json, variable_count, metadata_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    snap_id,
                    sandbox_id,
                    snap_name,
                    parent_snap,
                    branch_name,
                    now,
                    manifest_json,
                    blob_manifest_json,
                    len(manifest.variables),
                    meta_json,
                ),
            )

            # Update sandbox current_branch_id
            cur.execute(
                "UPDATE sandboxes SET current_branch_id = ?, updated_at = ? WHERE sandbox_id = ?",
                (snap_id, now, sandbox_id),
            )

        return PersistedSnapshotRecord(
            snapshot_id=snap_id,
            sandbox_id=sandbox_id,
            name=snap_name,
            parent_snapshot_id=parent_snap,
            branch_name=branch_name,
            created_at=now,
            state_vector=manifest,
            variable_count=len(manifest.variables),
            description=description,
            blob_manifest=blob_manifest,
            metadata=meta_dict,
        )

    def load_snapshot(
        self, sandbox_id: str, snapshot_id: str
    ) -> Optional[Tuple[PersistedSnapshotRecord, Dict[str, Any]]]:
        """
        Load snapshot metadata and deserialize its state vector into active variables.
        """
        row = self.engine.execute_single(
            "SELECT * FROM snapshots WHERE snapshot_id = ? AND (sandbox_id = ? OR ? = '')",
            (snapshot_id, sandbox_id, sandbox_id),
        )
        if row is None:
            # Fallback without sandbox_id constraint if sandbox_id was omitted
            row = self.engine.execute_single("SELECT * FROM snapshots WHERE snapshot_id = ?", (snapshot_id,))
            if row is None:
                return None

        manifest_dict = json.loads(row["state_vector_json"])
        manifest = StateVectorManifest.from_dict(manifest_dict)
        deserialized_vars = self.serializer.deserialize_namespace(manifest)
        blob_manifest = json.loads(row["blob_manifest_json"] or "{}")
        meta = json.loads(row["metadata_json"] or "{}")

        record = PersistedSnapshotRecord(
            snapshot_id=row["snapshot_id"],
            sandbox_id=row["sandbox_id"],
            name=row["name"],
            parent_snapshot_id=row["parent_snapshot_id"],
            branch_name=row["branch_name"],
            created_at=row["created_at"],
            state_vector=manifest,
            variable_count=row["variable_count"],
            description=meta.get("description", ""),
            blob_manifest=blob_manifest,
            metadata=meta,
        )
        return record, deserialized_vars

    def restore_snapshot(
        self, sandbox_or_id: Union[Any, str], snapshot_id: str
    ) -> Dict[str, Any]:
        """
        Restore sandbox namespace to state vector captured at snapshot_id.
        """
        if hasattr(sandbox_or_id, "sandbox_id"):
            sandbox_id = getattr(sandbox_or_id, "sandbox_id")
            sb = sandbox_or_id
        else:
            sandbox_id = str(sandbox_or_id)
            sb = None

        loaded = self.load_snapshot(sandbox_id, snapshot_id)
        if loaded is None:
            raise StorageNotFoundError(f"Snapshot '{snapshot_id}' not found for sandbox '{sandbox_id}'.")

        record, variables = loaded

        if sb is not None and hasattr(sb, "hydrate_state"):
            sb.hydrate_state(variables)

        # Update current branch in DB
        self.engine.execute_non_query(
            "UPDATE sandboxes SET current_branch_id = ?, updated_at = ? WHERE sandbox_id = ?",
            (snapshot_id, time.time(), sandbox_id),
        )

        return variables

    def list_snapshots(self, sandbox_id: str) -> List[PersistedSnapshotRecord]:
        """List all snapshots for a sandbox ordered by creation time."""
        rows = self.engine.execute_query(
            "SELECT * FROM snapshots WHERE sandbox_id = ? ORDER BY created_at ASC",
            (sandbox_id,),
        )
        snapshots: List[PersistedSnapshotRecord] = []
        for r in rows:
            blob_manifest = json.loads(r["blob_manifest_json"] or "{}")
            meta = json.loads(r["metadata_json"] or "{}")
            snapshots.append(
                PersistedSnapshotRecord(
                    snapshot_id=r["snapshot_id"],
                    sandbox_id=r["sandbox_id"],
                    name=r["name"],
                    parent_snapshot_id=r["parent_snapshot_id"],
                    branch_name=r["branch_name"],
                    created_at=r["created_at"],
                    variable_count=r["variable_count"],
                    description=meta.get("description", ""),
                    blob_manifest=blob_manifest,
                    metadata=meta,
                )
            )
        return snapshots

    def get_snapshot_tree(self, sandbox_id: str) -> Dict[str, Any]:
        """
        Return the full DAG tree of snapshot branches for a sandbox.
        """
        snapshots = self.list_snapshots(sandbox_id)
        nodes: Dict[str, Dict[str, Any]] = {}
        roots: List[str] = []
        branches: Dict[str, List[str]] = {}

        for s in snapshots:
            node = {
                "snapshot_id": s.snapshot_id,
                "name": s.name,
                "parent_snapshot_id": s.parent_snapshot_id,
                "branch_name": s.branch_name,
                "created_at": s.created_at,
                "variable_count": s.variable_count,
                "children": [],
            }
            nodes[s.snapshot_id] = node
            branches.setdefault(s.branch_name, []).append(s.snapshot_id)

            if not s.parent_snapshot_id:
                roots.append(s.snapshot_id)

        # Link children
        for s in snapshots:
            if s.parent_snapshot_id and s.parent_snapshot_id in nodes:
                nodes[s.parent_snapshot_id]["children"].append(s.snapshot_id)

        return {
            "sandbox_id": sandbox_id,
            "total_snapshots": len(snapshots),
            "roots": roots,
            "branches": branches,
            "nodes": nodes,
        }

    def delete_snapshot(self, snapshot_id: str) -> bool:
        """Delete a snapshot by ID."""
        with self.engine.transaction() as cur:
            cur.execute("DELETE FROM snapshots WHERE snapshot_id = ?", (snapshot_id,))
            return cur.rowcount > 0

    # -------------------------------------------------------------------------
    # Scheduled Worker Task Registry & Execution History Persistence
    # -------------------------------------------------------------------------

    def save_task(self, task: Any) -> None:
        """Persist or update a ScheduledTask in SQLite."""
        now = time.time()
        if hasattr(task, "task_id"):
            task_id = task.task_id
            name = task.name
            trigger_type = task.trigger_type.value if hasattr(task.trigger_type, "value") else str(task.trigger_type)
            trigger_spec = str(task.trigger_spec)
            code = task.code
            sandbox_id = getattr(task, "sandbox_id", None)
            status = task.status.value if hasattr(task.status, "value") else str(task.status)
            created_at = getattr(task, "created_at", now)
            next_run_at = getattr(task, "next_run_at", None)
            last_run_at = getattr(task, "last_run_at", None)
            run_count = getattr(task, "run_count", 0)
            max_runs = getattr(task, "max_runs", None)
            timeout = getattr(task, "timeout", 60.0)
            metadata = getattr(task, "metadata", {})
        elif isinstance(task, dict):
            task_id = task["task_id"]
            name = task.get("name", task_id)
            trigger_type = task.get("trigger_type", "cron")
            trigger_spec = str(task.get("trigger_spec", "* * * * *"))
            code = task.get("code", "")
            sandbox_id = task.get("sandbox_id")
            status = task.get("status", "scheduled")
            created_at = task.get("created_at", now)
            next_run_at = task.get("next_run_at")
            last_run_at = task.get("last_run_at")
            run_count = int(task.get("run_count", 0))
            max_runs = task.get("max_runs")
            timeout = float(task.get("timeout", 60.0))
            metadata = task.get("metadata", {})
        else:
            raise StorageError(f"Unsupported task type: {type(task)}")

        meta_json = json.dumps(metadata, ensure_ascii=False)

        with self.engine.transaction() as cur:
            cur.execute(
                """
                INSERT INTO scheduled_tasks (
                    task_id, name, trigger_type, trigger_spec, code, sandbox_id,
                    status, created_at, next_run_at, last_run_at, run_count, max_runs,
                    timeout, metadata_json, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(task_id) DO UPDATE SET
                    name = excluded.name,
                    trigger_type = excluded.trigger_type,
                    trigger_spec = excluded.trigger_spec,
                    code = excluded.code,
                    sandbox_id = excluded.sandbox_id,
                    status = excluded.status,
                    next_run_at = excluded.next_run_at,
                    last_run_at = excluded.last_run_at,
                    run_count = excluded.run_count,
                    max_runs = excluded.max_runs,
                    timeout = excluded.timeout,
                    metadata_json = excluded.metadata_json,
                    updated_at = excluded.updated_at
                """,
                (
                    task_id,
                    name,
                    trigger_type,
                    trigger_spec,
                    code,
                    sandbox_id,
                    status,
                    created_at,
                    next_run_at,
                    last_run_at,
                    run_count,
                    max_runs,
                    timeout,
                    meta_json,
                    now,
                ),
            )

    def get_task(self, task_id: str) -> Optional[Any]:
        """Load a ScheduledTask from SQLite by ID."""
        row = self.engine.execute_single(
            "SELECT * FROM scheduled_tasks WHERE task_id = ?", (task_id,)
        )
        if row is None:
            return None
        return self._row_to_task(row)

    def list_tasks(self, status: Optional[str] = None) -> List[Any]:
        """List scheduled tasks, optionally filtered by status."""
        if status is not None:
            status_str = status.value if hasattr(status, "value") else str(status)
            rows = self.engine.execute_query(
                "SELECT * FROM scheduled_tasks WHERE status = ? ORDER BY created_at ASC",
                (status_str,),
            )
        else:
            rows = self.engine.execute_query(
                "SELECT * FROM scheduled_tasks ORDER BY created_at ASC"
            )
        return [self._row_to_task(r) for r in rows]

    def load_tasks(self) -> List[Any]:
        """Alias to list_tasks for loading all persisted tasks."""
        return self.list_tasks()

    def delete_task(self, task_id: str) -> bool:
        """Delete task and its execution records from SQLite."""
        with self.engine.transaction() as cur:
            cur.execute("DELETE FROM scheduled_tasks WHERE task_id = ?", (task_id,))
            return cur.rowcount > 0

    def record_task_execution(
        self,
        task_id: str,
        record: Union[Any, Dict[str, Any]],
    ) -> None:
        """
        Record a task execution record and atomically update task stats (run_count, last_run_at).
        """
        now = time.time()
        if hasattr(record, "execution_id"):
            execution_id = record.execution_id or f"exec_{uuid.uuid4().hex[:12]}"
            started_at = getattr(record, "started_at", now)
            finished_at = getattr(record, "finished_at", now)
            duration_ms = getattr(record, "duration_ms", 0.0)
            exit_code = getattr(record, "exit_code", 0)
            stdout = getattr(record, "stdout", "")
            stderr = getattr(record, "stderr", "")
            result_repr = getattr(record, "result_repr", None) or getattr(record, "result", None)
            error = getattr(record, "error", None)
            artifacts = getattr(record, "artifacts", [])
            state = getattr(record, "state", {})
            backend_used = getattr(record, "backend_used", getattr(record, "sandbox_backend", "local"))
        elif isinstance(record, dict):
            execution_id = record.get("execution_id") or f"exec_{uuid.uuid4().hex[:12]}"
            started_at = record.get("started_at", now)
            finished_at = record.get("finished_at", now)
            duration_ms = record.get("duration_ms", 0.0)
            exit_code = record.get("exit_code", 0)
            stdout = record.get("stdout", "")
            stderr = record.get("stderr", "")
            result_repr = record.get("result_repr") or record.get("result")
            error = record.get("error")
            artifacts = record.get("artifacts", [])
            state = record.get("state", {})
            backend_used = record.get("backend_used", record.get("sandbox_backend", "local"))
        else:
            execution_id = f"exec_{uuid.uuid4().hex[:12]}"
            started_at = now
            finished_at = now
            duration_ms = getattr(record, "duration_ms", 0.0)
            exit_code = getattr(record, "exit_code", 0)
            stdout = getattr(record, "stdout", "")
            stderr = getattr(record, "stderr", "")
            result_repr = repr(record)
            error = getattr(record, "error", None)
            artifacts = []
            state = {}
            backend_used = "local"

        artifacts_json = json.dumps(artifacts, ensure_ascii=False)
        state_json = json.dumps(state, ensure_ascii=False)

        with self.engine.transaction() as cur:
            # 1. Insert execution record
            cur.execute(
                """
                INSERT INTO task_execution_records (
                    execution_id, task_id, started_at, finished_at, duration_ms,
                    exit_code, stdout, stderr, result_repr, error, artifacts_json,
                    state_json, sandbox_backend, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    execution_id,
                    task_id,
                    started_at,
                    finished_at,
                    duration_ms,
                    exit_code,
                    stdout,
                    stderr,
                    result_repr,
                    error,
                    artifacts_json,
                    state_json,
                    backend_used,
                    now,
                ),
            )

            # 2. Update task last_run_at and increment run_count
            cur.execute(
                """
                UPDATE scheduled_tasks
                SET last_run_at = ?, run_count = run_count + 1, updated_at = ?
                WHERE task_id = ?
                """,
                (started_at, now, task_id),
            )

    def get_task_history(self, task_id: str, limit: Optional[int] = 50) -> List[Any]:
        """
        Retrieve execution history records for a task ordered chronologically.
        """
        if limit is not None and limit > 0:
            rows = self.engine.execute_query(
                """
                SELECT * FROM task_execution_records
                WHERE task_id = ?
                ORDER BY started_at DESC
                LIMIT ?
                """,
                (task_id, limit),
            )
            # Re-sort in ascending chronological order
            rows = list(reversed(rows))
        else:
            rows = self.engine.execute_query(
                """
                SELECT * FROM task_execution_records
                WHERE task_id = ?
                ORDER BY started_at ASC
                """,
                (task_id,),
            )

        from antigravity.scheduler.models import TaskExecutionRecord

        records = []
        for r in rows:
            art = json.loads(r["artifacts_json"] or "[]")
            st = json.loads(r["state_json"] or "{}")
            records.append(
                TaskExecutionRecord(
                    execution_id=r["execution_id"],
                    task_id=r["task_id"],
                    started_at=r["started_at"],
                    finished_at=r["finished_at"],
                    duration_ms=r["duration_ms"],
                    exit_code=r["exit_code"],
                    stdout=r["stdout"] or "",
                    stderr=r["stderr"] or "",
                    result=r["result_repr"],
                    error=r["error"],
                    artifacts=art,
                    state=st,
                    sandbox_backend=r["sandbox_backend"],
                    backend_used=r["sandbox_backend"],
                )
            )
        return records

    def _row_to_task(self, row: Any) -> Any:
        """Construct ScheduledTask model from SQLite row."""
        from antigravity.scheduler.models import ScheduledTask, TaskStatus, TaskTriggerType

        meta = json.loads(row["metadata_json"] or "{}")
        try:
            status = TaskStatus(row["status"])
        except ValueError:
            status = TaskStatus.SCHEDULED

        try:
            trigger_type = TaskTriggerType(row["trigger_type"])
        except ValueError:
            trigger_type = TaskTriggerType.CRON

        return ScheduledTask(
            task_id=row["task_id"],
            name=row["name"],
            trigger_type=trigger_type,
            trigger_spec=row["trigger_spec"],
            code=row["code"],
            sandbox_id=row["sandbox_id"],
            status=status,
            created_at=row["created_at"],
            next_run_at=row["next_run_at"],
            last_run_at=row["last_run_at"],
            run_count=row["run_count"],
            max_runs=row["max_runs"],
            timeout=row["timeout"],
            metadata=meta,
        )

    # -------------------------------------------------------------------------
    # Model Configurations Persistence
    # -------------------------------------------------------------------------

    def save_model_config(self, config: Union[PersistedModelConfig, Dict[str, Any]]) -> None:
        """Persist or update local model configuration metadata."""
        now = time.time()
        if isinstance(config, PersistedModelConfig):
            model_id = config.model_id
            name = config.name
            architecture = config.architecture
            model_path = config.model_path
            tokenizer_path = config.tokenizer_path
            device = config.device
            dtype = config.dtype
            quantization = config.quantization
            context_window = config.context_window
            gen_params = config.generation_params
            meta = config.metadata
            created_at = config.created_at or now
        elif isinstance(config, dict):
            model_id = config["model_id"]
            name = config.get("name", model_id)
            architecture = config.get("architecture", "nemotron")
            model_path = config.get("model_path", "")
            tokenizer_path = config.get("tokenizer_path")
            device = config.get("device", "cpu")
            dtype = config.get("dtype", "float32")
            quantization = config.get("quantization")
            context_window = int(config.get("context_window", 4096))
            gen_params = config.get("generation_params", {})
            meta = config.get("metadata", {})
            created_at = float(config.get("created_at", now))
        else:
            raise StorageError(f"Unsupported config type: {type(config)}")

        gen_json = json.dumps(gen_params, ensure_ascii=False)
        meta_json = json.dumps(meta, ensure_ascii=False)

        with self.engine.transaction() as cur:
            cur.execute(
                """
                INSERT OR REPLACE INTO model_configurations (
                    model_id, name, architecture, model_path, tokenizer_path,
                    device, dtype, quantization, context_window, generation_params_json,
                    metadata_json, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    model_id,
                    name,
                    architecture,
                    model_path,
                    tokenizer_path,
                    device,
                    dtype,
                    quantization,
                    context_window,
                    gen_json,
                    meta_json,
                    created_at,
                    now,
                ),
            )

    def get_model_config(self, model_id: str) -> Optional[PersistedModelConfig]:
        """Retrieve a model configuration by ID."""
        row = self.engine.execute_single(
            "SELECT * FROM model_configurations WHERE model_id = ?", (model_id,)
        )
        if row is None:
            return None
        return self._row_to_model_config(row)

    def list_model_configs(self, architecture: Optional[str] = None) -> List[PersistedModelConfig]:
        """List all model configurations, optionally filtered by architecture."""
        if architecture is not None:
            rows = self.engine.execute_query(
                "SELECT * FROM model_configurations WHERE architecture = ? ORDER BY name ASC",
                (architecture,),
            )
        else:
            rows = self.engine.execute_query(
                "SELECT * FROM model_configurations ORDER BY name ASC"
            )
        return [self._row_to_model_config(r) for r in rows]

    def delete_model_config(self, model_id: str) -> bool:
        """Delete a model configuration by ID."""
        with self.engine.transaction() as cur:
            cur.execute("DELETE FROM model_configurations WHERE model_id = ?", (model_id,))
            return cur.rowcount > 0

    def _row_to_model_config(self, row: Any) -> PersistedModelConfig:
        """Construct PersistedModelConfig from SQLite row."""
        gen_params = json.loads(row["generation_params_json"] or "{}")
        meta = json.loads(row["metadata_json"] or "{}")
        return PersistedModelConfig(
            model_id=row["model_id"],
            name=row["name"],
            architecture=row["architecture"],
            model_path=row["model_path"],
            tokenizer_path=row["tokenizer_path"],
            device=row["device"],
            dtype=row["dtype"],
            quantization=row["quantization"],
            context_window=row["context_window"],
            generation_params=gen_params,
            metadata=meta,
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def close(self) -> None:
        """Close SQLite engine and release open database connections."""
        self.engine.close()

    def __enter__(self) -> "PersistenceManager":
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()
