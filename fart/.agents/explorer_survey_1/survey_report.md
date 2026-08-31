# Technical Survey & Architecture Report: R1 (MicroVM Sandbox & Execution Engine) and R4 (Scheduled Background Service Worker Daemon)

**Author:** Explorer Survey Agent 1 (`explorer_survey_1`)  
**Target Milestone:** Phase 0 (Survey & Scope Mapping)  
**Date:** 2026-08-29  
**Status:** Complete  

---

## 1. Executive Summary & Architectural Overview

This survey establishes the complete technical architecture, interface specifications, security models, error topologies, and modular decomposition for:
1. **R1: MicroVM Sandbox & Execution Engine** — A dual-layer Python code execution engine providing hardware-isolated microVM sandboxes via E2B (Firecracker/KVM) alongside an offline-first, highly secure Local Fallback Sandbox featuring AST validation, restricted builtins, and stateful subprocess-isolated REPL sessions.
2. **R4: Scheduled Background Service Worker Daemon** — An autonomous, non-blocking service worker orchestrator supporting 5-field cron schedules, one-shot duration timers, recurring intervals, task registries, worker execution inside sandboxes, and detailed execution logging.

### System Architecture Diagram

```
+---------------------------------------------------------------------------------------+
|                               Antigravity Runtime Host                                |
|                                                                                       |
|  +---------------------------------------------------------------------------------+  |
|  |             R4: Scheduled Background Service Worker Daemon                      |  |
|  |  +---------------------+  +----------------------+  +------------------------+  |  |
|  |  |  Task Registry &    |  |  Trigger Scheduler   |  |  Execution History     |  |  |
|  |  |  Priority Queue     |  |  (Cron / One-Shot)   |  |  & Health Monitor      |  |  |
|  |  +----------+----------+  +----------+-----------+  +-----------+------------+  |  |
|  |             |                        |                          |               |  |
|  |             +------------------------+--------------------------+               |  |
|  |                                      |                                          |  |
|  |                         Worker Dispatcher & Pool                                |  |
|  +--------------------------------------+------------------------------------------+  |
|                                         |                                             |
|                                         v                                             |
|  +---------------------------------------------------------------------------------+  |
|  |                    R1: Unified Sandbox Execution Engine                         |  |
|  |                                                                                 |  |
|  |    +-----------------------------+         +-------------------------------+    |  |
|  |    |     E2B Sandbox Backend     |         |     Local Fallback Backend    |    |  |
|  |    |  - Firecracker microVM      |         |  - AST Syntax & Import Guard  |    |  |
|  |    |  - KVM Hardware Isolation   |  [Fail] |  - Sanitized Builtins Table   |    |  |
|  |    |  - Remote REPL Session      | ------->|  - Subprocess Worker via IPC  |    |  |
|  |    |  - Snapshot & Pause/Resume  | (Auto)  |  - Persistent Session State   |    |  |
|  |    |  - e2b-code-interpreter SDK |         |  - Cross-Platform Timeouts    |    |  |
|  |    +--------------+--------------+         +---------------+---------------+    |  |
|  |                   |                                        |                    |  |
|  +-------------------|----------------------------------------|--------------------+  |
+----------------------|----------------------------------------|-----------------------+
                       |                                        |
                       v                                        v
          [Cloud: E2B Firecracker microVM]             [Local Subprocess Isolated OS]
```

---

## 2. Requirement R1: MicroVM Sandbox & Execution Engine

### 2.1 E2B Firecracker MicroVM Backend Architecture

#### 2.1.1 Core Principles & Technology Foundation
E2B (`e2b-code-interpreter` / `e2b` Python SDK) provisions cloud-native, sub-second (150–200ms cold start) Linux environments running in isolated AWS Firecracker microVMs over Kernel-based Virtual Machine (KVM) hypervisors. Unlike standard OS containers (Docker) which share the host kernel and rely on cgroups/namespaces, Firecracker provides hardware virtualization with a dedicated, lightweight guest kernel per sandbox.

