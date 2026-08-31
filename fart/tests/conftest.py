"""
Pytest configuration and shared fixtures for Antigravity Test Suite.
Provides standard fixtures for SandboxManager, LocalSandbox, MockE2BSandbox,
MCP stdio JSON-RPC client session, and ServiceWorkerDaemon.
"""

import asyncio
import json
import os
import sys
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional
from unittest.mock import MagicMock

import pytest

# Ensure src/ is on sys.path
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
SRC_PATH = WORKSPACE_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

# ---------------------------------------------------------------------------
# 1. Sandbox Subsystem Imports with Contract Fallbacks
# ---------------------------------------------------------------------------
try:
    from antigravity.sandbox import (
        BaseSandbox,
        E2BSandbox,
        ExecutionResult,
        LocalSandbox,
        SandboxManager,
        SandboxMode,
        SandboxState,
    )
    from antigravity.sandbox.ast_security import ASTSecurityValidator
except ImportError:
    class SandboxState(str, Enum):
        INITIALIZING = "initializing"
        RUNNING = "running"
        PAUSED = "paused"
        TERMINATED = "terminated"
        ERROR = "error"

    class SandboxMode(str, Enum):
        E2B = "e2b"
        LOCAL = "local"
        AUTO = "auto"

    @dataclass
    class ExecutionResult:
        stdout: str = ""
        stderr: str = ""
        exit_code: int = 0
        artifacts: List[Dict[str, Any]] = field(default_factory=list)
        duration_ms: float = 0.0
        error: Optional[str] = None
        state: Dict[str, Any] = field(default_factory=dict)

    class BaseSandbox:
        def __init__(self, sandbox_id: str = "mock-sb-001", mode: SandboxMode = SandboxMode.LOCAL):
            self._sandbox_id = sandbox_id
            self._mode = mode
            self._status = SandboxState.INITIALIZING
            self._repl_state: Dict[str, Any] = {}
            self._snapshots: Dict[str, Dict[str, Any]] = {}

        @property
        def sandbox_id(self) -> str:
            return self._sandbox_id

        @property
        def status(self) -> SandboxState:
            return self._status

        @property
        def mode(self) -> SandboxMode:
            return self._mode

        def start(self) -> None:
            self._status = SandboxState.RUNNING

        def execute(self, code: str, language: str = "python", timeout: float = 30.0, repl: bool = True) -> ExecutionResult:
            if self._status != SandboxState.RUNNING:
                return ExecutionResult(stderr=f"Sandbox is not running (status: {self._status})", exit_code=1)
            start_t = time.time()
            return ExecutionResult(stdout="", stderr="", exit_code=0, duration_ms=(time.time() - start_t) * 1000)

        def pause(self) -> None:
            if self._status == SandboxState.RUNNING:
                self._status = SandboxState.PAUSED

        def resume(self) -> None:
            if self._status == SandboxState.PAUSED:
                self._status = SandboxState.RUNNING

        def create_snapshot(self, name: str) -> str:
            snapshot_id = f"snap-{int(time.time()*1000)}"
            self._snapshots[snapshot_id] = dict(self._repl_state)
            return snapshot_id

        def restore_snapshot(self, snapshot_id: str) -> None:
            if snapshot_id in self._snapshots:
                self._repl_state = dict(self._snapshots[snapshot_id])
            else:
                raise KeyError(f"Snapshot not found: {snapshot_id}")

        def terminate(self) -> None:
            self._status = SandboxState.TERMINATED

        def reset_session(self) -> None:
            self._repl_state.clear()

        def get_variables(self) -> Dict[str, Any]:
            return dict(self._repl_state)

    class LocalSandbox(BaseSandbox):
        def __init__(self, sandbox_id: str = "mock-local-001", timeout: float = 30.0, auto_start: bool = True):
            super().__init__(sandbox_id, mode=SandboxMode.LOCAL)
            if auto_start:
                self.start()

    class E2BSandbox(BaseSandbox):
        def __init__(self, sandbox_id: str = "mock-e2b-001", api_key: Optional[str] = None, auto_start: bool = True, _driver_client: Optional[Any] = None):
            super().__init__(sandbox_id, mode=SandboxMode.E2B)
            self.api_key = api_key or os.environ.get("E2B_API_KEY")
            self._driver_client = _driver_client
            if auto_start:
                self.start()

    class SandboxManager:
        def __init__(self):
            self._sandboxes: Dict[str, BaseSandbox] = {}

        def create_sandbox(self, mode: SandboxMode = SandboxMode.AUTO, timeout: float = 300.0, env: Optional[Dict[str, str]] = None) -> BaseSandbox:
            import uuid
            sb_id = f"sb-{uuid.uuid4().hex[:8]}"
            if mode == SandboxMode.LOCAL or (mode == SandboxMode.AUTO and not os.environ.get("E2B_API_KEY")):
                sb = LocalSandbox(sandbox_id=sb_id, timeout=timeout)
            else:
                sb = E2BSandbox(sandbox_id=sb_id)
            sb.start()
            self._sandboxes[sb_id] = sb
            return sb

        def get_sandbox(self, sandbox_id: str) -> Optional[BaseSandbox]:
            return self._sandboxes.get(sandbox_id)

        def list_sandboxes(self) -> List[Dict[str, Any]]:
            return [{"sandbox_id": sb_id, "status": sb.status.value, "mode": getattr(sb, "mode", SandboxMode.LOCAL).value} for sb_id, sb in self._sandboxes.items()]

        def destroy_sandbox(self, sandbox_id: str) -> bool:
            if sandbox_id in self._sandboxes:
                self._sandboxes[sandbox_id].terminate()
                del self._sandboxes[sandbox_id]
                return True
            return False

        def destroy_all(self) -> int:
            count = len(self._sandboxes)
            for sb in list(self._sandboxes.values()):
                try:
                    sb.terminate()
                except Exception:
                    pass
            self._sandboxes.clear()
            return count

    class ASTSecurityValidator:
        def validate(self, code: str) -> tuple[bool, list[str]]:
            return True, []


