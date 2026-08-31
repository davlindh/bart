# Architectural Specification & Technical Survey: R1 Disk-Backed Local Persistence Store

**Module Target**: `src/antigravity/storage/`  
**Author**: Explorer 1 (Survey Agent)  
**Date**: 2026-08-29  
**Status**: Ready for Implementation  

---

## 1. Executive Summary & Problem Formulation

The Antigravity platform currently provisions and manages isolated REPL sandboxes (`LocalSandbox`, `E2BSandbox`) and scheduled background tasks (`ServiceWorkerDaemon`, `TaskRegistry`). However, all runtime state—including REPL session namespaces, multi-branch snapshot state vectors, variable tables, scheduled worker task registries, and execution histories—is currently held strictly in-memory or in ephemeral subprocess memory.

When a Python process terminates, restarts, or crashes:
1. **Sandbox Sessions & Namespaces are Lost**: An agent's multi-turn computation, loaded datasets, functions, and REPL variables vanish.
2. **Snapshots Disappear**: Checkpoints created via `manage_snapshot` or `sandbox.create_snapshot()` exist only within the ephemeral subprocess lifetime.
3. **Scheduled Tasks & History are Reset**: The `ServiceWorkerDaemon` loses all registered cron/timer jobs, execution records, run counts, and telemetry.
4. **Model Metadata is Ephemeral**: Local model inference configurations (architectures, weight paths, quantization, device mappings) must be re-specified on every startup.

**Requirement R1 Objective**:
Design and specify a production-grade, disk-backed local persistence engine (`PersistenceManager`, `DiskStateStore`, `SQLiteEngine`, `VariableSerializer`) that persists and restores all sandbox sessions, multi-branch snapshot DAGs, variable tables, scheduled worker task histories, and model configurations across restarts and process boundaries.

---

## 2. Codebase Investigation & Current Limitations

### 2.1 MicroVM & Local Sandbox Subsystem (`src/antigravity/sandbox/`)
- **`src/antigravity/sandbox/models.py`**: Defines `SandboxState`, `SandboxMode`, `SandboxConfig`, `ExecutionResult`, and exception hierarchy (`SandboxError`, `SecurityViolationError`, `SandboxTimeoutError`, `SandboxExecutionError`, `SnapshotError`).
- **`src/antigravity/sandbox/base.py`**: `BaseSandbox` defines lifecycle and snapshot methods (`start`, `execute`, `pause`, `resume`, `create_snapshot`, `restore_snapshot`, `list_snapshots`, `delete_snapshot`, `terminate`, `reset_session`, `get_variables`).
- **`src/antigravity/sandbox/local_sandbox.py`**: Spawns `local_repl_worker.py` subprocess via stdio JSON-RPC. Maintains an in-memory dictionary `self._snapshots: Dict[str, Dict[str, Any]]`.
- **`src/antigravity/sandbox/local_repl_worker.py`**: Holds `self.session_globals: Dict[str, Any]` and `self.snapshots: Dict[str, Dict[str, Any]]`. Snapshot creation performs `copy.deepcopy()` in-memory.
- **`src/antigravity/sandbox/manager.py`**: Tracks active sandboxes in `self._sandboxes: Dict[str, BaseSandbox]`. No disk catalog exists; upon process reboot, `list_sandboxes()` returns empty.

### 2.2 Scheduled Service Worker Subsystem (`src/antigravity/scheduler/`)
- **`src/antigravity/scheduler/models.py`**: Defines `ScheduledTask`, `TaskExecutionRecord`, `TaskStatus`, `TaskTriggerType`.
- **`src/antigravity/scheduler/registry.py`**: `TaskRegistry` stores tasks in `self._tasks: Dict[str, ScheduledTask]` and history in `self._history: Dict[str, Deque[TaskExecutionRecord]]`.
- **`src/antigravity/scheduler/daemon.py`**: `ServiceWorkerDaemon` runs background loop inspecting due tasks. When stopped, all memory is wiped.
- **`src/antigravity/scheduler/monitor.py`**: Exposes telemetry calculated dynamically from in-memory registry.