#### 2.1.2 Integration Patterns with `e2b-code-interpreter`
The integration with E2B is structured as follows:
- **Sandbox Instantiation:** Instantiated via `CodeInterpreter.create(api_key=..., template=..., timeout=...)` or async equivalent `AsyncCodeInterpreter.create()`.
- **REPL Execution:** `sandbox.notebook.exec_cell(code)` submits Python code directly to a running Jupyter kernel inside the microVM.
- **Output & Artifact Capture:**
  - **Stdout / Stderr:** Streamed and collected into text buffers.
  - **Rich Output Formats (MIME):** Native parsing of `results` containing PNG/SVG charts (e.g. Matplotlib), HTML tables (e.g. Pandas DataFrames), JSON data, and plain text.
  - **Error Structures:** Exceptions in the guest kernel are captured structured as `ExecutionError(name=..., value=..., traceback=...)`.
- **Filesystem & Command Access:**
  - Filesystem manipulation: `sandbox.files.write(path, content)` / `sandbox.files.read(path)`.
  - Shell commands: `sandbox.commands.run(cmd)` for installing packages or running CLI tools.
- **State Management & Snapshots:**
  - Support for microVM pause, resume, and snapshot creation (`create_snapshot()`) to preserve memory state across long periods of inactivity without incurring compute costs.
- **Lifecycle & Cleanup:** Explicit lifecycle methods (`close()`, `kill()`) and asynchronous/synchronous context managers (`with CodeInterpreter() as sandbox:`) to prevent orphan cloud instances.

#### 2.1.3 Automatic Graceful Fallback Detection
The sandbox engine must implement a deterministic fallback protocol:
1. **API Key Check:** If `E2B_API_KEY` is empty, unset, or invalid.
2. **Network Reachability & Connectivity Check:** If HTTP/gRPC connection to `api.e2b.dev` fails or times out during initialization.
3. **Quota & Rate Limit Exhaustion:** If E2B returns HTTP 429, 401, or 503 errors.
4. **Behavioral Action:** On any detection trigger, the system logs a structured warning and transparently switches to the `LocalSandbox` backend (or respects an explicit user configuration `backend="local"` / `backend="e2b"` / `backend="auto"`).

---

### 2.2 Local Fallback Sandbox Execution Engine

To guarantee zero-dependency reliability in offline environments, CI/CD runners, and local developer machines, a secure `LocalSandbox` engine is implemented.

```
+------------------------------------------------------------------------------------+
|                         Local Fallback Sandbox Engine                              |
|                                                                                    |
|  [Code Input] --> [AST Validation] --> [Static Security Check]                     |
|                         |                     |                                    |
|                         v (Pass)              v (Violation -> Reject)             |
|                  [Worker IPC Channel]                                              |
|                         |                                                          |
|                         v                                                          |
|           +-------------------------------+                                        |
|           |   Isolated Python Subprocess  |                                        |
|           |   - Sanitized __builtins__    |                                        |
|           |   - Custom __import__ Hook    |                                        |
|           |   - Namespace Persistence     |                                        |
|           |   - Memory / Stream Redirect  |                                        |
|           +---------------+---------------+                                        |
|                           |                                                        |
|                           v                                                        |
|       [Timeout Enforcement & Output Capture (stdout/stderr)]                       |
+------------------------------------------------------------------------------------+
```

#### 2.2.1 Abstract Syntax Tree (AST) Security Validation
Before code is dispatched to execution, it is parsed via Python's standard `ast.parse()` and analyzed by an `ASTSecurityValidator(ast.NodeVisitor)`:

