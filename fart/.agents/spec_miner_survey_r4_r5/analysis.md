# Specification Mining Report: Requirements R4 & R5
## Antigravity MCP Tools & Skill Suite and Comprehensive Verification & Test Suite

**Author**: Spec Miner 3 (R4 & R5)  
**Date**: 2026-08-29  
**Status**: Complete  
**Scope**: 
- **Requirement R4**: Antigravity MCP Tools & Progressive Disclosure Skill Suite
- **Requirement R5**: Comprehensive Verification & Test Suite Expansion (Tiers 1–5) and End-to-End Demo Script (`demo.py`)

---

## 1. Executive Summary & Specification Sources

This report provides the authoritative specification, interface schemas, parameter validations, progressive disclosure skill hierarchies, test matrix, and end-to-end verification workflows for Requirements R4 and R5 as defined in `ORIGINAL_REQUEST.md`.

### Authoritative Sources Examined
1. `ORIGINAL_REQUEST.md`: Requirements R1–R5 and Acceptance Criteria.
2. `PROJECT.md`: System Architecture, Interfaces, Code Layout, and Milestones.
3. `src/antigravity/mcp/`: Existing JSON-RPC 2.0 stdio protocol (`protocol.py`), schemas (`schemas.py`), tool registry (`tools.py`), and server loop (`server.py`).
4. `plugins/antigravity-sandbox-plugin/`: Plugin manifest (`plugin.json`), MCP configuration (`mcp_config.json`), Agent Directives (`rules/AGENTS.md`), and existing skills (`sandbox-execution`, `worker-orchestration`, `snapshot-management`).
5. `tests/`: 153 existing automated tests spanning Tiers 1–5, test client harnesses (`tests/conftest.py`).
6. `demo.py`: Existing end-to-end sandbox and scheduler verification script.

---

## 2. Features Discovered Table