### 2.3 Key Architectural Gaps Identified
1. **No State Serialization Protocol**: No IPC action exists between `LocalSandbox` and `local_repl_worker.py` to dump or inject full session state vectors.
2. **No Persistent Relational Store**: No SQLite database exists to store metadata, tasks, execution records, model configs, and snapshot lineages.
3. **No Content-Addressed Blob Storage**: No filesystem store exists for storing large variable binaries, tensors, pickled complex objects, and execution artifacts.
4. **No Process Re-hydration Mechanism**: `LocalSandbox` cannot currently be instantiated by referencing a stored disk session ID and having its environment restored without executing code from scratch.

---

## 3. R1 Architecture Specification

### 3.1 Subsystem Architecture & Layered Design

```
+----------------------------------------------------------------------------------------------------+
|                                      Antigravity Subsystems                                        |
|         [ SandboxManager ]        [ LocalSandbox ]        [ ServiceWorkerDaemon / TaskRegistry ]   |
+----------------------------------------------------------------------------------------------------+
                                                  │
                                                  ▼
+----------------------------------------------------------------------------------------------------+
|                         PersistenceManager  (src/antigravity/storage/manager.py)                   |
|  - High-level lifecycle & orchestration API                                                        |
|  - Sandbox export / hydrate / restore across process boundaries                                    |
|  - Multi-branch snapshot DAG management (branching, merging, restoring)                           |
|  - Scheduled worker task registry sync & history logging                                           |
|  - Model configurations registry                                                                   |
+------------------------------------+---------------------------------------------------------------+
                                     │
                  ┌──────────────────┴──────────────────┐
                  ▼                                     ▼
+------------------------------------+   +-----------------------------------------------------------+
|    VariableSerializer & Codec      |   |        DiskStateStore (disk_store.py)                     |
|  (src/antigravity/storage/...)     |   |  - Filesystem blob & artifact storage                     |
|  - JSON Codec (primitives)         |   |  - Content-addressed SHA-256 deduplication               |
|  - Pickle Codec (safe whitelist)   |   |  - Atomic file writes (temp + os.replace)                 |
|  - NumPy/Safetensors Codec         |   |  - Directory tree management                              |
|  - StateVectorCodec (manifests)    |   +-----------------------------------------------------------+
+------------------------------------+                                  │
                  │                                                     ▼
                  ▼                                        [ <storage_root>/blobs/ ]
+----------------------------------------------------+     [ <storage_root>/models/ ]
|          SQLiteEngine (engine.py & schema.sql)     |     [ <storage_root>/artifacts/ ]
|  - WAL mode, foreign keys, 10s busy timeout        |
|  - Schema migrations & connection context manager  |
|  - Thread-safe connection pool                     |
+----------------------------------------------------+
                          │
                          ▼
             [ <storage_root>/state.db ]
```

---

### 3.2 Concrete SQLite Database Schema (`schema.sql`)