1. **AST Node Whitelisting:**
   - **Allowed Nodes:** Expressions (`Expr`, `BinOp`, `UnaryOp`, `BoolOp`, `Compare`), Control Flow (`If`, `For`, `While`, `Break`, `Continue`, `Pass`, `Try`, `ExceptHandler`, `With`), Data Structures (`List`, `Tuple`, `Dict`, `Set`, `Constant`, `FormattedValue`, `JoinedStr`), Definitions (`FunctionDef`, `AsyncFunctionDef`, `ClassDef`, `Return`, `Yield`, `YieldFrom`, `Assign`, `AugAssign`, `AnnAssign`, `Lambda`, `ListComp`, `DictComp`, `SetComp`, `GeneratorExp`).
   - **Disallowed Syntax Constructs:** `Global`, `Nonlocal` (when targeting outer sandbox internals), direct execution primitives (`Exec`, though obsolete in Python 3).

2. **Dunder & Introspection Traversal Prevention:**
   - Detect and block any `ast.Attribute` access to prohibited dunder names that allow escaping the sandbox via class hierarchies:
     - Prohibited attributes: `__subclasses__`, `__globals__`, `__code__`, `__builtins__`, `__class__`, `__bases__`, `__mro__`, `__dict__`, `__closure__`, `__qualname__`, `__module__`, `__import__`, `__loader__`, `__spec__`, `__func__`.
   - Detect string-based attribute access attacks (e.g. `getattr(obj, "__" + "subclasses__")`) through runtime wrapping of `getattr`, `setattr`, `delattr`.

3. **Module Import Whitelisting & Sandboxing:**
   - AST checks on `ast.Import` and `ast.ImportFrom`:
     - **Default Whitelisted Modules:** `math`, `json`, `random`, `datetime`, `re`, `collections`, `itertools`, `time`, `statistics`, `typing`, `string`, `decimal`, `fractions`, `functools`, `heapq`, `bisect`, `copy`, `dataclasses`, `enum`, `uuid`, `hashlib`, `base64`, `zlib`, `urllib.parse`.
     - **Strictly Prohibited Modules:** `os`, `sys`, `subprocess`, `socket`, `shutil`, `ctypes`, `importlib`, `pty`, `multiprocessing`, `threading` (unless sandboxed), `posix`, `nt`, `gc`, `signal`, `inspect`, `pickle`, `shelve`, `marshal`, `webbrowser`, `http.server`.
   - Extensibility: Support custom configuration `authorized_imports: list[str]` (mirroring the Hugging Face `smolagents` paradigm).

4. **Sanitized Builtins Dictionary:**
   - The execution namespace utilizes a heavily restricted `__builtins__` mapping:
     - **Removed / Blocked Builtins:** `open`, `compile`, `eval`, `exec`, `input`, `help`, `breakpoint`, `exit`, `quit`, `globals`, `locals`, `memoryview`, `vars`.
     - **Guarded Builtins:**
       - `__import__`: Custom hook that enforces the module whitelist at runtime.
       - `getattr`, `setattr`, `delattr`: Custom wrappers that raise `SecurityError` if accessing any attribute starting with `__`.
     - **Preserved Safe Builtins:** Standard math/collection primitives (`abs`, `all`, `any`, `bin`, `bool`, `bytes`, `callable`, `chr`, `complex`, `dict`, `dir`, `divmod`, `enumerate`, `filter`, `float`, `format`, `frozenset`, `hash`, `hex`, `int`, `isinstance`, `issubclass`, `iter`, `len`, `list`, `map`, `max`, `min`, `next`, `oct`, `ord`, `pow`, `print`, `range`, `repr`, `reversed`, `round`, `set`, `slice`, `sorted`, `str`, `sum`, `tuple`, `type`, `zip`).

#### 2.2.2 Process Isolation & Subprocess Architecture
To prevent CPU locking, infinite loops, memory leaks, and segmentation faults from affecting the host server process, local execution runs in a dedicated worker subprocess.