| # | Category | Feature | Description | Inputs | Outputs | Error Behavior | Discovered Via |
|---|----------|---------|-------------|--------|---------|----------------|----------------|
| 1 | MCP Tool | `load_model` | Loads a local open-weight model / checkpoint (Nemotron, Transformers, GGUF, ONNX) into memory with configurable precision and device placement | `model_path`, `model_id`, `model_format`, `device`, `precision`, `max_seq_length`, `trust_remote_code`, `offload_folder` | Model status, metadata, parameter count, allocated memory | Returns `isError: true` on missing weights, unsupported format, or CUDA OOM | `ORIGINAL_REQUEST.md` R2, R4; `src/antigravity/models/` |
| 2 | MCP Tool | `model_generate` | Performs local token generation and completion from a loaded model with sampling hyperparameters | `model_id`, `prompt`, `max_new_tokens`, `temperature`, `top_p`, `top_k`, `repetition_penalty`, `stop_sequences`, `stream` | Generated text, token counts, latency ms, finish reason | Returns `isError: true` if model not loaded or context window exceeded | `ORIGINAL_REQUEST.md` R2, R4; `src/antigravity/models/` |
| 3 | MCP Tool | `model_chat` | Multi-turn conversational chat completion applying model-specific chat templates (Nemotron, ChatML, Llama 3) | `model_id`, `messages`, `chat_template`, `system_prompt`, `max_new_tokens`, `temperature`, `top_p`, `top_k` | Assistant message object, token breakdown, latency | Returns `isError: true` on invalid message schema or empty role | `ORIGINAL_REQUEST.md` R2, R4; `src/antigravity/models/` |
| 4 | MCP Tool | `persist_sandbox` | Serializes sandbox REPL session, memory variables, snapshots, and filesystem state to SQLite disk store | `sandbox_id`, `storage_path`, `name`, `description`, `include_variables`, `include_snapshots`, `include_filesystem` | `persisted_id`, `storage_path`, variables count, snapshots count, size in bytes | Returns `isError: true` if sandbox ID not found or SQLite write lock error | `ORIGINAL_REQUEST.md` R1, R4; `src/antigravity/storage/` |
| 5 | MCP Tool | `restore_sandbox_disk` | Restores a persisted sandbox session from disk into an active execution environment (LocalSandbox / E2B) | `persisted_id`, `sandbox_id`, `storage_path`, `target_mode`, `restore_variables`, `restore_snapshots`, `new_sandbox_id` | `sandbox_id`, `persisted_id`, restored variable counts, status | Returns `isError: true` on missing record or corrupted checkpoint | `ORIGINAL_REQUEST.md` R1, R4; `src/antigravity/storage/` |
| 6 | MCP Tool | `list_persisted_sandboxes` | Lists all persisted sandbox sessions and snapshot vectors on disk with metadata and size statistics | `storage_path`, `filter_name`, `limit`, `offset`, `include_details` | Total count, array of persisted session metadata records | Returns `isError: true` on invalid storage directory | `ORIGINAL_REQUEST.md` R1, R4; `src/antigravity/storage/` |
| 7 | MCP Protocol | Tool Catalog Expansion (13 Tools) | `tools/list` returns 13 complete tool definitions combining 7 lifecycle/worker tools and 6 inference/persistence tools | JSON-RPC `tools/list` request | Array of 13 `ToolDefinition` objects | Standard JSON-RPC error response | `PROJECT.md`, `src/antigravity/mcp/` |
| 8 | Skill Suite | `skills/local-inference` | Progressive disclosure skill instructing agents on local model loading, GPU/CPU device management, chat templating, and memory hygiene | User prompt / agent intent | Instructions, JSON tool call examples, reference docs | N/A (Guidance document) | `ORIGINAL_REQUEST.md` R4 |
| 9 | Skill Suite | `skills/disk-persistence` | Progressive disclosure skill instructing agents on SQLite disk persistence, multi-branch snapshot trees, and process recovery | User prompt / agent intent | Instructions, JSON tool call examples, reference docs | N/A (Guidance document) | `ORIGINAL_REQUEST.md` R4 |
| 10 | Customization | Manifest & Rules Updates | Updates to `plugin.json`, `mcp_config.json`, and `rules/AGENTS.md` for local inference and disk persistence directives | Environment variables, workspace rules | Validated JSON configs & Markdown rules | Lint/Schema validation | `ORIGINAL_REQUEST.md` R4 |
| 11 | Test Suite | Tiers 1–5 Test Expansion | Pytest suite expanded to cover persistence store, real local inference, extended MCP tools, multi-turn pipelines, adversarial probes | Pytest execution runner | 100% test pass with assertion logs | AssertionError / Pytest failure | `ORIGINAL_REQUEST.md` R5; `tests/` |
| 12 | Demo Script | End-to-End `demo.py` | Complete runnable verification script demonstrating persistence roundtrips, real local model loading/inference, and state recovery | CLI execution `python demo.py` | Step-by-step terminal execution log & JSON summary matrix | Exit code != 0 on failure | `ORIGINAL_REQUEST.md` R5; `demo.py` |

---

## 3. Detailed MCP Tool Specifications (JSON-RPC 2.0 & Pydantic)

### 3.1 Error Codes & Domain Protocol
In addition to standard JSON-RPC 2.0 error codes (`PARSE_ERROR`, `INVALID_REQUEST`, `METHOD_NOT_FOUND`, `INVALID_PARAMS`, `INTERNAL_ERROR`), the MCP server utilizes domain-specific error codes:

| Constant | Code | Description |
|:---|:---|:---|
| `SANDBOX_NOT_FOUND` | `-32001` | Target `sandbox_id` does not exist in memory or manager. |
| `EXECUTION_TIMEOUT` | `-32002` | Code execution exceeded allotted `timeout_seconds`. |
| `AST_SECURITY_VIOLATION` | `-32003` | Code AST contained forbidden modules, builtins, or dunders. |
| `WORKER_SCHEDULE_ERROR` | `-32004` | Invalid cron expression or worker schedule parameter. |
| `MODEL_NOT_FOUND` | `-32010` | Model weights, checkpoint path, or HF repo ID not found. |
| `MODEL_LOAD_ERROR` | `-32011` | Failed to load model weights (OOM, architecture mismatch, corrupted file). |
| `MODEL_INFERENCE_ERROR` | `-32012` | Exception during forward pass, tokenization, or context window overflow. |
| `PERSISTENCE_NOT_FOUND` | `-32020` | Persisted session ID or snapshot not found in SQLite store. |
| `PERSISTENCE_WRITE_ERROR`| `-32021` | Failed to serialize state or write to SQLite database / disk. |
| `PERSISTENCE_READ_ERROR` | `-32022` | Checksum mismatch or corrupted serialized state on disk. |