```sql
-- Schema Version: 1.0.0
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA foreign_keys = ON;
PRAGMA busy_timeout = 10000;

-- 1. Metadata and Version Tracking
CREATE TABLE IF NOT EXISTS schema_meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at REAL NOT NULL
);

-- 2. Sandboxes Session Registry
CREATE TABLE IF NOT EXISTS sandboxes (
    sandbox_id TEXT PRIMARY KEY,
    mode TEXT NOT NULL DEFAULT 'local',       -- 'local', 'e2b', 'auto'
    status TEXT NOT NULL DEFAULT 'running',   -- 'running', 'paused', 'terminated', 'error'
    config_json TEXT NOT NULL,                -- SandboxConfig serialized (timeout, env, imports)
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
    codec TEXT NOT NULL,                      -- 'json', 'pickle', 'safetensors', 'npy', 'bytes', 'str'
    inline_data TEXT,                         -- JSON string for small primitives (<= 4KB)
    blob_hash TEXT,                           -- SHA-256 hash in DiskStateStore if external
    size_bytes INTEGER NOT NULL DEFAULT 0,
    is_restorable INTEGER NOT NULL DEFAULT 1, -- 1=True, 0=False
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
    state_vector_json TEXT NOT NULL,          -- JSON manifest of all variables in snapshot
    blob_manifest_json TEXT NOT NULL,         -- Map of var_name -> blob_hash
    variable_count INTEGER NOT NULL DEFAULT 0,
    metadata_json TEXT DEFAULT '{}',
    FOREIGN KEY (sandbox_id) REFERENCES sandboxes(sandbox_id) ON DELETE CASCADE,
    FOREIGN KEY (parent_snapshot_id) REFERENCES snapshots(snapshot_id) ON DELETE SET NULL
);

-- 5. Scheduled Worker Tasks
CREATE TABLE IF NOT EXISTS scheduled_tasks (
    task_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    trigger_type TEXT NOT NULL,               -- 'cron', 'timer'
    trigger_spec TEXT NOT NULL,               -- Cron expression or interval in seconds
    code TEXT NOT NULL,                       -- Python source payload
    sandbox_id TEXT,
    status TEXT NOT NULL DEFAULT 'scheduled', -- 'scheduled', 'running', 'completed', 'failed', 'cancelled', 'paused'
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
    architecture TEXT NOT NULL,               -- 'nemotron', 'nemo', 'transformer', 'gguf', 'onnx'
    model_path TEXT NOT NULL,
    tokenizer_path TEXT,
    device TEXT NOT NULL DEFAULT 'cpu',       -- 'cpu', 'cuda', 'cuda:0', 'mps'
    dtype TEXT NOT NULL DEFAULT 'float32',    -- 'float32', 'float16', 'bfloat16', 'int8', 'int4'
    quantization TEXT,                        -- '4bit', '8bit', 'awq', 'gptq', None
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
```

---

### 3.3 Multi-Tiered Variable Serialization & State Vector Strategy

A sandbox session contains heterogeneous Python objects. The `VariableSerializer` employs a 4-tier codec hierarchy:

| Tier | Codec | Target Types | Storage Format | Fallback / Safety |
|---|---|---|---|---|
| **1** | `json` | `int`, `float`, `str`, `bool`, `list`, `dict`, `None` | Inline JSON in SQLite (if ≤ 4KB) or `.json` file in `blobs/vars/` | Standard JSON serialization |
| **2** | `safetensors` / `npy` | `numpy.ndarray`, `torch.Tensor` | `.safetensors` or `.npy` binary blob | Memory-mapped zero-copy load; preserves dtype & shape |
| **3** | `pickle` | Custom classes, dataclasses, complex standard types | Protocol 5 `.pkl` blob in `blobs/vars/` | Whitelisted safe `RestrictedUnpickler` preventing arbitrary code execution |
| **4** | `unrestorable` | File descriptors, sockets, thread locks, active generators | Store `repr(val)` and `type_name`, mark `is_restorable=0` | Emits warning log, avoids crashing session restore |

#### Restricted Safe Deserialization (Pickle Safety)
To prevent deserialization vulnerabilities when restoring sessions, `VariableSerializer` utilizes a subclassed `pickle.Unpickler` that permits only standard builtins, collections, numpy/torch primitives, and standard library data structures, while strictly blocking dangerous system invocation objects (`subprocess.Popen`, `os.system`, etc.).

#### State Vector Manifest Schema
When a snapshot or session is persisted, variables are cataloged in a `StateVectorManifest`:
```python
@dataclass
class VariableDescriptor:
    name: str
    type_name: str
    codec: str                        # 'json' | 'safetensors' | 'npy' | 'pickle' | 'unrestorable'
    inline_data: Optional[str] = None # JSON string if stored directly in DB
    blob_hash: Optional[str] = None   # SHA-256 hash if stored in blob store
    size_bytes: int = 0
    repr_str: str = ""
    is_restorable: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
```

---

### 3.4 Multi-Branch Snapshot State Vector DAG

Snapshots in Antigravity are not purely linear; autonomous agents can fork hypotheses into multiple branches.

```
                  [ Snapshot 0 (root) ]
                            │
            ┌───────────────┴───────────────┐
            ▼                               ▼
    [ Snapshot 1: branch="main" ]   [ Snapshot 2: branch="experiment-A" ]
            │                               │
            ▼                               ▼
    [ Snapshot 3: branch="main" ]   [ Snapshot 4: branch="experiment-A" ]
```