- **Execution Runner Script (`repl_runner.py`):**
  - A lightweight, self-contained Python script spawned via `subprocess.Popen([sys.executable, "-u", runner_path], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)`.
  - Communicates with the parent process via JSON-RPC / NDJSON over standard streams (`stdin` / `stdout`).
  - Implements the sandboxed `exec()` loop with redirected `sys.stdout` and `sys.stderr` capturing into in-memory `io.StringIO` buffers per turn.
- **Cross-Platform Timeout Enforcement:**
  - Controlled by the parent process using `asyncio.wait_for()` or `subprocess.communicate(timeout=...)`.
  - If execution exceeds `timeout_seconds`:
    1. Parent issues `terminate()` to worker process.
    2. Grace period (500ms) before forceful `kill()`.
    3. The session is marked as faulted, a fresh replacement worker process is spawned, and an `ExecutionTimeoutError` is returned.
- **Output Capping:**
  - Stdin/stdout capture limits (e.g. max 2MB per run) to prevent memory exhaustion from scripts generating massive output loops (`while True: print("A")`).

---

### 2.3 Persistent REPL Session State Mechanics

A central requirement for agentic workflows is the ability to execute sequential turns while maintaining variable, function, and class definitions across turns.

```
Agent Turn 1:  x = 42
               -> Output: None, State: {x: 42}
               
Agent Turn 2:  def compute(val): return val * 2
               -> Output: None, State: {x: 42, compute: <func>}
               
Agent Turn 3:  result = compute(x)
               print(f"Result: {result}")
               -> Output: "Result: 84", State: {x: 42, compute: <func>, result: 84}
```

#### 2.3.1 Local Stateful REPL Mechanics
- **Namespace Retention in Worker Process:**
  - The worker process maintains a persistent dictionary `session_globals = {"__builtins__": sanitized_builtins}`.
  - Successive calls to `exec(compiled_code, session_globals)` mutate and retain variables in `session_globals`.
- **Expression Value Evaluation (Jupyter-style):**
  - If the last statement in an AST block is an `ast.Expr`, it is separated, compiled with mode `'eval'`, and its evaluated return value is captured and returned in `results` (e.g. evaluating `df.head()` or `2 + 2` without explicit `print()`).
- **Session Reset & Variable Inspection:**
  - `reset_session()`: Clears `session_globals` back to the default sanitized environment without the latency of spawning a new process.
  - `get_variables()`: Returns a dictionary of variable names, types, and truncated representations (`repr`), filtering out internal builtins.
- **Fault Recovery & Self-Healing:**
  - If a fatal exception, out-of-memory condition, or timeout causes the subprocess to die, the `SandboxManager` detects the broken pipe, marks the session state, restarts the worker process, and reports a clear error without crashing the server.

---

## 3. Requirement R4: Scheduled Background Service Worker Daemon

### 3.1 Daemon Lifecycle & Event Loop

The Service Worker Daemon operates as an autonomous background scheduler managing tasks that execute independently of immediate client interactions.

```
+-----------------------------------------------------------------------------------+
|                        Service Worker Daemon State Machine                        |
|                                                                                   |
|       +-------------------------------------------------------------------+       |
|       |                                                                   |       |
|       v                                                                   |       |
|  [ STOPPED ] -- start() --> [ STARTING ] --> [ RUNNING ] -- pause() --> [ PAUSED ]|
|       ^                           |               |                        |      |
|       |                           v               v                        |      |
|       +--------------------- [ STOPPING ] <-------+------------------------+      |
|                               (Drain/Kill)                                        |
+-----------------------------------------------------------------------------------+
```

#### 3.1.1 State Machine & Threading Model
- **States:** `STOPPED`, `STARTING`, `RUNNING`, `PAUSED`, `STOPPING`.
- **AsyncIO Core Event Loop:**
  - Uses `asyncio.Task` loop running non-blocking sleep intervals calculated from the next pending task in the priority queue.
  - Thread-safe: Can run within an existing AsyncIO event loop or inside a dedicated background worker thread with its own event loop (`threading.Thread(target=daemon.run, daemon=True)`).