---

### 3.2 Tool 1: `load_model`

#### Pydantic Schema
```python
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
```

#### JSON Catalog Declaration (`TOOL_SCHEMAS`)
```json
{
  "name": "load_model",
  "description": "Loads an open-weight local language model or checkpoint (NVIDIA Nemotron, Transformers, GGUF, ONNX) into memory with configurable precision and device placement.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "model_path": {
        "type": "string",
        "description": "Local filesystem path or HuggingFace identifier for model weights."
      },
      "model_id": {
        "type": "string",
        "description": "Unique identifier assigned to the loaded model instance."
      },
      "model_format": {
        "type": "string",
        "enum": ["transformers", "nemotron", "nemo", "gguf", "onnx", "auto"],
        "default": "auto",
        "description": "Model framework/architecture format."
      },
      "device": {
        "type": "string",
        "enum": ["cpu", "cuda", "cuda:0", "auto", "mps"],
        "default": "auto",
        "description": "Compute device placement for tensor operations."
      },
      "precision": {
        "type": "string",
        "enum": ["fp16", "bf16", "fp32", "int8", "int4", "auto"],
        "default": "auto",
        "description": "Floating point precision or quantization mode."
      },
      "max_seq_length": {
        "type": "integer",
        "default": 4096,
        "description": "Maximum context sequence length in tokens."
      },
      "trust_remote_code": {
        "type": "boolean",
        "default": false,
        "description": "Allow loading custom modeling architectures from repository."
      }
    },
    "required": ["model_path"]
  }
}
```

---

### 3.3 Tool 2: `model_generate`

#### Pydantic Schema
```python
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
```

#### JSON Catalog Declaration (`TOOL_SCHEMAS`)
```json
{
  "name": "model_generate",
  "description": "Performs local text generation from a loaded open-weight model with sampling controls.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "model_id": {
        "type": "string",
        "description": "Identifier of the active loaded model."
      },
      "prompt": {
        "type": "string",
        "description": "Prompt text to complete."
      },
      "max_new_tokens": {
        "type": "integer",
        "default": 256,
        "minimum": 1,
        "maximum": 8192,
        "description": "Maximum number of new tokens to generate."
      },
      "temperature": {
        "type": "number",
        "default": 0.7,
        "minimum": 0.0,
        "maximum": 2.0,
        "description": "Sampling temperature (0.0 for deterministic greedy decoding)."
      },
      "top_p": {
        "type": "number",
        "default": 0.9,
        "minimum": 0.0,
        "maximum": 1.0,
        "description": "Nucleus sampling cumulative probability cutoff."
      },
      "top_k": {
        "type": "integer",
        "default": 50,
        "minimum": 0,
        "description": "Top-k sampling token filter."
      },
      "repetition_penalty": {
        "type": "number",
        "default": 1.1,
        "minimum": 1.0,
        "maximum": 2.0,
        "description": "Repetition penalty."
      },
      "stop_sequences": {
        "type": "array",
        "items": {"type": "string"},
        "description": "List of strings that stop generation when encountered."
      },
      "stream": {
        "type": "boolean",
        "default": false,
        "description": "Whether to stream token chunks."
      }
    },
    "required": ["model_id", "prompt"]
  }
}
```

---

### 3.4 Tool 3: `model_chat`

#### Pydantic Schema
```python
class ChatMessage(BaseModel):
    """Structured role message for chat completions."""
    role: Literal["system", "user", "assistant"] = Field(..., description="Message role.")
    content: str = Field(..., description="Text content of the message.")

class ModelChatInput(BaseModel):
    """Arguments for `model_chat` tool."""
    model_id: str = Field(..., description="Identifier of the loaded model instance.")
    messages: List[ChatMessage] = Field(..., min_length=1, description="Ordered conversation turns.")
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

    model_config = ConfigDict(extra="ignore")
```