1. **Branch Tracking**: Each snapshot records `snapshot_id`, `parent_snapshot_id`, and `branch_name`.
2. **Snapshot Creation**:
   - Captures active `session_globals` from REPL worker.
   - Serializes variables to `DiskStateStore` (deduplicating identical blobs via SHA-256).
   - Writes record into `snapshots` table with `parent_snapshot_id = sandbox.current_snapshot_id`.
   - Updates sandbox `current_branch_id = snapshot_id`.
3. **Snapshot Restoration**:
   - Looks up `snapshot_id` in `snapshots` table.
   - Retrieves `blob_manifest_json` and `state_vector_json`.
   - Loads and deserializes variable descriptors.
   - Hydrates target `LocalSandbox` REPL namespace with variables.
   - Updates sandbox `current_branch_id = snapshot_id`.
4. **Branch Exploration API**:
   - `get_snapshot_tree(sandbox_id)`: Returns full tree/DAG of snapshots.
   - `create_branch(sandbox_id, branch_name, from_snapshot_id)`: Explicitly forks from an existing checkpoint.

---

### 3.5 Scheduled Service Worker Daemon Persistence & Crash Recovery

When `ServiceWorkerDaemon` is paired with `PersistentTaskRegistry`:
1. **Write-Through Persistence**:
   - `register_task(task)`: Inserts/updates `scheduled_tasks` in SQLite.
   - `cancel_task(task_id)`: Sets `status = 'cancelled'` in SQLite.
   - `record_execution(task_id, record)`: Inserts into `task_execution_records` and updates `last_run_at`, `run_count` in `scheduled_tasks` within a single atomic transaction.
2. **Crash & Restart Recovery Flow**:
   - On daemon startup, `PersistentTaskRegistry.load_from_db()` executes:
     * Queries all tasks from `scheduled_tasks` where `status IN ('scheduled', 'running', 'paused')`.
     * If a task was marked `'running'` during an abrupt process termination, detects orphaned state, logs a failure execution record (`"Daemon crashed while task was running"`), and resets status to `'scheduled'` (or `'failed'` if `max_runs` exceeded).
     * Recomputes accurate `next_run_at` from `time.time()` using `CronTrigger` or `TimerTrigger`.
     * Pre-populates history deques with the last `N` execution records from `task_execution_records`.
3. **Zero Lost Tasks**: Even after `kill -9` or system restart, 100% of tasks, run counts, and audit logs are preserved.

---

### 3.6 Directory Layout & Storage Hierarchy

Default root: `~/.antigravity/storage/` (or customizable via `StorageConfig(base_dir=...)`):

```
<storage_root>/
├── state.db                     # Primary SQLite database (WAL mode)
├── state.db-wal                 # Write-Ahead Log
├── state.db-shm                 # Shared memory file
├── blobs/                       # Content-addressed variable data
│   └── vars/
│       ├── a1b2c3d4...json      # Large JSON payload
│       ├── e5f6g7h8...safetensors # Tensor weights / state vector
│       ├── 9a8b7c6d...npy       # Large NumPy array
│       └── 12345678...pkl       # Serialized Python object
├── artifacts/                   # Execution artifacts (images, CSVs, logs)
│   └── <execution_id>/
│       ├── figure.png
│       └── output.csv
├── models/                      # Local model weights, tokenizers, metadata
│   └── <model_id>/
│       ├── config.json
│       └── model.safetensors
└── locks/                       # Cross-process mutex & coordination locks
    └── persistence.lock
```

---

### 3.7 Atomic File Operations & Concurrency Control

1. **Atomic File Writes**:
   - Writing blobs follows strict two-phase atomic write:
     ```python
     tmp_file = target_path.with_suffix(f".tmp.{uuid.uuid4().hex[:8]}")
     with open(tmp_file, "wb") as f:
         f.write(data)
         f.flush()
         os.fsync(f.fileno())
     os.replace(tmp_file, target_path)  # Atomic on POSIX and Windows (Python 3.3+)
     ```
2. **SQLite Multi-Process Concurrency**:
   - Enabled `WAL` journal mode allowing simultaneous readers and single writer.
   - Configured `busy_timeout = 10000` (10s) ensuring process waits for busy locks rather than throwing immediate `sqlite3.OperationalError: database is locked`.
   - Explicit transactions (`BEGIN IMMEDIATE`) for critical compound operations (e.g. task run count increments + execution logging).