- **Graceful Shutdown Protocol:**
  - When `stop(timeout=10.0)` is invoked:
    1. Daemon state transitions to `STOPPING`.
    2. Event loop stops accepting new task executions.
    3. Active workers are given `shutdown_timeout` seconds to complete execution.
    4. Tasks exceeding the grace period are forcefully cancelled/terminated.
    5. Sandboxes and background resources are destroyed.
    6. State transitions to `STOPPED`.

---

### 3.2 Task Registry & Trigger Mechanics

#### 3.2.1 Data Models

```python
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Literal, Optional

class TaskStatus(str, Enum):
    PENDING = "pending"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"

class ScheduleType(str, Enum):
    CRON = "cron"
    ONE_SHOT = "one_shot"
    INTERVAL = "interval"

@dataclass
class TaskExecutionRecord:
    execution_id: str
    task_id: str
    started_at: datetime
    finished_at: Optional[datetime] = None
    duration_seconds: float = 0.0
    exit_code: int = 0
    stdout: str = ""
    stderr: str = ""
    result: Optional[Any] = None
    error: Optional[str] = None
    sandbox_backend: str = "unknown"

@dataclass
class ScheduledTask:
    task_id: str
    name: str
    schedule_type: ScheduleType
    schedule_spec: str                # e.g., "*/5 * * * *" or "300" (seconds)
    code_payload: str                # Python script to execute
    sandbox_backend: str = "auto"    # "auto", "e2b", "local"
    timeout_seconds: float = 60.0
    max_retries: int = 0
    retry_delay_seconds: float = 5.0
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    next_run_at: Optional[datetime] = None
    last_run_at: Optional[datetime] = None
    execution_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)
    execution_history: list[TaskExecutionRecord] = field(default_factory=list)
```

#### 3.2.2 Trigger Calculations
1. **Cron Expression Triggers (`croniter` / lightweight parser):**
   - Standard 5-field cron: `minute (0-59)`, `hour (0-23)`, `day of month (1-31)`, `month (1-12)`, `day of week (0-7, 0/7=Sun)`.
   - Supports wildcards (`*`), steps (`*/5`), ranges (`1-5`), and lists (`1,15,30`).
   - Calculation: `next_run_at = croniter(schedule_spec, base_time).get_next(datetime)`.
   - **Catch-up & Coalescing Policy:** If the daemon was paused or sleeping and multiple ticks elapsed, `coalesce=True` prevents a flood of executions by advancing `next_run_at` to the next future tick after running once.
2. **One-Shot Duration Timers:**
   - Specified as a delay in seconds (e.g. `delay_seconds=300`) or ISO duration.
   - `next_run_at = now + timedelta(seconds=delay)`.
   - Executes exactly once, then transitions status to `COMPLETED` (or `FAILED` if unrecoverable).
3. **Recurring Intervals:**
   - Specified as interval in seconds (e.g. `interval_seconds=60`).
   - `next_run_at = last_run_at + timedelta(seconds=interval)`.

---

### 3.3 Worker Execution in Isolated Sandboxes

When a scheduled task triggers:
1. **Concurrency Throttling:** Checked against an `asyncio.Semaphore(max_concurrent_workers)` (default: 5) to prevent host exhaustion.
2. **Sandbox Provisioning:** The scheduler requests a sandbox instance from the `SandboxManager` configured with the task's specified backend (`"auto"`, `"e2b"`, or `"local"`).
3. **Execution & Context Injection:**
   - Injects contextual variables into the sandbox session:
     ```python
     __TASK_CONTEXT__ = {
         "task_id": task.task_id,
         "task_name": task.name,
         "scheduled_time": task.next_run_at.isoformat(),
         "metadata": task.metadata
     }
     ```
   - Executes `task.code_payload` under the task's `timeout_seconds`.