#### JSON Catalog Declaration (`TOOL_SCHEMAS`)
```json
{
  "name": "model_chat",
  "description": "Executes multi-turn conversational chat completion applying structured chat templates (Nemotron, ChatML, Llama 3).",
  "inputSchema": {
    "type": "object",
    "properties": {
      "model_id": {
        "type": "string",
        "description": "Identifier of the loaded model instance."
      },
      "messages": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "role": {"type": "string", "enum": ["system", "user", "assistant"]},
            "content": {"type": "string"}
          },
          "required": ["role", "content"]
        },
        "description": "List of conversation messages in chronological order."
      },
      "chat_template": {
        "type": "string",
        "enum": ["auto", "nemotron", "chatml", "llama3", "mistral", "custom"],
        "default": "auto",
        "description": "Prompt formatting template to wrap conversation tokens."
      },
      "system_prompt": {
        "type": "string",
        "description": "Override system instructions if not present in messages list."
      },
      "max_new_tokens": {
        "type": "integer",
        "default": 512,
        "description": "Maximum tokens to generate for the assistant response."
      },
      "temperature": {
        "type": "number",
        "default": 0.7,
        "description": "Sampling temperature."
      },
      "top_p": {
        "type": "number",
        "default": 0.9,
        "description": "Nucleus sampling probability cutoff."
      }
    },
    "required": ["model_id", "messages"]
  }
}
```

---

### 3.5 Tool 4: `persist_sandbox`

#### Pydantic Schema
```python
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
```

#### JSON Catalog Declaration (`TOOL_SCHEMAS`)
```json
{
  "name": "persist_sandbox",
  "description": "Serializes sandbox REPL session, variable tables, snapshots, and filesystem state to disk (SQLite + filesystem).",
  "inputSchema": {
    "type": "object",
    "properties": {
      "sandbox_id": {
        "type": "string",
        "description": "Identifier of the active sandbox to persist."
      },
      "storage_path": {
        "type": "string",
        "description": "Custom directory path for the persistence SQLite database and assets."
      },
      "name": {
        "type": "string",
        "description": "Descriptive name for the persisted session."
      },
      "description": {
        "type": "string",
        "description": "Optional notes on the serialized execution state."
      },
      "include_variables": {
        "type": "boolean",
        "default": true,
        "description": "Whether to serialize in-memory REPL variables."
      },
      "include_snapshots": {
        "type": "boolean",
        "default": true,
        "description": "Whether to serialize existing memory snapshots."
      },
      "include_filesystem": {
        "type": "boolean",
        "default": true,
        "description": "Whether to archive sandbox filesystem artifacts."
      }
    },
    "required": ["sandbox_id"]
  }
}
```

---

### 3.6 Tool 5: `restore_sandbox_disk`

#### Pydantic Schema
```python
class RestoreSandboxDiskInput(BaseModel):
    """Arguments for `restore_sandbox_disk` tool."""
    persisted_id: Optional[str] = Field(None, description="Persistent record ID in SQLite store.")
    sandbox_id: Optional[str] = Field(None, description="Original sandbox ID to look up if persisted_id not given.")
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
```

#### JSON Catalog Declaration (`TOOL_SCHEMAS`)
```json
{
  "name": "restore_sandbox_disk",
  "description": "Restores a previously persisted sandbox session from disk back into an active sandbox execution environment.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "persisted_id": {
        "type": "string",
        "description": "Persistent record identifier in the disk store."
      },
      "sandbox_id": {
        "type": "string",
        "description": "Target sandbox ID to locate in the persistent store."
      },
      "storage_path": {
        "type": "string",
        "description": "Custom directory path for the persistence SQLite database."
      },
      "target_mode": {
        "type": "string",
        "enum": ["auto", "local", "e2b"],
        "default": "auto",
        "description": "Target execution engine backend."
      },
      "restore_variables": {
        "type": "boolean",
        "default": true,
        "description": "Whether to inject saved variables into the REPL namespace."
      },
      "restore_snapshots": {
        "type": "boolean",
        "default": true,
        "description": "Whether to restore memory snapshot checkpoints."
      },
      "new_sandbox_id": {
        "type": "string",
        "description": "Optional new ID to assign to the restored sandbox instance (cloning)."
      }
    },
    "required": []
  }
}
```

---

### 3.7 Tool 6: `list_persisted_sandboxes`