---

## 4. Concrete Interface Contracts & Class Definitions

### 4.1 Storage Models (`src/antigravity/storage/models.py`)

```python
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

class CodecType(str, Enum):
    JSON = "json"
    SAFETENSORS = "safetensors"
    NUMPY = "npy"
    PICKLE = "pickle"
    BYTES = "bytes"
    STR = "str"
    UNRESTORABLE = "unrestorable"

@dataclass
class StorageConfig:
    base_dir: str = "~/.antigravity/storage"
    db_name: str = "state.db"
    max_inline_bytes: int = 4096  # Store inline in SQLite if <= 4KB
    wal_mode: bool = True
    busy_timeout_ms: int = 10000
    auto_vacuum: bool = True

@dataclass
class VariableDescriptor:
    name: str
    type_name: str
    codec: CodecType
    inline_data: Optional[str] = None
    blob_hash: Optional[str] = None
    size_bytes: int = 0
    repr_str: str = ""
    is_restorable: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class StateVectorManifest:
    sandbox_id: str
    timestamp: float
    variables: Dict[str, VariableDescriptor] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class PersistedSandboxRecord:
    sandbox_id: str
    mode: str
    status: str
    config_json: str
    work_dir: Optional[str]
    created_at: float
    updated_at: float
    last_active_at: float
    current_branch_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class PersistedSnapshotRecord:
    snapshot_id: str
    sandbox_id: str
    name: str
    parent_snapshot_id: Optional[str]
    branch_name: str
    created_at: float
    state_vector: StateVectorManifest
    variable_count: int
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class PersistedModelConfig:
    model_id: str
    name: str
    architecture: str
    model_path: str
    tokenizer_path: Optional[str] = None
    device: str = "cpu"
    dtype: str = "float32"
    quantization: Optional[str] = None
    context_window: int = 4096
    generation_params: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = 0.0
    updated_at: float = 0.0
```

---

### 4.2 DiskStateStore (`src/antigravity/storage/disk_store.py`)

```python
class DiskStateStore:
    def __init__(self, config: StorageConfig) -> None: ...
    def write_blob(self, data: bytes, ext: str = "bin", mime_type: str = "application/octet-stream") -> str:
        """Writes binary data atomically, returns SHA-256 blob hash."""
    def read_blob(self, blob_hash: str) -> bytes:
        """Reads binary blob by hash. Raises KeyError if missing."""
    def has_blob(self, blob_hash: str) -> bool: ...
    def delete_blob(self, blob_hash: str) -> bool: ...
    def save_artifact(self, execution_id: str, name: str, data: bytes) -> str:
        """Saves execution artifact, returns relative file path."""
    def get_artifact_path(self, execution_id: str, name: str) -> Optional[Path]: ...
    def purge_orphaned_blobs(self, active_hashes: Set[str]) -> int: ...
```

---

### 4.3 SQLiteEngine (`src/antigravity/storage/engine.py`)

```python
class SQLiteEngine:
    def __init__(self, config: StorageConfig) -> None: ...
    def initialize_schema(self) -> None: ...
    @contextmanager
    def connection(self) -> Generator[sqlite3.Connection, None, None]: ...
    @contextmanager
    def transaction(self) -> Generator[sqlite3.Cursor, None, None]: ...
    def execute_query(self, sql: str, params: tuple = ()) -> List[sqlite3.Row]: ...
    def execute_single(self, sql: str, params: tuple = ()) -> Optional[sqlite3.Row]: ...
    def close(self) -> None: ...
```

---

### 4.4 VariableSerializer (`src/antigravity/storage/serializer.py`)

```python
class VariableSerializer:
    def __init__(self, disk_store: DiskStateStore, max_inline_bytes: int = 4096) -> None: ...
    def serialize_variable(self, name: str, value: Any) -> VariableDescriptor:
        """Encodes Python object into VariableDescriptor + blob if needed."""
    def deserialize_variable(self, descriptor: VariableDescriptor) -> Any:
        """Decodes VariableDescriptor back into active Python object."""
    def serialize_namespace(self, namespace: Dict[str, Any]) -> StateVectorManifest:
        """Encodes full dictionary of globals into StateVectorManifest."""
    def deserialize_namespace(self, manifest: StateVectorManifest) -> Dict[str, Any]:
        """Decodes StateVectorManifest into dictionary of globals."""
```