4. **Result Recording & Status Transition:**
   - A `TaskExecutionRecord` is constructed containing full stdout, stderr, execution artifacts, duration, and error traces.
   - If successful:
     - For One-Shot: task marked `COMPLETED`.
     - For Cron/Interval: `execution_count += 1`, `next_run_at` recalculated, status returns to `SCHEDULED`.
   - If failed:
     - If `retry_count < max_retries`: schedule immediate retry after `retry_delay_seconds`.
     - If retries exhausted: mark `FAILED` (or for cron, log failure and schedule next future tick).
5. **Sandbox Teardown:** The ephemeral sandbox is terminated, or returned to the pool.

---

### 3.4 Execution Logging, Health Monitoring & Status Inspection

- **In-Memory & Persistent Task Registry:**
  - Thread-safe storage with support for task registration, lookup, modification, cancellation, and inspection.
  - History retention policy: Configurable maximum execution records per task (e.g. `max_history_records=50`) to bound memory footprint.
- **Inspection & Telemetry APIs:**
  - `list_tasks(status: Optional[TaskStatus] = None) -> list[ScheduledTask]`
  - `get_task(task_id: str) -> Optional[ScheduledTask]`
  - `get_task_history(task_id: str, limit: int = 10) -> list[TaskExecutionRecord]`
  - `get_daemon_metrics() -> dict[str, Any]` (uptime, total_tasks, active_workers, queue_depth, total_executions, failed_executions).
- **Health Monitoring & Orphan Reaping:**
  - Periodic background sweep (every 30s) checks for orphaned worker subprocesses, deadlocked tasks, or stale sandboxes, forcefully cleaning up resources.

---

## 4. Unified Python Interface Requirements & Class Contracts

### 4.1 Sandbox Interface (`src/antigravity/sandbox/base.py`)

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

class SandboxBackend(str, Enum):
    E2B = "e2b"
    LOCAL = "local"
    AUTO = "auto"

@dataclass
class ExecutionError:
    name: str
    value: str
    traceback: str

@dataclass
class ExecutionResult:
    stdout: str = ""
    stderr: str = ""
    results: List[Any] = field(default_factory=list)
    error: Optional[ExecutionError] = None
    exit_code: int = 0
    duration_seconds: float = 0.0
    backend_used: str = "local"

    @property
    def is_success(self) -> bool:
        return self.exit_code == 0 and self.error is None

@dataclass
class SandboxConfig:
    backend: SandboxBackend = SandboxBackend.AUTO
    timeout_seconds: float = 30.0
    e2b_api_key: Optional[str] = None
    e2b_template: Optional[str] = None
    authorized_imports: Optional[List[str]] = None
    max_output_bytes: int = 2 * 1024 * 1024  # 2MB
    memory_limit_mb: int = 512

class BaseSandbox(ABC):
    """Abstract Base Class for all Sandbox Execution Engines."""

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the sandbox environment (spin up microVM or worker process)."""
        pass

    @abstractmethod
    async def execute_code(self, code: str, timeout: Optional[float] = None) -> ExecutionResult:
        """Execute code in the persistent REPL session."""
        pass

    @abstractmethod
    async def reset_session(self) -> None:
        """Reset the REPL session state (clear variables)."""
        pass

    @abstractmethod
    async def get_variables(self) -> Dict[str, str]:
        """Inspect defined variables in the current session."""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Terminate the sandbox and clean up all allocated resources."""
        pass

    async def __aenter__(self) -> "BaseSandbox":
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()
```

### 4.2 Service Worker Daemon Interface (`src/antigravity/scheduler/daemon.py`)

```python
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from datetime import datetime
from .models import ScheduledTask, TaskExecutionRecord, TaskStatus, ScheduleType