#### Pydantic Schema
```python
class ListPersistedSandboxesInput(BaseModel):
    """Arguments for `list_persisted_sandboxes` tool."""
    storage_path: Optional[str] = Field(None, description="Custom root directory path for SQLite store.")
    filter_name: Optional[str] = Field(None, description="Optional name substring filter.")
    limit: Optional[int] = Field(50, ge=1, le=200, description="Max number of records to return.")
    offset: Optional[int] = Field(0, ge=0, description="Pagination offset.")
    include_details: Optional[bool] = Field(False, description="Whether to include full variable manifests.")

    model_config = ConfigDict(extra="ignore")
```

#### JSON Catalog Declaration (`TOOL_SCHEMAS`)
```json
{
  "name": "list_persisted_sandboxes",
  "description": "Lists all sandbox sessions and state snapshots currently stored in the SQLite persistence engine.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "storage_path": {
        "type": "string",
        "description": "Custom directory path for the persistence SQLite database."
      },
      "filter_name": {
        "type": "string",
        "description": "Filter sessions matching name substring."
      },
      "limit": {
        "type": "integer",
        "default": 50,
        "minimum": 1,
        "maximum": 200,
        "description": "Pagination record limit."
      },
      "offset": {
        "type": "integer",
        "default": 0,
        "minimum": 0,
        "description": "Pagination offset."
      },
      "include_details": {
        "type": "boolean",
        "default": false,
        "description": "Whether to include variable metadata details."
      }
    },
    "required": []
  }
}
```

---

## 4. Progressive Disclosure Skill Suite Architecture

The Antigravity Customization Plugin (`plugins/antigravity-sandbox-plugin/`) is extended with two progressive disclosure skills following the standard Antigravity skill specification:

```
plugins/antigravity-sandbox-plugin/
├── plugin.json                              # Updated manifest with 5 skills and keywords
├── mcp_config.json                          # MCP server runtime configuration
├── hooks.json                               # Workspace event hooks
├── rules/
│   └── AGENTS.md                            # Comprehensive operational rules for agents
└── skills/
    ├── sandbox-execution/                   # (Existing) Core sandbox execution & REPL
    │   ├── SKILL.md
    │   └── references/
    │       ├── repl-patterns.md
    │       └── artifact-extraction.md
    ├── worker-orchestration/                # (Existing) Background daemon & cron tasks
    │   ├── SKILL.md
    │   └── references/
    │       └── cron-syntax.md
    ├── snapshot-management/                 # (Existing) Checkpointing & branching
    │   ├── SKILL.md
    │   └── references/
    │       └── branching.md
    ├── local-inference/                     # [NEW - R4] Real local model inference
    │   ├── SKILL.md
    │   └── references/
    │       ├── nemotron-architecture.md     # Nemotron-Mini-4B, NeMo checkpoints, prompt tokens
    │       ├── device-and-precision.md      # CPU vs CUDA, FP16/BF16/INT8, VRAM budgeting
    │       ├── chat-templates.md            # Nemotron, ChatML, Llama 3 formatting
    │       └── generation-parameters.md     # Sampling parameters, temp, top_p, penalties
    └── disk-persistence/                    # [NEW - R4] SQLite & directory persistence
        ├── SKILL.md
        └── references/
            ├── session-persistence.md       # SQLite schema, variable serialization, pickles
            ├── snapshot-branching.md        # State vector diffs & multi-branch trees on disk
            └── worker-recovery.md           # Worker daemon recovery across process restarts
```

### 4.1 Specification for `skills/local-inference/SKILL.md`
- **Frontmatter**:
  ```yaml
  ---
  name: local-inference
  description: Load and execute real local open-weight language models (NVIDIA Nemotron-Mini-4B, NeMo checkpoints, Transformers, GGUF, ONNX) with CPU/CUDA device placement, token generation, and multi-turn chat completions directly inside the Antigravity sandbox.
  ---
  ```
- **Structure**:
  - **Overview**: Local inference architecture without external API dependencies or mock placeholders.
  - **Tool Reference Table**: `load_model`, `model_generate`, `model_chat`.
  - **Step-by-Step Workflow**:
    1. Inspecting compute resources and selecting device/precision (`cpu` vs `cuda`, `fp16`/`int8`).
    2. Loading weights via `load_model`.
    3. Generating raw text completions via `model_generate`.
    4. Executing multi-turn structured conversations via `model_chat` with Nemotron/ChatML templates.
    5. In-sandbox model synthesis: combining model generation with immediate sandbox code execution.
    6. Memory management: unloading models or offloading to disk when switching tasks.
  - **Reference Links**: `references/nemotron-architecture.md`, `references/device-and-precision.md`, `references/chat-templates.md`, `references/generation-parameters.md`.