---

### 4.5 PersistenceManager (`src/antigravity/storage/manager.py`)

```python
class PersistenceManager:
    """Unified Persistence Orchestrator."""
    def __init__(self, config: Optional[StorageConfig] = None) -> None: ...
    
    # --- Sandbox Persistence & Process Boundary Restoration ---
    def save_sandbox(self, sandbox: BaseSandbox, branch_name: str = "main") -> PersistedSandboxRecord:
        """Exports sandbox variables, saves state to disk, updates SQLite."""
    def restore_sandbox(self, sandbox_id: str, auto_start: bool = True) -> BaseSandbox:
        """Loads sandbox metadata from disk and spins up a fully hydrated LocalSandbox in current process."""
    def list_persisted_sandboxes(self) -> List[Dict[str, Any]]: ...
    def delete_persisted_sandbox(self, sandbox_id: str) -> bool: ...

    # --- Multi-Branch Snapshots ---
    def save_snapshot(self, sandbox_id: str, name: str, branch_name: str = "main", parent_id: Optional[str] = None) -> str:
        """Takes a persistent snapshot of sandbox state vector."""
    def restore_snapshot(self, sandbox: BaseSandbox, snapshot_id: str) -> None:
        """Restores sandbox in-memory variables to the snapshot state vector."""
    def list_snapshots(self, sandbox_id: str) -> List[Dict[str, Any]]: ...
    def get_snapshot_tree(self, sandbox_id: str) -> Dict[str, Any]:
        """Returns the full DAG tree of snapshot branches."""

    # --- Scheduler Task Registry Persistence ---
    def save_task(self, task: ScheduledTask) -> None: ...
    def get_task(self, task_id: str) -> Optional[ScheduledTask]: ...
    def list_tasks(self, status: Optional[str] = None) -> List[ScheduledTask]: ...
    def delete_task(self, task_id: str) -> bool: ...
    def record_task_execution(self, task_id: str, record: TaskExecutionRecord) -> None: ...
    def get_task_history(self, task_id: str, limit: Optional[int] = None) -> List[TaskExecutionRecord]: ...

    # --- Model Configurations ---
    def save_model_config(self, config: PersistedModelConfig) -> None: ...
    def get_model_config(self, model_id: str) -> Optional[PersistedModelConfig]: ...
    def list_model_configs(self) -> List[PersistedModelConfig]: ...
    def delete_model_config(self, model_id: str) -> bool: ...
```

---

## 5. Integration Blueprint with Existing Modules

### 5.1 Updates to `LocalSandbox` and `LocalREPLWorker`
1. **Add `export_state` command to `local_repl_worker.py`**:
   - Iterates `self.session_globals` excluding internal builtins.
   - Returns `{var_name: {"type": ..., "codec": ..., "payload": ...}}` or pickled stream.
2. **Add `hydrate_state` command to `local_repl_worker.py`**:
   - Takes decoded variable dictionary and safely updates `self.session_globals`.
3. **Add `export_state()` and `hydrate_state(state)` methods to `LocalSandbox`**:
   - Dispatches `export_state` and `hydrate_state` JSON-RPC commands to child process.

### 5.2 Updates to `TaskRegistry` and `ServiceWorkerDaemon`
1. **Persistent Backing for `TaskRegistry`**:
   - `TaskRegistry` accepts optional `persistence_manager: Optional[PersistenceManager] = None`.
   - If provided, `register()`, `cancel()`, `update_status()`, and `record_execution()` write through to `PersistenceManager`.
   - On initialization, `TaskRegistry.hydrate_from_persistence()` loads active tasks and history records from SQLite.

### 5.3 Updates to `SandboxManager`
- `SandboxManager` integrates with `PersistenceManager` to auto-record created sandboxes and enable `manager.restore_persisted_sandbox(sandbox_id)`.