class BaseSchedulerDaemon(ABC):
    """Abstract Base Class for the Service Worker Daemon."""

    @abstractmethod
    async def start(self) -> None:
        """Start the background scheduler event loop."""
        pass

    @abstractmethod
    async def stop(self, timeout: float = 10.0) -> None:
        """Gracefully stop the daemon and wait for running tasks."""
        pass

    @abstractmethod
    async def pause(self) -> None:
        """Pause task dispatching."""
        pass

    @abstractmethod
    async def resume(self) -> None:
        """Resume task dispatching."""
        pass

    @abstractmethod
    async def register_task(
        self,
        name: str,
        schedule_type: ScheduleType,
        schedule_spec: str,
        code_payload: str,
        sandbox_backend: str = "auto",
        timeout_seconds: float = 60.0,
        max_retries: int = 0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ScheduledTask:
        """Register a new scheduled task (cron or one-shot)."""
        pass

    @abstractmethod
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a registered task."""
        pass

    @abstractmethod
    async def get_task(self, task_id: str) -> Optional[ScheduledTask]:
        """Retrieve task details and status."""
        pass

    @abstractmethod
    async def list_tasks(self, status: Optional[TaskStatus] = None) -> List[ScheduledTask]:
        """List all tasks, optionally filtered by status."""
        pass

    @abstractmethod
    async def get_task_history(self, task_id: str, limit: int = 10) -> List[TaskExecutionRecord]:
        """Get execution history for a specific task."""
        pass

    @abstractmethod
    def get_metrics(self) -> Dict[str, Any]:
        """Get daemon telemetry and health metrics."""
        pass
```

---

## 5. Error Modes, Failure Scenarios & Mitigations

| Failure Mode | Root Cause | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- |
| **E2B API Key Missing / Auth Failed** | `E2B_API_KEY` not set in environment or invalid | E2B sandbox fails to provision | Immediate automatic fallback to `LocalSandbox` with warning log. |
| **Network Partition / E2B Outage** | E2B cloud unreachable, rate limits (HTTP 429), or 503 error | Request hangs or fails | Timeout on E2B initialization (5s max), catch network exceptions, seamless switch to `LocalSandbox`. |
| **Malicious Code Injection (AST Attack)** | Code attempts to access `__subclasses__()`, `__globals__`, or `os.system` | Potential host system compromise | `ASTSecurityValidator` rejects forbidden AST nodes and dunder attribute lookups before execution. |
| **Forbidden Module Import** | Code attempts `import os`, `import socket`, `import subprocess` | Unauthorized filesystem/network access | AST validator blocks import statements; runtime `__import__` hook blocks dynamic imports. |
| **Infinite Loop / CPU Hog** | Code contains `while True: pass` or heavy recursive calls | Host process locks up, high CPU | Subprocess timeout via `asyncio.wait_for()`. Subprocess is killed (`SIGKILL`) and clean `ExecutionTimeoutError` returned. |
| **Memory Exhaustion (OOM)** | Code allocates massive arrays or unbounded lists | Host system memory pressure | Output stream truncation; OS subprocess memory limit / watchdog; crash detection and sandbox recycling. |
| **Large Stdout Flood** | Code prints gigabytes of logs in a tight loop | Buffer overflow / memory exhaustion | Output stream capture truncates at `max_output_bytes` (e.g. 2MB) with warning message appended. |
| **REPL Session Crash / Segfault** | Native library crash or unhandled C-extension fault | Subprocess dies unexpectedly | Subprocess death detected via pipe EOF; session state marked faulted; fresh replacement worker spawned. |
| **Missed Cron Ticks (System Sleep)** | Host system was suspended or daemon paused during scheduled tick | Accumulated backlog of tasks | `coalesce=True` policy executes the task once and advances `next_run_at` to the next upcoming tick. |
| **Worker Concurrency Starvation** | Many tasks trigger simultaneously | Resource exhaustion / high latency | `asyncio.Semaphore(max_concurrent_workers)` queues executions; worker queue prioritized by trigger timestamp. |
| **Orphan Subprocesses / MicroVMs** | Unexpected daemon termination or unhandled crash | Leaked processes / cloud costs | Context managers, `atexit` cleanup hooks, and periodic orphan reaper task. |

---

## 6. Dependencies & Platform Compatibility

### 6.1 Dependency Matrix

```toml
[project]
name = "antigravity-mcp"
version = "0.1.0"
description = "Antigravity MCP Server and Customization Plugin with E2B MicroVM and Service Worker Daemon"
requires-python = ">=3.10"

dependencies = [
    # Core MCP Protocol
    "mcp>=1.0.0",
    "pydantic>=2.0.0",
    # Scheduler
    "croniter>=2.0.0",
]

[project.optional-dependencies]
e2b = [
    "e2b-code-interpreter>=1.0.0",
    "e2b>=1.0.0",
]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "pytest-cov>=4.1.0",
]
```

### 6.2 Zero-Hard-Dependency Fallback Architecture
- **E2B Isolation:** `e2b-code-interpreter` is an **optional runtime dependency**. If not installed or if no API key is present, the codebase uses standard dynamic import detection (`importlib.util.find_spec("e2b_code_interpreter")`) and automatically operates in `LocalSandbox` mode.
- **Cron Parsing:** `croniter` is lightweight and pure Python. A built-in simplified 5-field cron parser is also provided as a secondary fallback.
- **Platform Support:** Fully cross-platform compatible with **Windows (PowerShell/CMD)**, **Linux (Ubuntu/Debian/RHEL)**, and **macOS (Darwin)**.

---

## 7. Recommended Module Decomposition for Implementation

```
src/antigravity/
├── __init__.py
├── sandbox/
│   ├── __init__.py
│   ├── base.py                 # Abstract BaseSandbox, ExecutionResult, ExecutionError, SandboxConfig
│   ├── ast_validator.py        # ASTSecurityValidator, SecurityPolicy, node/attribute/import whitelists
│   ├── builtins_guard.py       # Sanitized builtins dictionary and guarded __import__ hook
│   ├── repl_runner.py          # Standalone runner script executed in isolated subprocess
│   ├── local_sandbox.py        # LocalSandbox implementation with process IPC & session persistence
│   ├── e2b_sandbox.py          # E2BSandbox implementation wrapping e2b-code-interpreter
│   └── manager.py              # SandboxManager: lifecycle orchestration, pooling, and auto-fallback
│
├── scheduler/
│   ├── __init__.py
│   ├── models.py               # ScheduledTask, TaskExecutionRecord, TaskStatus, ScheduleType
│   ├── cron.py                 # Cron schedule evaluator and next-tick calculator
│   ├── timer.py                # One-shot timer and interval primitives
│   ├── registry.py             # Thread-safe in-memory and persistent task registry
│   ├── daemon.py               # ServiceWorkerDaemon core event loop and worker dispatcher
│   └── health.py               # Health monitor, orphan reaper, and telemetry metrics collector
│
└── utils/
    ├── __init__.py
    ├── logging.py              # Structured JSON/console logging
    └── platform.py             # Cross-platform process and path utilities
```

---

## 8. Summary of Findings & Next Steps

1. **R1 (Sandbox Engine)** is fully defined with a resilient two-tier architecture:
   - Tier 1: Cloud-native Firecracker microVMs via E2B with snapshot/pause capabilities.
   - Tier 2: Secure Local Sandbox with AST-level validation, blocked dunder introspection, sanitized builtins, subprocess isolation, and stateful multi-turn REPL persistence.
2. **R4 (Service Worker Daemon)** is fully specified with an AsyncIO event loop, standard 5-field cron support, one-shot duration timers, concurrency throttling, and structured execution telemetry.
3. **Seamless Integration**: The scheduler directly consumes the sandbox engine abstraction, enabling scheduled background jobs to run inside hardware microVMs or secure local sandboxes transparently.

This survey report provides the complete blueprint for the implementation agents in Phase 1.