### 4.2 Specification for `skills/disk-persistence/SKILL.md`
- **Frontmatter**:
  ```yaml
  ---
  name: disk-persistence
  description: Persist and restore sandbox REPL sessions, multi-branch snapshot trees, variable registries, and scheduled worker histories to durable disk storage (SQLite + filesystem) across restarts and process boundaries.
  ---
  ```
- **Structure**:
  - **Overview**: Durable SQLite and directory state persistence engine (`PersistenceManager`).
  - **Tool Reference Table**: `persist_sandbox`, `restore_sandbox_disk`, `list_persisted_sandboxes`, `manage_snapshot`.
  - **Step-by-Step Workflow**:
    1. Creating checkpoints of long-running data ingestion and ML training to disk.
    2. Persisting complete REPL sessions before context handoffs or restarts.
    3. Querying and listing persisted session catalogs with `list_persisted_sandboxes`.
    4. Restoring sessions in completely new processes using `restore_sandbox_disk`.
    5. Managing branched exploration trees on disk.
    6. Recovering scheduled worker task registries and execution history buffers.
  - **Reference Links**: `references/session-persistence.md`, `references/snapshot-branching.md`, `references/worker-recovery.md`.

### 4.3 Updates to `plugin.json`, `mcp_config.json`, and `rules/AGENTS.md`
1. **`plugin.json`**:
   - Add `"local-inference"` and `"disk-persistence"` to `"skills"` list.
   - Add keywords: `"local-models"`, `"nemotron"`, `"persistence"`, `"sqlite"`, `"inference"`, `"transformers"`, `"safetensors"`.
   - Update version to `"0.2.0"`.
2. **`rules/AGENTS.md`**:
   - Add **Section 9: Local Model Inference Directives**:
     - *Hardware Awareness*: Check GPU availability before requesting `cuda`; default to `auto` with `fp16` or `int8` quantization to conserve memory.
     - *Model Lifecycle*: Do not keep multiple large models loaded simultaneously in memory unless needed; unload inactive weights.
     - *Chat Templating*: Always specify appropriate chat template (`nemotron`, `chatml`, `llama3`) matching the underlying checkpoint architecture.
   - Add **Section 10: Disk Persistence & Session Durability Directives**:
     - *Session Checkpointing*: Call `persist_sandbox` before executing risky transformations, ending conversation turns, or initiating worker delegation.
     - *Clean Variable Spaces*: Avoid storing open file descriptors, sockets, or thread handles in global REPL variables intended for disk serialization.
     - *Session Restoration*: When resuming previous research tasks, query `list_persisted_sandboxes` and restore via `restore_sandbox_disk`.

---

## 5. Comprehensive Verification & Test Suite Expansion (Tiers 1–5)

To guarantee production readiness and verify Requirements R1–R5, the pytest test suite is expanded to cover all 5 test tiers:

### 5.1 Test Suite Matrix