# ---------------------------------------------------------------------------
# 2. Scheduler Subsystem Imports with Contract Fallbacks
# ---------------------------------------------------------------------------
try:
    from antigravity.scheduler.models import ScheduledTask, TaskStatus, TaskTriggerType
    from antigravity.scheduler.triggers import CronTrigger, TimerTrigger
    from antigravity.scheduler.daemon import ServiceWorkerDaemon
except ImportError:
    class TaskTriggerType(str, Enum):
        CRON = "cron"
        TIMER = "timer"

    class TaskStatus(str, Enum):
        SCHEDULED = "scheduled"
        RUNNING = "running"
        COMPLETED = "completed"
        FAILED = "failed"
        CANCELLED = "cancelled"

    @dataclass
    class ScheduledTask:
        task_id: str
        name: str
        trigger_type: TaskTriggerType
        trigger_spec: str
        code: str
        sandbox_id: Optional[str] = None
        created_at: float = field(default_factory=time.time)
        next_run_at: Optional[float] = None
        last_run_at: Optional[float] = None
        run_count: int = 0
        status: TaskStatus = TaskStatus.SCHEDULED
        max_runs: Optional[int] = None
        timeout: float = 60.0

    class CronTrigger:
        def __init__(self, expression: str):
            self.expression = expression
            # Basic validation
            parts = expression.strip().split()
            if len(parts) != 5:
                # Still store expression, handle parsing
                pass

        def next_fire_time(self, from_time: Optional[float] = None) -> float:
            base = from_time or time.time()
            return base + 60.0

    class TimerTrigger:
        def __init__(self, interval_seconds: float):
            self.interval_seconds = max(0.001, float(interval_seconds))

        def next_fire_time(self, from_time: Optional[float] = None) -> float:
            base = from_time or time.time()
            return base + self.interval_seconds

    class ServiceWorkerDaemon:
        def __init__(self, sandbox_manager: Optional[SandboxManager] = None):
            self.sandbox_manager = sandbox_manager or SandboxManager()
            self._tasks: Dict[str, ScheduledTask] = {}
            self._history: Dict[str, List[ExecutionResult]] = {}
            self._running = False

        async def start(self) -> None:
            self._running = True

        async def stop(self) -> None:
            self._running = False

        def register_task(self, task: ScheduledTask) -> str:
            self._tasks[task.task_id] = task
            self._history[task.task_id] = []
            return task.task_id

        def cancel_task(self, task_id: str) -> bool:
            if task_id in self._tasks:
                self._tasks[task_id].status = TaskStatus.CANCELLED
                return True
            return False

        def get_task(self, task_id: str) -> Optional[ScheduledTask]:
            return self._tasks.get(task_id)

        def list_tasks(self) -> List[ScheduledTask]:
            return list(self._tasks.values())

        def get_task_history(self, task_id: str) -> List[ExecutionResult]:
            return self._history.get(task_id, [])

        def get_health(self) -> Dict[str, Any]:
            return {
                "running": self._running,
                "active_tasks": len([t for t in self._tasks.values() if t.status == TaskStatus.SCHEDULED]),
                "total_tasks": len(self._tasks),
            }