### 5.4 Integration with MCP Tools (Requirement R4)
- New MCP tools:
  - `persist_sandbox`: Calls `persistence_manager.save_sandbox(sandbox_id)`.
  - `restore_sandbox_disk`: Calls `persistence_manager.restore_sandbox(sandbox_id)`.
  - `list_persisted_sandboxes`: Calls `persistence_manager.list_persisted_sandboxes()`.

---

## 6. Verification & Validation Plan

### 6.1 Unit Test Coverage (`tests/tier1_features/test_storage_features.py`)
1. **SQLite Engine & Schema**: Table creation, WAL mode verification, index validation, CRUD operations.
2. **DiskStateStore**: Atomic file write verification, SHA-256 content-addressing, binary read/write, duplicate blob deduplication.
3. **VariableSerializer**:
   - Primitive round-trip (int, float, str, dict, list).
   - Large objects & byte buffers.
   - NumPy array round-trip (if numpy available or via raw buffer).
   - Restricted unpickler safety checks (rejection of malicious bytecode payloads).
   - Graceful handling of unrestorable objects (file handles, locks).

### 6.2 Process Boundary Integration Test (`tests/tier3_cross_feature/test_persistence_process_boundary.py`)
1. **Process 1**:
   - Instantiate `LocalSandbox(sandbox_id="sb-persist-test")`.
   - Execute Python code: `x = 42; y = [1, 2, 3]; msg = 'hello persistent world'`.
   - Create snapshot `"checkpoint_1"`.
   - Call `PersistenceManager.save_sandbox(sb)`.
   - Terminate `LocalSandbox` and close all connections.
2. **Process 2 (Simulated Clean Process)**:
   - Create brand new `PersistenceManager` pointing to the same storage directory.
   - Call `sb_restored = PersistenceManager.restore_sandbox("sb-persist-test")`.
   - Execute: `res = sb_restored.execute("print(f'{msg}: {x + sum(y)}')")`.
   - Assert: `res.stdout.strip() == "hello persistent world: 48"`.
   - Assert: Snapshot `"checkpoint_1"` is listable and restorable.

### 6.3 Daemon Crash Recovery Test (`tests/tier3_cross_feature/test_scheduler_crash_recovery.py`)
1. Register cron and timer tasks in `ServiceWorkerDaemon` backed by `PersistenceManager`.
2. Run task to trigger 2 execution records.
3. Abruptly stop daemon (simulate process crash).
4. Spin up fresh `ServiceWorkerDaemon` with new `TaskRegistry` pointing to same DB.
5. Assert: All tasks restored, run count is 2, previous execution records intact, `next_run_at` correctly calculated.

---

## 7. Implementation Roadmap for Builder Agents

1. **Step 1: Module Scaffolding & Base Models**
   - Create directory `src/antigravity/storage/`.
   - Implement `src/antigravity/storage/models.py` (enums, dataclasses, `StorageConfig`).
   - Implement `src/antigravity/storage/exceptions.py`.

2. **Step 2: SQLite Engine & Schema**
   - Implement `src/antigravity/storage/schema.sql` (full SQL schema with indexes).
   - Implement `src/antigravity/storage/engine.py` (`SQLiteEngine`, connection management, transactions, migrations).

3. **Step 3: DiskStateStore & Serialization**
   - Implement `src/antigravity/storage/disk_store.py` (atomic blob writer/reader, artifact store).
   - Implement `src/antigravity/storage/serializer.py` (`VariableSerializer`, `RestrictedUnpickler`, codec dispatch).

4. **Step 4: High-Level PersistenceManager**
   - Implement `src/antigravity/storage/manager.py` (`PersistenceManager` integrating engine, store, serializer, sandboxes, scheduler, models).
   - Expose package exports in `src/antigravity/storage/__init__.py`.

5. **Step 5: Subsystem Integrations**
   - Extend `local_repl_worker.py` and `local_sandbox.py` with `export_state` and `hydrate_state`.
   - Connect `TaskRegistry` to `PersistenceManager`.
   - Connect `SandboxManager` to `PersistenceManager`.

6. **Step 6: Comprehensive Pytest Verification**
   - Implement automated unit and process-boundary integration test suites in `tests/tier1_features/test_storage_features.py` and `tests/tier3_cross_feature/test_storage_process_boundary.py`.
   - Verify 100% pytest pass rate.