```
tests/
├── conftest.py                                   # Enhanced fixtures: SQLite store, real model fixtures, MCP test client
├── tier1_features/
│   ├── test_sandbox_features.py                  # (Existing) Base sandbox features
│   ├── test_repl_features.py                     # (Existing) REPL features
│   ├── test_mcp_features.py                      # (Existing) 7 core MCP tools
│   ├── test_plugin_features.py                   # (Existing) Plugin manifest & skills
│   ├── test_scheduler_features.py                # (Existing) Scheduler triggers
│   ├── test_local_sandbox_optimal.py             # (Existing) Local sandbox optimizations
│   ├── test_persistence_features.py              # [NEW] SQLite store, variable serialization, snapshot persistence
│   ├── test_local_model_features.py              # [NEW] LocalModelRunner, NemotronEngine, weight loading, generation
│   ├── test_mcp_extended_tools.py                # [NEW] 6 new MCP tools via JSON-RPC 2.0
│   └── test_extended_plugin_skills.py            # [NEW] local-inference & disk-persistence SKILL.md & references
├── tier2_boundaries/
│   ├── test_ast_security_boundaries.py           # (Existing) AST node whitelist & dunders
│   ├── test_sandbox_timeouts_and_errors.py       # (Existing) Timeouts & exception handling
│   ├── test_scheduler_cron_edge_cases.py         # (Existing) Cron edge cases
│   ├── test_mcp_protocol_boundaries.py           # (Existing) JSON-RPC protocol edge cases
│   ├── test_persistence_boundaries.py            # [NEW] Corrupted SQLite, non-serializable objects, empty state
│   ├── test_local_model_boundaries.py            # [NEW] Context window overflows, empty prompts, invalid sampling
│   └── test_mcp_extended_boundaries.py           # [NEW] Missing fields, type validation in 6 new tools
├── tier3_cross_feature/
│   ├── test_mcp_sandbox_pipeline.py              # (Existing) MCP to sandbox pipeline
│   ├── test_scheduler_sandbox_pipeline.py        # (Existing) Scheduler to sandbox pipeline
│   ├── test_fallback_degradation_pipeline.py     # (Existing) E2B fallback pipeline
│   ├── test_persistence_sandbox_pipeline.py      # [NEW] REPL execute -> persist -> terminate -> restore in new process -> verify
│   ├── test_mcp_model_sandbox_pipeline.py        # [NEW] load_model -> model_generate -> sandbox execute -> persist
│   └── test_scheduler_persistence_pipeline.py    # [NEW] Worker daemon task history persisted across daemon restart
├── tier4_workloads/
│   ├── test_agent_multi_turn_analysis.py         # (Existing) Multi-turn analytics
│   ├── test_artifact_data_pipeline.py            # (Existing) Artifact handling
│   ├── test_scheduled_health_monitoring.py       # (Existing) Health monitoring
│   ├── test_multi_turn_agent_with_local_model.py # [NEW] Autonomous agent reasoning with local model & sandbox
│   ├── test_snapshot_branching_persistence.py    # [NEW] Tree branching persisted and navigated from SQLite
│   └── test_model_whitelisting_in_sandbox.py     # [NEW] torch/transformers execution inside LocalSandbox
└── tier5_adversarial/
    ├── test_adversarial_security.py              # (Existing) Exploit attempts & AST bypass
    ├── test_m1_deep_challenge.py                 # (Existing) Sandbox challenges
    ├── test_m1_it2_adversarial.py                # (Existing) Introspection & metaclass probes
    ├── test_m3_scheduler_deep_challenge.py       # (Existing) Scheduler ring buffer & concurrency
    ├── test_resilience_and_stress.py             # (Existing) Rapid stress & memory truncation
    └── test_adversarial_persistence_and_models.py# [NEW] Concurrent SQLite writes, OOM recovery, AST bypass probes
```

### 5.2 Test Fixture Design (`tests/conftest.py`)
1. `tmp_storage_dir`: Dedicated temporary filesystem path for SQLite database (`sandbox_states.db`) and serialized variable blobs.
2. `persistence_manager`: Instance of `PersistenceManager` linked to `tmp_storage_dir`.
3. `local_model_engine`: Lightweight real model runner using lightweight Transformer / GGUF / ONNX or Nemotron-Mini weights (with deterministic fallback testing double when weight files are downloaded on-demand).
4. `extended_mcp_client`: `StdioMCPTestClient` wired to `AntigravityMCPServer` initialized with `PersistenceManager` and `LocalModelRunner`.

---

## 6. End-to-End Demo Script (`demo.py`) Specification

The demo script demonstrates complete real-world autonomous agent workflows running on standard hardware without mock placeholders.