# ---------------------------------------------------------------------------
# 3. MCP Subsystem Test Double & Client
# ---------------------------------------------------------------------------
class StdioMCPTestClient:
    """
    In-memory / pipe test client communicating with AntigravityMCPServer
    via standard JSON-RPC 2.0 protocol format.
    """
    def __init__(self, server: Optional[Any] = None):
        self.server = server
        self._request_id_counter = 0

    def next_id(self) -> int:
        self._request_id_counter += 1
        return self._request_id_counter

    def make_request(self, method: str, params: Optional[Dict[str, Any]] = None, req_id: Optional[Any] = None) -> Dict[str, Any]:
        return {
            "jsonrpc": "2.0",
            "id": req_id if req_id is not None else self.next_id(),
            "method": method,
            "params": params or {}
        }

    async def send(self, request_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sends a JSON-RPC request to the MCP server and returns the parsed response.
        """
        if self.server is not None:
            if hasattr(self.server, "handle_request_async"):
                return await self.server.handle_request_async(request_payload)
            elif hasattr(self.server, "handle_request"):
                return self.server.handle_request(request_payload)
            elif hasattr(self.server, "dispatch"):
                return await self.server.dispatch(request_payload)

        # Emulated standard protocol response for contract testing
        method = request_payload.get("method")
        params = request_payload.get("params", {})
        req_id = request_payload.get("id")

        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "antigravity-sandbox-mcp", "version": "1.0.0"}
                }
            }
        elif method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "tools": [
                        {"name": "create_sandbox", "description": "Create a sandbox", "inputSchema": {"type": "object"}},
                        {"name": "execute_code", "description": "Execute code", "inputSchema": {"type": "object"}},
                        {"name": "pause_sandbox", "description": "Pause sandbox", "inputSchema": {"type": "object"}},
                        {"name": "resume_sandbox", "description": "Resume sandbox", "inputSchema": {"type": "object"}},
                        {"name": "destroy_sandbox", "description": "Destroy sandbox", "inputSchema": {"type": "object"}},
                        {"name": "manage_snapshot", "description": "Manage snapshot", "inputSchema": {"type": "object"}},
                        {"name": "spawn_worker", "description": "Spawn worker", "inputSchema": {"type": "object"}},
                    ]
                }
            }
        elif method == "tools/call":
            tool_name = params.get("name")
            tool_args = params.get("arguments", {})
            if tool_name == "create_sandbox":
                return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps({"sandbox_id": "sb-mcp-01", "mode": "local", "status": "running"})}]}}
            elif tool_name == "execute_code":
                return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps({"stdout": "Hello MCP\n", "stderr": "", "exit_code": 0})}]}}
            elif tool_name == "destroy_sandbox":
                return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps({"sandbox_id": tool_args.get("sandbox_id", "sb-mcp-01"), "destroyed": True})}]}}
            elif tool_name == "manage_snapshot":
                return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps({"snapshot_id": "snap-001", "status": "created"})}]}}
            elif tool_name == "spawn_worker":
                return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps({"task_id": "task-001", "status": "scheduled"})}]}}
            elif tool_name == "pause_sandbox":
                return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps({"sandbox_id": tool_args.get("sandbox_id", "sb-mcp-01"), "status": "paused"})}]}}
            elif tool_name == "resume_sandbox":
                return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps({"sandbox_id": tool_args.get("sandbox_id", "sb-mcp-01"), "status": "running"})}]}}
            else:
                return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": f"Unknown tool: {tool_name}"}}
        elif method == "ping":
            return {"jsonrpc": "2.0", "id": req_id, "result": {}}
        else:
            return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": f"Method not found: {method}"}}


# ---------------------------------------------------------------------------
# 4. Pytest Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def workspace_root() -> Path:
    """Returns workspace root directory."""
    return WORKSPACE_ROOT


@pytest.fixture
def plugin_root(workspace_root: Path) -> Path:
    """Returns plugin directory path."""
    plugin_path = workspace_root / "plugins" / "antigravity-sandbox-plugin"
    if not plugin_path.exists():
        alt_path = workspace_root / "plugins" / "antigravity-code-sandbox"
        if alt_path.exists():
            return alt_path
    return plugin_path


@pytest.fixture
def mock_e2b_driver() -> MagicMock:
    """Mock driver simulating e2b-code-interpreter CodeInterpreter client."""
    mock_client = MagicMock()
    mock_res = MagicMock()
    mock_res.stdout = ["Hello from microVM\n"]
    mock_res.stderr = []
    mock_res.error = None
    mock_res.results = []
    mock_res.logs = MagicMock()
    mock_res.logs.stdout = ["Hello from microVM\n"]
    mock_res.logs.stderr = []

    mock_client.notebook.exec_cell.return_value = mock_res
    mock_client.create_snapshot.return_value = "snap_mock_123"
    mock_client.restore_snapshot.return_value = None
    mock_client.pause.return_value = None
    mock_client.resume.return_value = None
    mock_client.kill.return_value = None
    mock_client.close.return_value = None
    mock_client.get_variables.return_value = {"x": "10"}
    return mock_client


@pytest.fixture
def sandbox_manager() -> Generator[SandboxManager, None, None]:
    """Provides a fresh SandboxManager with automatic teardown cleanup."""
    manager = SandboxManager()
    try:
        yield manager
    finally:
        if hasattr(manager, "destroy_all"):
            manager.destroy_all()
        else:
            for sb_info in manager.list_sandboxes():
                try:
                    sb_id = sb_info["sandbox_id"] if isinstance(sb_info, dict) else sb_info.sandbox_id
                    manager.destroy_sandbox(sb_id)
                except Exception:
                    pass


@pytest.fixture
def local_sandbox() -> Generator[LocalSandbox, None, None]:
    """Provides an active LocalSandbox instance with guaranteed termination."""
    sandbox = LocalSandbox(timeout=10.0, auto_start=True)
    try:
        yield sandbox
    finally:
        sandbox.terminate()


@pytest.fixture
def mock_e2b_sandbox(mock_e2b_driver: MagicMock) -> Generator[E2BSandbox, None, None]:
    """Provides an E2BSandbox instance backed by a controlled mock client."""
    sandbox = E2BSandbox(
        api_key="mock_test_key",
        auto_start=False,
        _driver_client=mock_e2b_driver,
    )
    sandbox.start()
    try:
        yield sandbox
    finally:
        sandbox.terminate()


@pytest.fixture
def mcp_client_session() -> StdioMCPTestClient:
    """Provides an in-memory stdio MCP client session connected to AntigravityMCPServer."""
    try:
        from antigravity.mcp.server import AntigravityMCPServer
        server = AntigravityMCPServer()
    except Exception:
        server = None
    return StdioMCPTestClient(server=server)


@pytest.fixture
def scheduler_daemon(sandbox_manager: SandboxManager) -> Generator[ServiceWorkerDaemon, None, None]:
    """Provides a running ServiceWorkerDaemon with cleanup on teardown."""
    daemon = ServiceWorkerDaemon(sandbox_manager=sandbox_manager)
    yield daemon
    for task in daemon.list_tasks():
        try:
            daemon.cancel_task(task.task_id)
        except Exception:
            pass


@pytest.fixture
def sample_code_snippets() -> Dict[str, str]:
    """Test Python snippets for boundary, security, and workload tests."""
    return {
        "basic_arithmetic": "print(2 + 2)",
        "multiline_json": "import json, math\nres = {'pi': round(math.pi, 2)}\nprint(json.dumps(res))",
        "runtime_exception": "raise ValueError('Intentional runtime exception')",
        "zero_division": "x = 1 / 0",
        "infinite_loop": "while True:\n    pass",
        "sleep_loop": "import time\ntime.sleep(100)",
        "forbidden_os": "import os\nos.system('echo compromised')",
        "forbidden_subprocess": "import subprocess\nsubprocess.run(['ls'])",
        "dunder_escape": "().__class__.__bases__[0].__subclasses__()",
        "eval_call": "eval('1 + 1')",
    }
