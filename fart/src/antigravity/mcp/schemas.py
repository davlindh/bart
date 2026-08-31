"""
Pydantic Models and Tool Schemas for Model Context Protocol (MCP) Server.

Defines schemas for MCP handshake, tool discovery (tools/list), tool calls
(tools/call), and arguments validation for all 7 lifecycle and worker tools.
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Core MCP Protocol Schemas
# ---------------------------------------------------------------------------
class ClientInfo(BaseModel):
    """Metadata describing the connecting client."""
    name: str = "antigravity-client"
    version: Optional[str] = "1.0.0"

    model_config = ConfigDict(extra="ignore")


class ServerInfo(BaseModel):
    """Metadata describing the MCP server."""
    name: str = "antigravity-sandbox-mcp"
    version: str = "1.0.0"


class ServerCapabilities(BaseModel):
    """Supported MCP server capabilities."""
    tools: Dict[str, Any] = Field(default_factory=lambda: {"listChanged": True})
    logging: Dict[str, Any] = Field(default_factory=dict)
    resources: Optional[Dict[str, Any]] = Field(default_factory=lambda: {"subscribe": True, "listChanged": True})

    model_config = ConfigDict(extra="allow")


class InitializeParams(BaseModel):
    """Parameters sent in an MCP initialize request."""
    protocolVersion: str = "2024-11-05"
    capabilities: Optional[Dict[str, Any]] = Field(default_factory=dict)
    clientInfo: Optional[ClientInfo] = None

    model_config = ConfigDict(extra="ignore")


class InitializeResult(BaseModel):
    """Result returned in response to an MCP initialize request."""
    protocolVersion: str = "2024-11-05"
    capabilities: ServerCapabilities = Field(default_factory=ServerCapabilities)
    serverInfo: ServerInfo = Field(default_factory=ServerInfo)


class TextContent(BaseModel):
    """MCP Text Content payload."""
    type: Literal["text"] = "text"
    text: str


class ImageContent(BaseModel):
    """MCP Image Content payload (e.g. charts)."""
    type: Literal["image"] = "image"
    data: str
    mimeType: str = "image/png"


class EmbeddedResource(BaseModel):
    """MCP Embedded Resource payload."""
    type: Literal["resource"] = "resource"
    resource: Dict[str, Any]


class ToolDefinition(BaseModel):
    """Declaration of an exposed MCP tool."""
    name: str
    description: str
    inputSchema: Dict[str, Any]


class ToolsListResult(BaseModel):
    """List of all available tools returned by tools/list."""
    tools: List[ToolDefinition]


class ToolCallParams(BaseModel):
    """Parameters received in a tools/call request."""
    name: str
    arguments: Optional[Dict[str, Any]] = Field(default_factory=dict)

    model_config = ConfigDict(extra="ignore")


class ToolCallResult(BaseModel):
    """Result returned for a tools/call request."""
    content: List[Union[TextContent, ImageContent, EmbeddedResource, Dict[str, Any]]]
    isError: Optional[bool] = False

    model_config = ConfigDict(extra="allow")


# ---------------------------------------------------------------------------
# Tool Argument Schemas (7 MCP Tools)
# ---------------------------------------------------------------------------
class CreateSandboxInput(BaseModel):
    """Arguments for `create_sandbox` tool."""
    mode: Optional[str] = Field("auto", description="Sandbox backend: 'auto', 'e2b', or 'local'.")
    template: Optional[str] = Field("python-3.11", description="Execution template.")
    timeout: Optional[float] = Field(300.0, description="Lifetime timeout in seconds.")
    timeout_seconds: Optional[float] = Field(None, description="Alias for timeout.")
    env: Optional[Dict[str, str]] = Field(None, description="Environment variables.")
    env_vars: Optional[Dict[str, str]] = Field(None, description="Alias for env.")
    authorized_imports: Optional[List[str]] = Field(None, description="Allowed import modules.")
    memory_limit_mb: Optional[int] = Field(512, description="Memory limit in MB.")

    model_config = ConfigDict(extra="ignore")

    @property
    def effective_timeout(self) -> float:
        if self.timeout_seconds is not None:
            return float(self.timeout_seconds)
        return float(self.timeout if self.timeout is not None else 300.0)

    @property
    def effective_env(self) -> Dict[str, str]:
        if self.env_vars is not None:
            return dict(self.env_vars)
        if self.env is not None:
            return dict(self.env)
        return {}


class ExecuteCodeInput(BaseModel):
    """Arguments for `execute_code` tool."""
    sandbox_id: str = Field(..., description="ID of the target sandbox.")
    code: str = Field(..., description="Python or shell code block to execute.")
    language: Optional[str] = Field("python", description="Programming language (default 'python').")
    timeout: Optional[float] = Field(60.0, description="Execution timeout in seconds.")
    timeout_seconds: Optional[float] = Field(None, description="Alias for timeout.")
    repl: Optional[bool] = Field(True, description="Whether to execute in persistent REPL mode.")
    repl_mode: Optional[bool] = Field(None, description="Alias for repl.")
    stream_output: Optional[bool] = Field(False, description="Whether to emit live progress.")

    model_config = ConfigDict(extra="ignore")

    @property
    def effective_timeout(self) -> float:
        if self.timeout_seconds is not None:
            return float(self.timeout_seconds)
        return float(self.timeout if self.timeout is not None else 60.0)

    @property
    def effective_repl(self) -> bool:
        if self.repl_mode is not None:
            return bool(self.repl_mode)
        return bool(self.repl if self.repl is not None else True)


class PauseSandboxInput(BaseModel):
    """Arguments for `pause_sandbox` tool."""
    sandbox_id: str = Field(..., description="ID of the sandbox to pause.")
    auto_snapshot: Optional[bool] = Field(True, description="Create snapshot before pausing.")

    model_config = ConfigDict(extra="ignore")


class ResumeSandboxInput(BaseModel):
    """Arguments for `resume_sandbox` tool."""
    sandbox_id: str = Field(..., description="ID of the sandbox to resume.")
    timeout: Optional[float] = Field(300.0, description="New inactivity timeout in seconds.")
    timeout_seconds: Optional[float] = Field(None, description="Alias for timeout.")

    model_config = ConfigDict(extra="ignore")

    @property
    def effective_timeout(self) -> float:
        if self.timeout_seconds is not None:
            return float(self.timeout_seconds)
        return float(self.timeout if self.timeout is not None else 300.0)


class DestroySandboxInput(BaseModel):
    """Arguments for `destroy_sandbox` tool."""
    sandbox_id: str = Field(..., description="ID of the sandbox to destroy.")
    force: Optional[bool] = Field(True, description="Force termination of active processes.")

    model_config = ConfigDict(extra="ignore")


class ManageSnapshotInput(BaseModel):
    """Arguments for `manage_snapshot` tool."""
    action: Literal["create", "restore", "list", "delete"] = Field(
        ..., description="Action: 'create', 'restore', 'list', 'delete'."
    )
    sandbox_id: Optional[str] = Field(None, description="ID of the sandbox.")
    snapshot_id: Optional[str] = Field(None, description="ID of the snapshot.")
    name: Optional[str] = Field(None, description="Name for the new snapshot.")
    snapshot_name: Optional[str] = Field(None, description="Alias for name.")
    description: Optional[str] = Field(None, description="Optional snapshot description.")

    model_config = ConfigDict(extra="ignore")

    @property
    def effective_name(self) -> str:
        if self.snapshot_name:
            return str(self.snapshot_name)
        if self.name:
            return str(self.name)
        return f"snap-{int(time.time() * 1000)}"


class SpawnWorkerInput(BaseModel):
    """Arguments for `spawn_worker` tool."""
    name: Optional[str] = Field(None, description="Descriptive name of the worker task.")
    task_name: Optional[str] = Field(None, description="Alias for name.")
    trigger_type: str = Field(..., description="Trigger type: 'cron', 'timer', or 'immediate'.")
    trigger_spec: str = Field(..., description="Cron expression (e.g. '*/5 * * * *') or seconds ('10.0').")
    code: str = Field(..., description="Executable Python code payload.")
    sandbox_id: Optional[str] = Field(None, description="Optional persistent sandbox ID.")
    timeout: Optional[float] = Field(60.0, description="Task timeout in seconds.")
    timeout_seconds: Optional[float] = Field(None, description="Alias for timeout.")
    max_runs: Optional[int] = Field(None, description="Maximum iterations for cron tasks.")
    max_iterations: Optional[int] = Field(None, description="Alias for max_runs.")
    sandbox_template: Optional[str] = Field("python-3.11", description="Sandbox template.")
    env: Optional[Dict[str, str]] = Field(None, description="Environment variables.")
    env_vars: Optional[Dict[str, str]] = Field(None, description="Alias for env.")

    model_config = ConfigDict(extra="ignore")

    @property
    def effective_name(self) -> str:
        if self.task_name:
            return str(self.task_name)
        if self.name:
            return str(self.name)
        return f"worker-{int(time.time() * 1000)}"

    @property
    def effective_timeout(self) -> float:
        if self.timeout_seconds is not None:
            return float(self.timeout_seconds)
        return float(self.timeout if self.timeout is not None else 60.0)

    @property
    def effective_max_runs(self) -> Optional[int]:
        if self.max_iterations is not None:
            return int(self.max_iterations)
        if self.max_runs is not None:
            return int(self.max_runs)
        return None

    @property
    def effective_env(self) -> Dict[str, str]:
        if self.env_vars is not None:
            return dict(self.env_vars)
        if self.env is not None:
            return dict(self.env)
        return {}


# ---------------------------------------------------------------------------
# Extended Tool Argument Schemas (6 New Tools - M7 / R4)
# ---------------------------------------------------------------------------
class LoadModelInput(BaseModel):
    """Arguments for `load_model` tool."""
    model_path: str = Field(..., description="Path to model weights directory, GGUF/ONNX file, or HF repo ID.")
    model_id: Optional[str] = Field(None, description="Unique alias/identifier for this loaded model instance.")
    model_format: Optional[Literal["transformers", "nemotron", "nemo", "gguf", "onnx", "auto"]] = Field(
        "auto", description="Model architecture/engine backend."
    )
    device: Optional[Literal["cpu", "cuda", "cuda:0", "auto", "mps"]] = Field(
        "auto", description="Target hardware compute device."
    )
    precision: Optional[Literal["fp16", "bf16", "fp32", "int8", "int4", "auto"]] = Field(
        "auto", description="Weight precision / quantization."
    )
    max_seq_length: Optional[int] = Field(4096, description="Maximum context sequence length in tokens.")
    trust_remote_code: Optional[bool] = Field(False, description="Allow custom modeling code execution.")
    offload_folder: Optional[str] = Field(None, description="Directory for disk offloading if memory constrained.")

    # Aliases
    path: Optional[str] = Field(None, description="Alias for model_path.")
    device_map: Optional[str] = Field(None, description="Alias for device.")
    dtype: Optional[str] = Field(None, description="Alias for precision.")

    model_config = ConfigDict(extra="ignore")

    @property
    def effective_model_path(self) -> str:
        return self.path if self.path is not None else self.model_path

    @property
    def effective_device(self) -> str:
        return self.device_map if self.device_map is not None else (self.device or "auto")

    @property
    def effective_precision(self) -> str:
        return self.dtype if self.dtype is not None else (self.precision or "auto")

    @property
    def effective_model_id(self) -> str:
        if self.model_id:
            return self.model_id
        clean_name = self.effective_model_path.replace("\\", "/").rstrip("/").split("/")[-1]
        return f"{clean_name}-{int(time.time())}"


class ModelGenerateInput(BaseModel):
    """Arguments for `model_generate` tool."""
    model_id: str = Field(..., description="Identifier of the loaded model instance.")
    prompt: str = Field(..., description="Input prompt text string.")
    max_new_tokens: Optional[int] = Field(256, ge=1, le=8192, description="Maximum tokens to generate.")
    temperature: Optional[float] = Field(0.7, ge=0.0, le=2.0, description="Sampling temperature.")
    top_p: Optional[float] = Field(0.9, ge=0.0, le=1.0, description="Nucleus sampling probability.")
    top_k: Optional[int] = Field(50, ge=0, description="Top-k filtering threshold.")
    repetition_penalty: Optional[float] = Field(1.1, ge=1.0, le=2.0, description="Repetition penalty factor.")
    stop_sequences: Optional[List[str]] = Field(default_factory=list, description="Sequences that halt generation.")
    stream: Optional[bool] = Field(False, description="Whether to stream tokens via JSON-RPC notifications.")

    # Aliases
    max_tokens: Optional[int] = Field(None, description="Alias for max_new_tokens.")
    stop: Optional[List[str]] = Field(None, description="Alias for stop_sequences.")

    model_config = ConfigDict(extra="ignore")

    @property
    def effective_max_new_tokens(self) -> int:
        if self.max_tokens is not None:
            return self.max_tokens
        return self.max_new_tokens if self.max_new_tokens is not None else 256

    @property
    def effective_stop_sequences(self) -> List[str]:
        if self.stop is not None:
            return self.stop
        return self.stop_sequences or []


class ChatMessageItem(BaseModel):
    """Structured role message for chat completions."""
    role: Literal["system", "user", "assistant"] = Field(..., description="Message role.")
    content: str = Field(..., description="Text content of the message.")

    model_config = ConfigDict(extra="allow")


class ModelChatInput(BaseModel):
    """Arguments for `model_chat` tool."""
    model_id: str = Field(..., description="Identifier of the loaded model instance.")
    messages: List[ChatMessageItem] = Field(..., min_length=1, description="Ordered conversation turns.")
    chat_template: Optional[Literal["auto", "nemotron", "chatml", "llama3", "mistral", "custom"]] = Field(
        "auto", description="Chat template style to format message tokens."
    )
    system_prompt: Optional[str] = Field(None, description="Optional override for system instructions.")
    max_new_tokens: Optional[int] = Field(512, ge=1, le=8192, description="Maximum completion tokens.")
    temperature: Optional[float] = Field(0.7, ge=0.0, le=2.0, description="Sampling temperature.")
    top_p: Optional[float] = Field(0.9, ge=0.0, le=1.0, description="Nucleus sampling probability.")
    top_k: Optional[int] = Field(50, ge=0, description="Top-k filtering threshold.")
    repetition_penalty: Optional[float] = Field(1.1, ge=1.0, le=2.0, description="Repetition penalty factor.")
    stop_sequences: Optional[List[str]] = Field(default_factory=list, description="Stop token sequences.")

    # Aliases
    max_tokens: Optional[int] = Field(None, description="Alias for max_new_tokens.")
    stop: Optional[List[str]] = Field(None, description="Alias for stop_sequences.")

    model_config = ConfigDict(extra="ignore")

    @property
    def effective_max_new_tokens(self) -> int:
        if self.max_tokens is not None:
            return self.max_tokens
        return self.max_new_tokens if self.max_new_tokens is not None else 512

    @property
    def effective_stop_sequences(self) -> List[str]:
        if self.stop is not None:
            return self.stop
        return self.stop_sequences or []


class PersistSandboxInput(BaseModel):
    """Arguments for `persist_sandbox` tool."""
    sandbox_id: str = Field(..., description="Identifier of the active sandbox to persist.")
    storage_path: Optional[str] = Field(None, description="Custom root directory path for SQLite & asset store.")
    name: Optional[str] = Field(None, description="Human-readable alias or label for the persisted session.")
    description: Optional[str] = Field(None, description="Detailed notes describing the persisted state.")
    include_variables: Optional[bool] = Field(True, description="Whether to serialize REPL in-memory variables.")
    include_snapshots: Optional[bool] = Field(True, description="Whether to serialize existing memory snapshot vectors.")
    include_filesystem: Optional[bool] = Field(True, description="Whether to persist sandbox filesystem artifacts.")

    # Aliases
    session_name: Optional[str] = Field(None, description="Alias for name.")
    target_dir: Optional[str] = Field(None, description="Alias for storage_path.")

    model_config = ConfigDict(extra="ignore")

    @property
    def effective_name(self) -> str:
        if self.session_name:
            return self.session_name
        if self.name:
            return self.name
        return f"persisted-{self.sandbox_id}-{int(time.time())}"

    @property
    def effective_storage_path(self) -> Optional[str]:
        return self.target_dir if self.target_dir is not None else self.storage_path


class RestoreSandboxDiskInput(BaseModel):
    """Arguments for `restore_sandbox_disk` tool."""
    persisted_id: Optional[str] = Field(None, description="Persistent record ID in SQLite store.")
    sandbox_id: Optional[str] = Field(None, description="Target sandbox ID to look up if persisted_id not given.")
    storage_path: Optional[str] = Field(None, description="Custom root directory path for SQLite store.")
    target_mode: Optional[Literal["auto", "local", "e2b"]] = Field(
        "auto", description="Sandbox backend mode for the restored instance."
    )
    restore_variables: Optional[bool] = Field(True, description="Whether to rehydrate variable tables into REPL.")
    restore_snapshots: Optional[bool] = Field(True, description="Whether to restore multi-branch snapshot tree.")
    new_sandbox_id: Optional[str] = Field(None, description="Clone into a fresh sandbox ID instead of original ID.")

    # Aliases
    session_id: Optional[str] = Field(None, description="Alias for persisted_id.")
    mode: Optional[str] = Field(None, description="Alias for target_mode.")

    model_config = ConfigDict(extra="ignore")

    @property
    def effective_persisted_id(self) -> Optional[str]:
        return self.session_id if self.session_id is not None else self.persisted_id

    @property
    def effective_mode(self) -> str:
        return self.mode if self.mode is not None else (self.target_mode or "auto")


class ListPersistedSandboxesInput(BaseModel):
    """Arguments for `list_persisted_sandboxes` tool."""
    storage_path: Optional[str] = Field(None, description="Custom root directory path for SQLite store.")
    filter_name: Optional[str] = Field(None, description="Optional name substring filter.")
    limit: Optional[int] = Field(50, ge=1, le=200, description="Max number of records to return.")
    offset: Optional[int] = Field(0, ge=0, description="Pagination offset.")
    include_details: Optional[bool] = Field(False, description="Whether to include full variable manifests.")

    # Aliases
    name_filter: Optional[str] = Field(None, description="Alias for filter_name.")

    model_config = ConfigDict(extra="ignore")

    @property
    def effective_filter_name(self) -> Optional[str]:
        return self.name_filter if self.name_filter is not None else self.filter_name


# ---------------------------------------------------------------------------
# Declarative Tool Schemas for MCP Catalog (13 Tools)
# ---------------------------------------------------------------------------
TOOL_SCHEMAS: List[Dict[str, Any]] = [
    {
        "name": "create_sandbox",
        "description": "Provisions a new isolated execution sandbox with automatic E2B / Local fallback.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "template": {
                    "type": "string",
                    "description": "Template or base environment (e.g. 'python-3.11').",
                    "default": "python-3.11",
                },
                "timeout": {
                    "type": "number",
                    "description": "Inactivity lifetime timeout in seconds.",
                    "default": 300.0,
                },
                "timeout_seconds": {
                    "type": "number",
                    "description": "Inactivity lifetime timeout in seconds (alias).",
                },
                "env": {
                    "type": "object",
                    "additionalProperties": {"type": "string"},
                    "description": "Environment variables to inject.",
                },
                "env_vars": {
                    "type": "object",
                    "additionalProperties": {"type": "string"},
                    "description": "Environment variables to inject (alias).",
                },
                "mode": {
                    "type": "string",
                    "enum": ["auto", "e2b", "local", "local_fallback"],
                    "description": "Execution isolation backend.",
                    "default": "auto",
                },
                "memory_limit_mb": {
                    "type": "integer",
                    "description": "Memory limit in MB.",
                    "default": 512,
                },
            },
            "required": [],
        },
    },
    {
        "name": "execute_code",
        "description": "Executes Python code in a sandbox, supporting persistent REPL state and artifact capture.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "sandbox_id": {
                    "type": "string",
                    "description": "Identifier of the active sandbox.",
                },
                "code": {
                    "type": "string",
                    "description": "Python source code block to execute.",
                },
                "language": {
                    "type": "string",
                    "enum": ["python", "bash", "sh"],
                    "default": "python",
                    "description": "Execution interpreter language.",
                },
                "timeout": {
                    "type": "number",
                    "description": "Execution timeout in seconds.",
                    "default": 60.0,
                },
                "timeout_seconds": {
                    "type": "number",
                    "description": "Execution timeout in seconds (alias).",
                },
                "repl": {
                    "type": "boolean",
                    "description": "Whether to maintain REPL variable and function state across calls.",
                    "default": True,
                },
                "repl_mode": {
                    "type": "boolean",
                    "description": "Whether to maintain REPL state (alias).",
                },
                "stream_output": {
                    "type": "boolean",
                    "description": "If true, emits live progress notifications.",
                    "default": False,
                },
            },
            "required": ["sandbox_id", "code"],
        },
    },
    {
        "name": "pause_sandbox",
        "description": "Freezes sandbox execution state to conserve resources while retaining session memory.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "sandbox_id": {
                    "type": "string",
                    "description": "Identifier of the sandbox to pause.",
                },
                "auto_snapshot": {
                    "type": "boolean",
                    "description": "Whether to take a state snapshot before pausing.",
                    "default": True,
                },
            },
            "required": ["sandbox_id"],
        },
    },
    {
        "name": "resume_sandbox",
        "description": "Resumes a paused sandbox without losing REPL state.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "sandbox_id": {
                    "type": "string",
                    "description": "Identifier of the paused sandbox to resume.",
                },
                "timeout": {
                    "type": "number",
                    "description": "New inactivity timeout in seconds.",
                    "default": 300.0,
                },
            },
            "required": ["sandbox_id"],
        },
    },
    {
        "name": "destroy_sandbox",
        "description": "Terminates the sandbox, killing associated processes and purging temporary assets.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "sandbox_id": {
                    "type": "string",
                    "description": "Identifier of the sandbox to destroy.",
                },
                "force": {
                    "type": "boolean",
                    "description": "Force kill if a command is currently executing.",
                    "default": True,
                },
            },
            "required": ["sandbox_id"],
        },
    },
    {
        "name": "manage_snapshot",
        "description": "Manages sandbox state snapshots (create, restore, list, delete) for checkpointing and branching.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["create", "restore", "list", "delete"],
                    "description": "Snapshot action to perform.",
                },
                "sandbox_id": {
                    "type": "string",
                    "description": "Identifier of the sandbox.",
                },
                "snapshot_id": {
                    "type": "string",
                    "description": "Snapshot ID for restore or delete actions.",
                },
                "name": {
                    "type": "string",
                    "description": "Human-readable label for snapshot (for create action).",
                },
                "snapshot_name": {
                    "type": "string",
                    "description": "Alias for name.",
                },
                "description": {
                    "type": "string",
                    "description": "Optional snapshot description.",
                },
            },
            "required": ["action"],
        },
    },
    {
        "name": "spawn_worker",
        "description": "Registers a scheduled background service worker task (cron or timer) executing in an isolated sandbox.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Descriptive task name.",
                },
                "task_name": {
                    "type": "string",
                    "description": "Alias for name.",
                },
                "trigger_type": {
                    "type": "string",
                    "enum": ["cron", "timer", "immediate"],
                    "description": "Trigger modality: 'cron', 'timer', or 'immediate'.",
                },
                "trigger_spec": {
                    "type": "string",
                    "description": "5-field cron expression (e.g. '*/5 * * * *') or seconds interval ('10.0').",
                },
                "code": {
                    "type": "string",
                    "description": "Executable Python code payload.",
                },
                "sandbox_id": {
                    "type": "string",
                    "description": "Optional existing sandbox ID to attach to.",
                },
                "timeout": {
                    "type": "number",
                    "description": "Max runtime allowed per execution run in seconds.",
                    "default": 60.0,
                },
                "max_runs": {
                    "type": "integer",
                    "description": "Max iterations for recurring jobs before auto-terminating.",
                },
                "sandbox_template": {
                    "type": "string",
                    "description": "Sandbox template to provision for worker.",
                    "default": "python-3.11",
                },
            },
            "required": ["trigger_type", "trigger_spec", "code"],
        },
    },
    {
        "name": "load_model",
        "description": "Loads an open-weight local language model or checkpoint (NVIDIA Nemotron, Transformers, GGUF, ONNX) into memory with configurable precision and device placement.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "model_path": {
                    "type": "string",
                    "description": "Local filesystem path or HuggingFace identifier for model weights.",
                },
                "model_id": {
                    "type": "string",
                    "description": "Unique identifier assigned to the loaded model instance.",
                },
                "model_format": {
                    "type": "string",
                    "enum": ["transformers", "nemotron", "nemo", "gguf", "onnx", "auto"],
                    "default": "auto",
                    "description": "Model framework/architecture format.",
                },
                "device": {
                    "type": "string",
                    "enum": ["cpu", "cuda", "cuda:0", "auto", "mps"],
                    "default": "auto",
                    "description": "Compute device placement for tensor operations.",
                },
                "precision": {
                    "type": "string",
                    "enum": ["fp16", "bf16", "fp32", "int8", "int4", "auto"],
                    "default": "auto",
                    "description": "Floating point precision or quantization mode.",
                },
                "max_seq_length": {
                    "type": "integer",
                    "default": 4096,
                    "description": "Maximum context sequence length in tokens.",
                },
                "trust_remote_code": {
                    "type": "boolean",
                    "default": False,
                    "description": "Allow loading custom modeling architectures from repository.",
                },
            },
            "required": ["model_path"],
        },
    },
    {
        "name": "model_generate",
        "description": "Performs local text generation from a loaded open-weight model with sampling controls.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "model_id": {
                    "type": "string",
                    "description": "Identifier of the active loaded model.",
                },
                "prompt": {
                    "type": "string",
                    "description": "Prompt text to complete.",
                },
                "max_new_tokens": {
                    "type": "integer",
                    "default": 256,
                    "minimum": 1,
                    "maximum": 8192,
                    "description": "Maximum number of new tokens to generate.",
                },
                "temperature": {
                    "type": "number",
                    "default": 0.7,
                    "minimum": 0.0,
                    "maximum": 2.0,
                    "description": "Sampling temperature (0.0 for deterministic greedy decoding).",
                },
                "top_p": {
                    "type": "number",
                    "default": 0.9,
                    "minimum": 0.0,
                    "maximum": 1.0,
                    "description": "Nucleus sampling cumulative probability cutoff.",
                },
                "top_k": {
                    "type": "integer",
                    "default": 50,
                    "minimum": 0,
                    "description": "Top-k sampling token filter.",
                },
                "repetition_penalty": {
                    "type": "number",
                    "default": 1.1,
                    "minimum": 1.0,
                    "maximum": 2.0,
                    "description": "Repetition penalty factor.",
                },
                "stop_sequences": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of strings that stop generation when encountered.",
                },
                "stream": {
                    "type": "boolean",
                    "default": False,
                    "description": "Whether to stream token chunks.",
                },
            },
            "required": ["model_id", "prompt"],
        },
    },
    {
        "name": "model_chat",
        "description": "Executes multi-turn conversational chat completion applying structured chat templates (Nemotron, ChatML, Llama 3).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "model_id": {
                    "type": "string",
                    "description": "Identifier of the loaded model instance.",
                },
                "messages": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "role": {"type": "string", "enum": ["system", "user", "assistant"]},
                            "content": {"type": "string"},
                        },
                        "required": ["role", "content"],
                    },
                    "description": "List of conversation messages in chronological order.",
                },
                "chat_template": {
                    "type": "string",
                    "enum": ["auto", "nemotron", "chatml", "llama3", "mistral", "custom"],
                    "default": "auto",
                    "description": "Prompt formatting template to wrap conversation tokens.",
                },
                "system_prompt": {
                    "type": "string",
                    "description": "Override system instructions if not present in messages list.",
                },
                "max_new_tokens": {
                    "type": "integer",
                    "default": 512,
                    "description": "Maximum tokens to generate for the assistant response.",
                },
                "temperature": {
                    "type": "number",
                    "default": 0.7,
                    "description": "Sampling temperature.",
                },
                "top_p": {
                    "type": "number",
                    "default": 0.9,
                    "description": "Nucleus sampling probability cutoff.",
                },
            },
            "required": ["model_id", "messages"],
        },
    },
    {
        "name": "persist_sandbox",
        "description": "Serializes sandbox REPL session, variable tables, snapshots, and filesystem state to disk (SQLite + filesystem).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "sandbox_id": {
                    "type": "string",
                    "description": "Identifier of the active sandbox to persist.",
                },
                "storage_path": {
                    "type": "string",
                    "description": "Custom directory path for the persistence SQLite database and assets.",
                },
                "name": {
                    "type": "string",
                    "description": "Descriptive name for the persisted session.",
                },
                "description": {
                    "type": "string",
                    "description": "Optional notes on the serialized execution state.",
                },
                "include_variables": {
                    "type": "boolean",
                    "default": True,
                    "description": "Whether to serialize in-memory REPL variables.",
                },
                "include_snapshots": {
                    "type": "boolean",
                    "default": True,
                    "description": "Whether to serialize existing memory snapshots.",
                },
                "include_filesystem": {
                    "type": "boolean",
                    "default": True,
                    "description": "Whether to archive sandbox filesystem artifacts.",
                },
            },
            "required": ["sandbox_id"],
        },
    },
    {
        "name": "restore_sandbox_disk",
        "description": "Restores a previously persisted sandbox session from disk back into an active sandbox execution environment.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "persisted_id": {
                    "type": "string",
                    "description": "Persistent record identifier in the disk store.",
                },
                "sandbox_id": {
                    "type": "string",
                    "description": "Target sandbox ID to locate in the persistent store.",
                },
                "storage_path": {
                    "type": "string",
                    "description": "Custom directory path for the persistence SQLite database.",
                },
                "target_mode": {
                    "type": "string",
                    "enum": ["auto", "local", "e2b"],
                    "default": "auto",
                    "description": "Target execution engine backend.",
                },
                "restore_variables": {
                    "type": "boolean",
                    "default": True,
                    "description": "Whether to inject saved variables into the REPL namespace.",
                },
                "restore_snapshots": {
                    "type": "boolean",
                    "default": True,
                    "description": "Whether to restore memory snapshot checkpoints.",
                },
                "new_sandbox_id": {
                    "type": "string",
                    "description": "Optional new ID to assign to the restored sandbox instance (cloning).",
                },
            },
            "required": [],
        },
    },
    {
        "name": "list_persisted_sandboxes",
        "description": "Lists all sandbox sessions and state snapshots currently stored in the SQLite persistence engine.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "storage_path": {
                    "type": "string",
                    "description": "Custom directory path for the persistence SQLite database.",
                },
                "filter_name": {
                    "type": "string",
                    "description": "Filter sessions matching name substring.",
                },
                "limit": {
                    "type": "integer",
                    "default": 50,
                    "minimum": 1,
                    "maximum": 200,
                    "description": "Pagination record limit.",
                },
                "offset": {
                    "type": "integer",
                    "default": 0,
                    "minimum": 0,
                    "description": "Pagination offset.",
                },
                "include_details": {
                    "type": "boolean",
                    "default": False,
                    "description": "Whether to include variable metadata details.",
                },
            },
            "required": [],
        },
    },
]
