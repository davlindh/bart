"""
MCP Tool Registry and Implementations for Antigravity Platform.

Exposes the 7 required MCP tools integrating with SandboxManager
and ServiceWorkerDaemon:
  1. create_sandbox
  2. execute_code
  3. pause_sandbox
  4. resume_sandbox
  5. destroy_sandbox
  6. manage_snapshot
  7. spawn_worker
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple, Type

from pydantic import ValidationError

from antigravity.sandbox.base import BaseSandbox
from antigravity.sandbox.local_sandbox import LocalSandbox
from antigravity.sandbox.manager import SandboxManager
from antigravity.sandbox.models import (
    ExecutionResult,
    SandboxError,
    SandboxMode,
    SandboxState,
    SecurityViolationError,
)

from .protocol import (
    AST_SECURITY_VIOLATION,
    EXECUTION_TIMEOUT,
    INTERNAL_ERROR,
    INVALID_PARAMS,
    METHOD_NOT_FOUND,
    MODEL_INFERENCE_ERROR,
    MODEL_LOAD_ERROR,
    MODEL_NOT_FOUND,
    PERSISTENCE_NOT_FOUND,
    PERSISTENCE_READ_ERROR,
    PERSISTENCE_WRITE_ERROR,
    SANDBOX_NOT_FOUND,
    WORKER_SCHEDULE_ERROR,
    InvalidParamsError,
    JsonRpcError,
    MethodNotFoundError,
    ModelInferenceError,
    ModelLoadError,
    ModelNotFoundError,
    PersistenceNotFoundError,
    PersistenceReadError,
    PersistenceWriteError,
    SandboxNotFoundError,
    ToolError,
    log_stderr,
)
from .schemas import (
    TOOL_SCHEMAS,
    ChatMessageItem,
    CreateSandboxInput,
    DestroySandboxInput,
    ExecuteCodeInput,
    ListPersistedSandboxesInput,
    LoadModelInput,
    ManageSnapshotInput,
    ModelChatInput,
    ModelGenerateInput,
    PauseSandboxInput,
    PersistSandboxInput,
    RestoreSandboxDiskInput,
    ResumeSandboxInput,
    SpawnWorkerInput,
    ToolCallResult,
)

# ---------------------------------------------------------------------------
# Storage & Model Subsystem Imports with Graceful Fallbacks
# ---------------------------------------------------------------------------
try:
    from antigravity.storage.persistence_manager import PersistenceManager
    from antigravity.storage.models import StorageError, StorageNotFoundError
except ImportError:
    try:
        from antigravity.storage import PersistenceManager
        from antigravity.storage.models import StorageError, StorageNotFoundError
    except ImportError:
        PersistenceManager = None
        StorageError = Exception
        StorageNotFoundError = Exception

try:
    from antigravity.models.runner import LocalModelRunner
    from antigravity.models.models import (
        ChatMessage,
        GenerationConfig,
        GenerationResult,
        ModelBackend,
        ModelConfig,
    )
except ImportError:
    try:
        from antigravity.models import (
            ChatMessage,
            GenerationConfig,
            GenerationResult,
            LocalModelRunner,
            ModelBackend,
            ModelConfig,
        )
    except ImportError:
        LocalModelRunner = None
        ModelConfig = None
        GenerationConfig = None
        ChatMessage = None
        GenerationResult = None
        ModelBackend = None

logger = logging.getLogger("antigravity.mcp.tools")


# ---------------------------------------------------------------------------
# Graceful Scheduler Contract Support
# ---------------------------------------------------------------------------
try:
    from antigravity.scheduler.daemon import ServiceWorkerDaemon
    from antigravity.scheduler.models import ScheduledTask, TaskStatus, TaskTriggerType
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

    class ServiceWorkerDaemon:  # type: ignore[no-redef]
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
# Tool Implementations
# ---------------------------------------------------------------------------
class MCPToolRegistry:
    """
    Registry for MCP Tools. Dispatches tool requests to concrete handlers
    connected to SandboxManager, ServiceWorkerDaemon, PersistenceManager,
    and LocalModelRunner.
    """

    def __init__(
        self,
        sandbox_manager: Optional[SandboxManager] = None,
        scheduler_daemon: Optional[ServiceWorkerDaemon] = None,
        persistence_manager: Optional[Any] = None,
        model_runner: Optional[Any] = None,
    ) -> None:
        self.sandbox_manager = sandbox_manager or SandboxManager()
        self.scheduler_daemon = scheduler_daemon or ServiceWorkerDaemon(sandbox_manager=self.sandbox_manager)
        self.persistence_manager = persistence_manager
        self.model_runner = model_runner
        self._tools: Dict[str, Tuple[Callable[..., Any], Type[Any]]] = {
            "create_sandbox": (self._handle_create_sandbox, CreateSandboxInput),
            "execute_code": (self._handle_execute_code, ExecuteCodeInput),
            "pause_sandbox": (self._handle_pause_sandbox, PauseSandboxInput),
            "resume_sandbox": (self._handle_resume_sandbox, ResumeSandboxInput),
            "destroy_sandbox": (self._handle_destroy_sandbox, DestroySandboxInput),
            "manage_snapshot": (self._handle_manage_snapshot, ManageSnapshotInput),
            "spawn_worker": (self._handle_spawn_worker, SpawnWorkerInput),
            "load_model": (self._handle_load_model, LoadModelInput),
            "model_generate": (self._handle_model_generate, ModelGenerateInput),
            "model_chat": (self._handle_model_chat, ModelChatInput),
            "persist_sandbox": (self._handle_persist_sandbox, PersistSandboxInput),
            "restore_sandbox_disk": (self._handle_restore_sandbox_disk, RestoreSandboxDiskInput),
            "list_persisted_sandboxes": (self._handle_list_persisted_sandboxes, ListPersistedSandboxesInput),
        }

    def list_tools(self) -> List[Dict[str, Any]]:
        """Return schema catalog for all registered tools."""
        return list(TOOL_SCHEMAS)

    def has_tool(self, name: str) -> bool:
        """Check if tool name is registered."""
        return name in self._tools

    def _get_or_create_sandbox(self, sandbox_id: str, timeout: float = 300.0) -> BaseSandbox:
        """Retrieve existing sandbox or auto-provision local sandbox if missing."""
        sb = self.sandbox_manager.get_sandbox(sandbox_id)
        if sb is None:
            sb = LocalSandbox(sandbox_id=sandbox_id, timeout=timeout, auto_start=True)
            self.sandbox_manager._sandboxes[sandbox_id] = sb
        return sb

    def _get_persistence_manager(self, storage_path: Optional[str] = None) -> Any:
        """Retrieve or initialize persistence manager instance."""
        if storage_path is not None:
            if PersistenceManager is not None:
                return PersistenceManager(base_dir=storage_path)
        if self.persistence_manager is not None:
            return self.persistence_manager
        if PersistenceManager is not None:
            self.persistence_manager = PersistenceManager()
            return self.persistence_manager
        raise StorageError("PersistenceManager subsystem unavailable.")

    def _get_model_runner(self) -> Any:
        """Retrieve or initialize local model runner instance."""
        if self.model_runner is not None:
            return self.model_runner
        if LocalModelRunner is not None:
            self.model_runner = LocalModelRunner()
            return self.model_runner
        raise ModelLoadError("LocalModelRunner subsystem unavailable.")

    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute an MCP tool by name with arguments dictionary.
        Returns a standardized MCP ToolCallResult payload dictionary.
        """
        if name not in self._tools:
            log_stderr(f"Unknown tool requested: {name}", level="WARNING")
            raise MethodNotFoundError(f"Unknown tool: '{name}'")

        handler, schema_cls = self._tools[name]

        # 1. Parse and validate arguments against Pydantic schema
        try:
            parsed_args = schema_cls(**arguments)
        except ValidationError as val_err:
            log_stderr(f"Argument validation failed for tool '{name}': {val_err}", level="ERROR")
            err_dict = {
                "error": f"Invalid arguments for {name}: {val_err}",
                "exit_code": 1,
                "is_error": True,
            }
            return {
                "content": [{"type": "text", "text": json.dumps(err_dict)}],
                "isError": True,
            }
        except Exception as e:
            err_dict = {
                "error": f"Error parsing arguments for {name}: {e}",
                "exit_code": 1,
                "is_error": True,
            }
            return {
                "content": [{"type": "text", "text": json.dumps(err_dict)}],
                "isError": True,
            }

        # 2. Execute handler
        try:
            if asyncio.iscoroutinefunction(handler):
                result_payload = await handler(parsed_args)
            else:
                result_payload = handler(parsed_args)

            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(result_payload, ensure_ascii=False) if not isinstance(result_payload, str) else result_payload,
                    }
                ],
                "isError": False,
            }

        except SandboxNotFoundError as s_err:
            log_stderr(f"Sandbox not found: {s_err}", level="ERROR")
            err_dict = {"error": str(s_err), "exit_code": 1, "is_error": True}
            return {
                "content": [{"type": "text", "text": json.dumps(err_dict)}],
                "isError": True,
            }
        except SecurityViolationError as sec_err:
            log_stderr(f"Security violation: {sec_err}", level="ERROR")
            err_dict = {"error": str(sec_err), "exit_code": 1, "is_error": True}
            return {
                "content": [{"type": "text", "text": json.dumps(err_dict)}],
                "isError": True,
            }
        except SandboxError as sb_err:
            log_stderr(f"Sandbox error: {sb_err}", level="ERROR")
            err_dict = {"error": str(sb_err), "exit_code": 1, "is_error": True}
            return {
                "content": [{"type": "text", "text": json.dumps(err_dict)}],
                "isError": True,
            }
        except (ModelNotFoundError, ModelLoadError, ModelInferenceError) as m_err:
            log_stderr(f"Model error in '{name}': {m_err}", level="ERROR")
            err_dict = {"error": str(m_err), "code": getattr(m_err, "code", -32011), "is_error": True}
            return {
                "content": [{"type": "text", "text": json.dumps(err_dict)}],
                "isError": True,
            }
        except (PersistenceNotFoundError, PersistenceWriteError, PersistenceReadError) as p_err:
            log_stderr(f"Persistence error in '{name}': {p_err}", level="ERROR")
            err_dict = {"error": str(p_err), "code": getattr(p_err, "code", -32020), "is_error": True}
            return {
                "content": [{"type": "text", "text": json.dumps(err_dict)}],
                "isError": True,
            }
        except StorageNotFoundError as snf_err:
            log_stderr(f"Storage not found: {snf_err}", level="ERROR")
            err_dict = {"error": str(snf_err), "code": PERSISTENCE_NOT_FOUND, "is_error": True}
            return {
                "content": [{"type": "text", "text": json.dumps(err_dict)}],
                "isError": True,
            }
        except StorageError as st_err:
            log_stderr(f"Storage error: {st_err}", level="ERROR")
            err_dict = {"error": str(st_err), "code": PERSISTENCE_WRITE_ERROR, "is_error": True}
            return {
                "content": [{"type": "text", "text": json.dumps(err_dict)}],
                "isError": True,
            }
        except Exception as exc:
            log_stderr(f"Unexpected error in tool '{name}': {exc}", level="ERROR")
            err_dict = {"error": str(exc), "exit_code": 1, "is_error": True}
            return {
                "content": [{"type": "text", "text": json.dumps(err_dict)}],
                "isError": True,
            }

    # -----------------------------------------------------------------------
    # Handler Implementations
    # -----------------------------------------------------------------------
    def _handle_create_sandbox(self, params: CreateSandboxInput) -> Dict[str, Any]:
        """Provisions a new sandbox via SandboxManager."""
        mode_str = (params.mode or "auto").lower()
        if mode_str in ("local", "local_fallback"):
            mode_enum = SandboxMode.LOCAL
        elif mode_str == "e2b":
            mode_enum = SandboxMode.E2B
        else:
            mode_enum = SandboxMode.AUTO

        sb: BaseSandbox = self.sandbox_manager.create_sandbox(
            mode=mode_enum,
            timeout=params.effective_timeout,
            env=params.effective_env if params.effective_env else None,
            authorized_imports=params.authorized_imports,
            template=params.template,
        )

        return {
            "sandbox_id": sb.sandbox_id,
            "id": sb.sandbox_id,
            "mode": sb.mode.value if hasattr(sb.mode, "value") else str(sb.mode),
            "status": sb.status.value if hasattr(sb.status, "value") else str(sb.status),
            "created_at": time.time(),
            "template": params.template or "python-3.11",
            "timeout": params.effective_timeout,
        }

    def _handle_execute_code(self, params: ExecuteCodeInput) -> Dict[str, Any]:
        """Executes code in the specified sandbox."""
        sb: BaseSandbox = self._get_or_create_sandbox(params.sandbox_id, timeout=params.effective_timeout)

        res: ExecutionResult = sb.execute(
            code=params.code,
            language=params.language or "python",
            timeout=params.effective_timeout,
            repl=params.effective_repl,
        )

        return {
            "stdout": res.stdout,
            "stderr": res.stderr,
            "exit_code": res.exit_code,
            "artifacts": res.artifacts,
            "duration_ms": res.duration_ms,
            "error": res.error,
            "state": res.state,
            "success": res.is_success,
            "result": res.result,
        }

    def _handle_pause_sandbox(self, params: PauseSandboxInput) -> Dict[str, Any]:
        """Freezes sandbox state."""
        sb: BaseSandbox = self._get_or_create_sandbox(params.sandbox_id)

        snapshot_id = None
        if params.auto_snapshot:
            snapshot_id = sb.create_snapshot("pre_pause_snapshot")

        sb.pause()

        return {
            "sandbox_id": sb.sandbox_id,
            "status": sb.status.value if hasattr(sb.status, "value") else str(sb.status),
            "message": "Sandbox successfully paused.",
            "snapshot_id": snapshot_id,
        }

    def _handle_resume_sandbox(self, params: ResumeSandboxInput) -> Dict[str, Any]:
        """Resumes a paused sandbox."""
        sb: BaseSandbox = self._get_or_create_sandbox(params.sandbox_id, timeout=params.effective_timeout)

        sb.resume()

        return {
            "sandbox_id": sb.sandbox_id,
            "status": sb.status.value if hasattr(sb.status, "value") else str(sb.status),
            "message": "Sandbox successfully resumed.",
            "timeout": params.effective_timeout,
        }

    def _handle_destroy_sandbox(self, params: DestroySandboxInput) -> Dict[str, Any]:
        """Terminates and purges the sandbox."""
        destroyed = self.sandbox_manager.destroy_sandbox(params.sandbox_id)
        return {
            "sandbox_id": params.sandbox_id,
            "destroyed": destroyed,
            "status": "destroyed" if destroyed else "not_found",
        }

    def _handle_manage_snapshot(self, params: ManageSnapshotInput) -> Dict[str, Any]:
        """Performs snapshot management actions."""
        action = params.action.lower()

        if action == "create":
            if not params.sandbox_id:
                raise InvalidParamsError("sandbox_id is required for create snapshot.")
            sb = self._get_or_create_sandbox(params.sandbox_id)

            snap_name = params.effective_name
            snap_id = sb.create_snapshot(snap_name)
            return {
                "action": "create",
                "snapshot_id": snap_id,
                "sandbox_id": sb.sandbox_id,
                "name": snap_name,
                "status": "created",
            }

        elif action == "restore":
            if not params.sandbox_id:
                raise InvalidParamsError("sandbox_id is required for restore snapshot.")
            if not params.snapshot_id:
                raise InvalidParamsError("snapshot_id is required for restore snapshot.")
            sb = self._get_or_create_sandbox(params.sandbox_id)

            sb.restore_snapshot(params.snapshot_id)
            return {
                "action": "restore",
                "snapshot_id": params.snapshot_id,
                "sandbox_id": sb.sandbox_id,
                "status": "restored",
            }

        elif action == "list":
            snapshots_list = []
            if params.sandbox_id:
                sb = self._get_or_create_sandbox(params.sandbox_id)
                snapshots_list = sb.list_snapshots()
            return {
                "action": "list",
                "sandbox_id": params.sandbox_id,
                "snapshots": snapshots_list,
            }

        elif action == "delete":
            if not params.snapshot_id:
                raise InvalidParamsError("snapshot_id is required for delete snapshot.")
            deleted = False
            if params.sandbox_id:
                sb = self._get_or_create_sandbox(params.sandbox_id)
                deleted = sb.delete_snapshot(params.snapshot_id)
            return {
                "action": "delete",
                "snapshot_id": params.snapshot_id,
                "deleted": deleted,
                "status": "deleted" if deleted else "not_found",
            }

        else:
            raise InvalidParamsError(f"Unsupported snapshot action: '{action}'")

    def _handle_spawn_worker(self, params: SpawnWorkerInput) -> Dict[str, Any]:
        """Registers a scheduled background task in ServiceWorkerDaemon."""
        trig_type_str = params.trigger_type.lower()
        if trig_type_str == "cron":
            trig_type_enum = TaskTriggerType.CRON
        else:
            trig_type_enum = TaskTriggerType.TIMER

        task_id = f"task-{uuid.uuid4().hex[:8]}"
        task = ScheduledTask(
            task_id=task_id,
            name=params.effective_name,
            trigger_type=trig_type_enum,
            trigger_spec=params.trigger_spec,
            code=params.code,
            sandbox_id=params.sandbox_id,
            max_runs=params.effective_max_runs,
            timeout=params.effective_timeout,
        )

        registered_id = self.scheduler_daemon.register_task(task)
        return {
            "task_id": registered_id,
            "name": task.name,
            "status": task.status.value if hasattr(task.status, "value") else str(task.status),
            "trigger_type": params.trigger_type,
            "trigger_spec": params.trigger_spec,
            "sandbox_id": params.sandbox_id,
        }

    # -----------------------------------------------------------------------
    # Extended Handler Implementations (6 New Tools - M7 / R4)
    # -----------------------------------------------------------------------
    def _handle_load_model(self, params: LoadModelInput) -> Dict[str, Any]:
        """Loads a local open-weight model into memory."""
        runner = self._get_model_runner()
        model_id = params.effective_model_id
        model_path = params.effective_model_path

        fmt_str = (params.model_format or "auto").lower()
        if fmt_str in ("nemotron", "nemo"):
            backend_enum = ModelBackend.NEMOTRON if ModelBackend else "nemotron"
        elif fmt_str == "transformers":
            backend_enum = ModelBackend.TRANSFORMERS if ModelBackend else "transformers"
        elif fmt_str == "onnx":
            backend_enum = ModelBackend.ONNX if ModelBackend else "onnx"
        elif fmt_str in ("lightweight", "gguf"):
            backend_enum = ModelBackend.LIGHTWEIGHT if ModelBackend else "lightweight"
        else:
            backend_enum = ModelBackend.AUTO if ModelBackend else "auto"

        config = ModelConfig(
            model_id=model_id,
            model_path=model_path,
            backend=backend_enum,
            device=params.effective_device,
            precision=params.effective_precision,
            max_context_length=params.max_seq_length or 4096,
            trust_remote_code=params.trust_remote_code or False,
            extra_params={"offload_folder": params.offload_folder} if params.offload_folder else {},
        )

        try:
            engine = runner.load_model(config)
        except FileNotFoundError as fnf:
            raise ModelNotFoundError(f"Model path not found: {fnf}") from fnf
        except Exception as exc:
            raise ModelLoadError(f"Failed to load model '{model_id}': {exc}") from exc

        info = engine.model_info() if hasattr(engine, "model_info") else None
        return {
            "model_id": model_id,
            "model_path": model_path,
            "backend": backend_enum.value if hasattr(backend_enum, "value") else str(backend_enum),
            "device": params.effective_device,
            "precision": params.effective_precision,
            "status": "loaded",
            "parameter_count": info.parameter_count if info else getattr(engine, "parameter_count", 0),
            "max_seq_length": params.max_seq_length or 4096,
        }

    def _handle_model_generate(self, params: ModelGenerateInput) -> Dict[str, Any]:
        """Generates text from a loaded model."""
        runner = self._get_model_runner()
        gen_cfg = GenerationConfig(
            max_new_tokens=params.effective_max_new_tokens,
            temperature=params.temperature if params.temperature is not None else 0.7,
            top_p=params.top_p if params.top_p is not None else 0.9,
            top_k=params.top_k if params.top_k is not None else 50,
            repetition_penalty=params.repetition_penalty if params.repetition_penalty is not None else 1.1,
            stop_sequences=params.effective_stop_sequences,
        )
        try:
            res: GenerationResult = runner.generate(
                params.model_id,
                params.prompt,
                config=gen_cfg,
            )
        except Exception as exc:
            raise ModelInferenceError(f"Inference error with model '{params.model_id}': {exc}") from exc

        return {
            "model_id": params.model_id,
            "text": res.text,
            "prompt": params.prompt,
            "tokens_generated": res.tokens_generated,
            "prompt_tokens": res.prompt_tokens,
            "finish_reason": res.finish_reason,
            "duration_ms": res.duration_ms,
            "metadata": res.metadata,
        }

    def _handle_model_chat(self, params: ModelChatInput) -> Dict[str, Any]:
        """Performs multi-turn chat completion using chat templates."""
        runner = self._get_model_runner()
        messages_list: List[Any] = []
        if params.system_prompt and not any(m.role == "system" for m in params.messages):
            messages_list.append(ChatMessage(role="system", content=params.system_prompt) if ChatMessage else {"role": "system", "content": params.system_prompt})
        for m in params.messages:
            messages_list.append(ChatMessage(role=m.role, content=m.content) if ChatMessage else {"role": m.role, "content": m.content})

        gen_cfg = GenerationConfig(
            max_new_tokens=params.effective_max_new_tokens,
            temperature=params.temperature if params.temperature is not None else 0.7,
            top_p=params.top_p if params.top_p is not None else 0.9,
            top_k=params.top_k if params.top_k is not None else 50,
            repetition_penalty=params.repetition_penalty if params.repetition_penalty is not None else 1.1,
            stop_sequences=params.effective_stop_sequences,
        )

        try:
            res: GenerationResult = runner.chat(
                params.model_id,
                messages_list,
                config=gen_cfg,
            )
        except Exception as exc:
            raise ModelInferenceError(f"Chat completion error with model '{params.model_id}': {exc}") from exc

        return {
            "model_id": params.model_id,
            "message": {
                "role": "assistant",
                "content": res.text,
            },
            "text": res.text,
            "tokens_generated": res.tokens_generated,
            "prompt_tokens": res.prompt_tokens,
            "finish_reason": res.finish_reason,
            "duration_ms": res.duration_ms,
            "metadata": res.metadata,
        }

    def _handle_persist_sandbox(self, params: PersistSandboxInput) -> Dict[str, Any]:
        """Serializes a sandbox session, variables, and snapshots to SQLite/disk."""
        pm = self._get_persistence_manager(params.effective_storage_path)
        sb = self.sandbox_manager.get_sandbox(params.sandbox_id)
        if sb is None:
            raise SandboxNotFoundError(f"Sandbox '{params.sandbox_id}' not found.")

        variables: Dict[str, Any] = {}
        if params.include_variables:
            if hasattr(sb, "export_state"):
                try:
                    variables = sb.export_state()
                except Exception as e:
                    logger.warning("Failed exporting state from sandbox %s: %s", params.sandbox_id, e)
            elif hasattr(sb, "get_variables"):
                variables = sb.get_variables()

        meta = {
            "name": params.effective_name,
            "description": params.description or "",
        }

        try:
            record = pm.save_sandbox(
                sandbox_or_id=sb,
                variables=variables if params.include_variables else {},
                metadata=meta,
            )
        except Exception as exc:
            raise PersistenceWriteError(f"Failed to persist sandbox '{params.sandbox_id}': {exc}") from exc

        return {
            "sandbox_id": params.sandbox_id,
            "persisted_id": record.sandbox_id,
            "name": params.effective_name,
            "status": "persisted",
            "variable_count": record.variable_count,
            "created_at": record.created_at,
            "updated_at": record.updated_at,
            "storage_path": params.effective_storage_path,
        }

    def _handle_restore_sandbox_disk(self, params: RestoreSandboxDiskInput) -> Dict[str, Any]:
        """Restores a persisted sandbox session into an active sandbox environment."""
        target_id = params.effective_persisted_id or params.sandbox_id
        if not target_id:
            raise InvalidParamsError("Either persisted_id or sandbox_id must be provided to restore_sandbox_disk.")

        pm = self._get_persistence_manager(params.storage_path)
        try:
            loaded = pm.load_sandbox(target_id)
        except Exception as exc:
            raise PersistenceReadError(f"Failed to read persisted sandbox '{target_id}': {exc}") from exc

        if loaded is None:
            raise PersistenceNotFoundError(f"Persisted sandbox '{target_id}' not found in storage.")

        record, variables = loaded

        mode_str = (params.effective_mode or record.mode or "local").lower()
        if mode_str in ("local", "local_fallback"):
            mode_enum = SandboxMode.LOCAL
        elif mode_str == "e2b":
            mode_enum = SandboxMode.E2B
        else:
            mode_enum = SandboxMode.AUTO

        config_data = {}
        if isinstance(record.config_json, str):
            try:
                config_data = json.loads(record.config_json)
            except Exception:
                config_data = {}
        elif isinstance(record.config_json, dict):
            config_data = record.config_json

        env = config_data.get("env", {})
        timeout = float(config_data.get("timeout", 300.0))
        authorized_imports = config_data.get("authorized_imports", None)

        sb = self.sandbox_manager.create_sandbox(
            mode=mode_enum,
            timeout=timeout,
            env=env,
            authorized_imports=authorized_imports,
        )

        if params.restore_variables and variables:
            if hasattr(sb, "hydrate_state"):
                sb.hydrate_state(variables)
            elif hasattr(sb, "_repl_state"):
                sb._repl_state.update(variables)

        return {
            "sandbox_id": sb.sandbox_id,
            "restored_from": target_id,
            "mode": sb.mode.value if hasattr(sb.mode, "value") else str(sb.mode),
            "status": sb.status.value if hasattr(sb.status, "value") else str(sb.status),
            "variable_count": len(variables) if (params.restore_variables and variables) else 0,
        }

    def _handle_list_persisted_sandboxes(self, params: ListPersistedSandboxesInput) -> Dict[str, Any]:
        """Lists persisted sandbox sessions and snapshot catalog."""
        pm = self._get_persistence_manager(params.storage_path)
        try:
            records = pm.list_persisted_sandboxes()
        except Exception as exc:
            raise PersistenceReadError(f"Failed to list persisted sandboxes: {exc}") from exc

        if params.effective_filter_name:
            fn = params.effective_filter_name.lower()
            records = [
                r for r in records
                if (fn in r.sandbox_id.lower())
                or (r.metadata and fn in str(r.metadata.get("name", "")).lower())
                or (r.metadata and fn in str(r.metadata.get("description", "")).lower())
            ]

        total_count = len(records)
        offset = params.offset or 0
        limit = params.limit or 50
        paginated = records[offset : offset + limit]

        sandboxes_list = []
        for r in paginated:
            sandboxes_list.append({
                "sandbox_id": r.sandbox_id,
                "mode": r.mode,
                "status": r.status,
                "created_at": r.created_at,
                "updated_at": r.updated_at,
                "variable_count": r.variable_count,
                "metadata": r.metadata,
            })

        return {
            "total_count": total_count,
            "offset": offset,
            "limit": limit,
            "sandboxes": sandboxes_list,
        }