### 6.1 Demonstration Workflow Steps
```
+------------------------------------------------------------------------------------+
|                       demo.py Execution Flow Architecture                          |
+------------------------------------------------------------------------------------+

  [Step 1] System Environment & Persistence Initialization
           - Print platform, python version, device info (CUDA/CPU).
           - Initialize PersistenceManager (SQLite DB: .antigravity/storage/demo.db).
           - Provision LocalSandbox (REPL session: sb-demo-01).

  [Step 2] Real Local Model Loading & Generation (Nemotron/Transformers)
           - Load local open-weight model via LocalModelRunner / load_model.
           - Execute model_generate with sampling parameters (temp=0.7, top_p=0.9).
           - Execute model_chat with Nemotron chat template formatting.
           - Display generation output, tokens/sec, and latency.

  [Step 3] Stateful In-Sandbox Computation & Data Processing
           - Feed generated data/code into LocalSandbox REPL.
           - Compute statistical metrics (variance, std_dev, quantiles).
           - Store intermediate variables in REPL memory namespace.

  [Step 4] Disk Persistence & Process Boundary Simulation
           - Invoke persist_sandbox to serialize REPL state, variables, and snapshots.
           - Verify SQLite records written to disk.
           - Terminate and destroy active in-memory sandbox and model runners.

  [Step 5] Process Recovery & Restoration from Disk
           - Create a completely new LocalSandbox instance (sb-demo-restored).
           - Invoke restore_sandbox_disk from SQLite store.
           - Execute Python code referencing variables created in Step 3.
           - Verify variable continuity and zero state loss.

  [Step 6] Persistent Scheduled Background Worker
           - Initialize ServiceWorkerDaemon with disk store.
           - Register scheduled task, trigger execution, record run logs in SQLite.
           - Inspect persisted task history and daemon health metrics.

  [Step 7] Cleanup & Summary Verification Matrix
           - Cancel worker jobs, close database connection, purge temporary assets.
           - Output JSON verification matrix with 100% PASSED statuses.
```

---

## 7. Edge Cases & Risk Analysis Table

| # | Feature / Boundary | Edge Case Input / Condition | Expected Behavior & Mitigation |
|---|--------------------|-----------------------------|--------------------------------|
| 1 | `load_model` | Missing local weight directory or invalid HF repo name | Returns `MODEL_NOT_FOUND` error (`-32010`) with descriptive path error without crashing MCP server. |
| 2 | `load_model` | CUDA device requested on CPU-only hardware (`device="cuda"`) | Automatically falls back to `"cpu"` with informative log warning, or returns clean `isError: true` if explicit fallback is disabled. |
| 3 | `load_model` | Model weight tensor size exceeds available system RAM / VRAM | Catch `torch.cuda.OutOfMemoryError` / `MemoryError`, invoke garbage collection (`gc.collect()`), and return `MODEL_LOAD_ERROR` (`-32011`). |
| 4 | `model_generate` | Prompt token length + `max_new_tokens` > `max_seq_length` | Cleanly truncate prompt with warning or return `MODEL_INFERENCE_ERROR` (`-32012`) rather than throwing raw tensor shape exception. |
| 5 | `model_chat` | Message list contains empty messages or invalid role (`role: "invalid"`) | Pydantic validation rejects with `INVALID_PARAMS` (`-32602`), detailing schema mismatch. |
| 6 | `persist_sandbox` | REPL contains unpickleable objects (e.g. active file handles, generators, thread locks) | Selective serialization: serializes primitive types, numpy/pandas arrays, dataclasses; converts unpickleable objects to structured string/type representation with warning log. |
| 7 | `persist_sandbox` | Concurrent writes to SQLite database from multiple worker processes | Enable SQLite WAL (Write-Ahead Logging) mode and configure busy timeout (`timeout=30.0`) in SQLite connection. |
| 8 | `restore_sandbox_disk` | Target `persisted_id` or `sandbox_id` does not exist in SQLite DB | Returns `PERSISTENCE_NOT_FOUND` (`-32020`) with list of available persisted IDs. |
| 9 | `restore_sandbox_disk` | Corrupted binary blob in variable table (checksum mismatch) | Raise `PERSISTENCE_READ_ERROR` (`-32022`), preserve existing sandbox state without corruption. |
| 10| Sandbox AST Whitelist | Sandboxed script imports `torch`, `transformers`, `safetensors`, `tokenizers`, `onnxruntime` | Module whitelist allows imports; dynamic dunder escapes (`__globals__`, `__subclasses__`) remain strictly blocked by AST validator. |

---

## 8. Conclusion & Implementation Readiness

Requirements R4 and R5 are fully specified with complete schema contracts, Pydantic data models, tool implementations, progressive disclosure skill hierarchies, test matrix across Tiers 1–5, and end-to-end verification workflows. All interfaces are aligned with existing subsystems and ready for implementation.
