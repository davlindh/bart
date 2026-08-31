# Project: Antigravity Platform — MicroVM Sandbox, Real Local Model Inference, Disk Persistence & MCP Plugin

## Architecture
The system consists of 6 integrated, enterprise-grade subsystems:
1. **MicroVM Sandbox & Execution Engine (`src/antigravity/sandbox/`)**: Unified sandbox interface (`BaseSandbox`) with `E2BSandbox` (Firecracker microVMs) and `LocalSandbox` (secure AST-validated persistent REPL subprocess with state export/hydration and memory management), managed by `SandboxManager`.
2. **Disk-Backed Local Persistence Store (`src/antigravity/storage/`)**: SQLite and directory-backed persistence engine (`PersistenceManager`, `DiskStateStore`, `SQLiteEngine`, `VariableSerializer`) persisting sandbox sessions, multi-branch snapshot state vectors, variable tables, scheduled worker task histories, and model configurations across restarts and process boundaries.
3. **Real Local Model Inference Engine (`src/antigravity/models/`)**: Multi-backend local inference engine (`LocalModelRunner`, `NemotronEngine`, `LightweightTransformerEngine`, `HuggingFaceEngine`, `ONNXRuntimeEngine`) supporting NVIDIA Nemotron (e.g. `nvidia/Nemotron-Mini-4B-Instruct`, NeMo checkpoints), real weight loading, tokenization, chat templating, sampling, and CPU/GPU device placement without mock stubs.
4. **Scheduled Service Worker Daemon (`src/antigravity/scheduler/`)**: Non-blocking async daemon supporting cron expressions and duration timers, disk-backed task registry and execution history, isolated sandbox task execution, and health monitoring.
5. **Antigravity MCP Server (`src/antigravity/mcp/`)**: Standard JSON-RPC 2.0 stdio server exposing 13 lifecycle, execution, snapshot, worker, disk persistence, and model inference tools.
6. **Antigravity Customization Plugin (`plugins/antigravity-sandbox-plugin/`)**: Production plugin packaging with manifest, MCP configuration, workspace rules (AGENTS.md), and progressive disclosure skills (`sandbox-execution`, `worker-orchestration`, `snapshot-management`, `local-inference`, `disk-persistence`).

```
+----------------------------------------------------------------------------------------------------+
|                                    Antigravity Agent / Client                                      |
+----------------------------------------------------------------------------------------------------+
                                                  │
                               ┌──────────────────┴──────────────────┐
                               │ JSON-RPC 2.0 stdio Transport        │
                               ▼                                     ▼
                ┌─────────────────────────────┐        ┌────────────────────────────┐
                │   Antigravity MCP Server    │        │ Antigravity Customization  │
                │   (src/antigravity/mcp)     │        │ Plugin & Skill Suite       │
                │                             │        │ (plugins/antigravity-...)  │
                │ - create_sandbox            │        │ - plugin.json, mcp_config  │
                │ - execute_code              │        │ - 5 SKILL.md suites        │
                │ - pause/resume/destroy      │        │ - rules/AGENTS.md          │
                │ - manage_snapshot           │        └────────────────────────────┘
                │ - spawn_worker              │
                │ - load_model                │
                │ - model_generate            │
                │ - model_chat                │
                │ - persist_sandbox           │
                │ - restore_sandbox_disk      │
                │ - list_persisted_sandboxes  │
                └──────────────┬──────────────┘
                               │
            ┌──────────────────┼─────────────────────────────┐
            ▼                  ▼                             ▼
┌─────────────────────────┐ ┌───────────────────────────┐ ┌──────────────────────────────────┐
│ MicroVM Sandbox Engine  │ │ Local Model Inference     │ │ Scheduled Service Worker Daemon  │
│ (src/antigravity/       │ │ (src/antigravity/models)  │ │ (src/antigravity/scheduler)      │
│  sandbox)               │ │                           │ │                                  │
│ - BaseSandbox           │ │ - NemotronEngine          │ │ - CronTrigger & TimerTrigger     │
│ - ASTSecurityValidator  │ │ - LightweightTransformer  │ │ - Persistent TaskRegistry        │
│ - LocalSandbox & REPL   │ │ - HuggingFaceEngine       │ │ - History Ring Buffer            │
│ - E2BSandbox            │ │ - ONNXRuntimeEngine       │ │ - HealthMonitor                  │
│ - SandboxManager        │ │ - LocalModelRunner        │ └────────────────┬─────────────────┘
└───────────┬─────────────┘ └─────────────┬─────────────┘                  │
            │                             │                                │
            └─────────────────────────────┼────────────────────────────────┘
                                          ▼
                       ┌──────────────────────────────────────┐
                       │ Disk-Backed Persistence Engine       │
                       │ (src/antigravity/storage)            │
                       │ - SQLiteEngine (WAL + 8 tables)      │
                       │ - DiskStateStore (Atomic + SHA256)   │
                       │ - VariableSerializer (4-tier codec)  │
                       │ - PersistenceManager (High-level API)│
                       └──────────────────────────────────────┘
```

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | BaseSandbox & ExecutionResult | Common sandbox abstraction, lifecycle interface, and structured result models | M1 | R1 |
| 2 | AST Security Validator | AST parsing, node whitelist, dunder blocking, import validation | M1 | R1 |
| 3 | Sanitized Runtime Builtins | Stripped builtins preventing escape via eval/exec/open | M1 | R1 |
| 4 | Persistent REPL Subprocess | Long-lived Python subprocess retaining session state across execution turns | M1 | R1 |
| 5 | LocalSandbox Fallback Engine | Standalone secure sandbox executing scripts/REPL with timeout enforcement | M1 | R1 |
| 6 | E2B Firecracker Sandbox Driver | E2B Cloud Firecracker microVM integration with pause/resume & snapshots | M1 | R1 |
| 7 | SandboxManager & Fallback | Factory and routing engine with automatic fallback when E2B is unavailable | M1 | R1 |
| 8 | Artifact Capture & Serialization | Auto-capture of stdout, stderr, PNG charts (base64), CSVs, and exit status | M1 | R1, R2 |
| 9 | MCP Protocol & Transport | JSON-RPC 2.0 over stdio with message framing and stderr logging isolation | M2 | R2 |
| 10 | MCP Lifecycle Tools | `create_sandbox`, `pause_sandbox`, `resume_sandbox`, `destroy_sandbox` | M2 | R2 |
| 11 | MCP Execution Tool | `execute_code` with REPL / script mode, timeout, and streaming support | M2 | R2 |
| 12 | MCP Snapshot Tool | `manage_snapshot` for in-memory state saving and branching | M2 | R2 |
| 13 | MCP Worker Tool | `spawn_worker` registering tasks into the background daemon | M2 | R2, R4 |
| 14 | Cron & Timer Triggers | 5-field standard cron parsing and delta duration timer calculations | M3 | R4 |
| 15 | Task Registry & Scheduler Daemon | AsyncIO event loop prioritizing tasks, managing task states and concurrency | M3 | R4 |
| 16 | Isolated Worker Execution | Executing scheduled jobs inside sandboxes with output & error logging | M3 | R4 |
| 17 | Health Monitor & Task Inspection | Inspection API for active jobs, next run times, history, and status | M3 | R4 |
| 18 | Antigravity Plugin Packaging | `plugin.json`, `mcp_config.json`, `hooks.json` in `plugins/antigravity-sandbox-plugin` | M4 | R3 |
| 19 | Antigravity Skill Suite (Core) | Progressive disclosure `SKILL.md` (sandbox-execution, worker-orchestration, snapshot-management) | M4 | R3 |
| 20 | Antigravity Workspace Rules | Operational and safety guidelines in `rules/AGENTS.md` | M4 | R3 |
| 21 | Disk-Backed Persistence Engine | SQLite WAL engine + atomic filesystem blob store (`src/antigravity/storage/`) | M5 | R1 |
| 22 | Multi-Branch Snapshot DAG Persistence | Persisting session variables, snapshot DAGs, branch recovery in new processes | M5 | R1 |
| 23 | Persistent Task Registry | Backing scheduler tasks and history records in SQLite across daemon restarts | M5 | R1 |
| 24 | Heterogeneous Variable Codec | 4-tier serialization hierarchy (JSON -> safetensors/npy -> safe pickle -> unrestorable) | M5 | R1 |
| 25 | Real Local Model Inference Engine | `LocalModelRunner` supporting CPU/GPU device selection, weights, tokenizers, chat templating | M6 | R2 |
| 26 | NVIDIA Nemotron Engine | Real Nemotron architecture support, prompt templating, NeMo checkpoint loading | M6 | R2 |
| 27 | Lightweight Zero-Mock Transformer | Pure mathematical causal self-attention, GQA, RoPE, RMSNorm, SwiGLU, nucleus sampler | M6 | R2 |
| 28 | HuggingFace & ONNX Backends | Seamless execution with `transformers` and `onnxruntime` when installed | M6 | R2 |
| 29 | Sandbox ML Security Whitelisting | Whitelisting `torch`, `transformers`, `tokenizers`, `safetensors`, `onnxruntime`, `accelerate` in AST | M6 | R3 |
| 30 | Sandbox ML Memory Management | Tensor repr formatting, `torch.cuda.empty_cache()` and `gc.collect()` in REPL worker | M6 | R3 |
| 31 | Extended MCP Inference Tools | `load_model`, `model_generate`, `model_chat` tools with structured JSON-RPC schemas | M7 | R4 |
| 32 | Extended MCP Persistence Tools | `persist_sandbox`, `restore_sandbox_disk`, `list_persisted_sandboxes` tools | M7 | R4 |
| 33 | Extended Plugin Skill Suite | `skills/local-inference/` and `skills/disk-persistence/` with reference documentation | M7 | R4 |
| 34 | Comprehensive E2E Pytest Suite | Pytest test suite spanning Tiers 1-5 across persistence, models, sandbox, MCP | M-E2E | R5 |
| 35 | End-to-End Demo Script | `demo.py` showcasing persistence round-trips, real model loading, sandbox execution, worker durability | M-E2E | R5 |
| 36 | Adversarial Hardening (Tier 5) | Security exploit probes, corrupted persistence recovery, edge case inference tests | M-FINAL | R5 |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | MicroVM Sandbox & Execution Engine | Baseline sandbox abstractions, AST security, REPL worker, E2B driver, SandboxManager | none | DONE |
| M2 | Antigravity MCP Server | Baseline 7 MCP tools, JSON-RPC 2.0 stdio server, Pydantic schemas | M1 | DONE |
| M3 | Scheduled Background Worker Daemon | AsyncIO daemon, Cron & Timer triggers, TaskRegistry, health inspection | M1 | DONE |
| M4 | Customization Plugin & Skill Suite | Baseline plugin packaging, rules/AGENTS.md, 3 core skills | M2, M3 | DONE |
| M5 | Disk-Backed Local Persistence Store | R1: `src/antigravity/storage/`, REPL export/hydrate IPC, persistent TaskRegistry | M1, M3 | IN_PROGRESS |
| M6 | Real Local Model Inference & Security | R2, R3: `src/antigravity/models/`, Nemotron support, AST & builtins ML whitelisting | M1 | IN_PROGRESS |
| M7 | Extended MCP Tools & Skills Suite | R4: 6 new MCP tools, `skills/local-inference`, `skills/disk-persistence`, AGENTS.md | M2, M4, M5, M6 | PLANNED |
| M-E2E | Comprehensive Test Suite & Demo | R5: Pytest Tiers 1-5 test expansion, complete runnable `demo.py` | M5, M6, M7 | PLANNED |
| M-FINAL | Final Verification & Hardening | Phase 1: 100% test pass; Phase 2: Tier 5 adversarial review & forensic integrity audit | M-E2E | PLANNED |

## Interface Contracts

### 1. `antigravity.storage` ↔ `antigravity.sandbox` & `antigravity.scheduler`
```python
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

@dataclass
class VariableRecord:
    name: str
    type_name: str
    encoding: str  # "json", "blob_safetensors", "blob_pickle", "unrestorable"
    value_json: Optional[str] = None
    blob_hash: Optional[str] = None
    size_bytes: int = 0
    repr_str: str = ""

@dataclass
class SnapshotRecord:
    snapshot_id: str
    sandbox_id: str
    parent_snapshot_id: Optional[str] = None
    branch_name: str = "main"
    created_at: float = 0.0
    description: str = ""
    variable_count: int = 0
    variables: Dict[str, VariableRecord] = field(default_factory=dict)
    state_metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class PersistedSandboxRecord:
    sandbox_id: str
    mode: str
    status: str
    created_at: float
    updated_at: float
    env_json: str
    active_snapshot_id: Optional[str] = None
    variable_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

class PersistenceManager:
    def __init__(self, base_dir: Optional[str] = None): ...
    def save_sandbox(self, sandbox_id: str, mode: str, env: Dict[str, str], variables: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None) -> PersistedSandboxRecord: ...
    def load_sandbox(self, sandbox_id: str) -> Optional[Tuple[PersistedSandboxRecord, Dict[str, Any]]]: ...
    def list_persisted_sandboxes(self) -> List[PersistedSandboxRecord]: ...
    def delete_persisted_sandbox(self, sandbox_id: str) -> bool: ...
    def save_snapshot(self, sandbox_id: str, snapshot_id: str, variables: Dict[str, Any], parent_snapshot_id: Optional[str] = None, branch_name: str = "main", description: str = "", metadata: Optional[Dict[str, Any]] = None) -> SnapshotRecord: ...
    def load_snapshot(self, sandbox_id: str, snapshot_id: str) -> Optional[Tuple[SnapshotRecord, Dict[str, Any]]]: ...
    def list_snapshots(self, sandbox_id: str) -> List[SnapshotRecord]: ...
    def save_task(self, task: Any) -> None: ...
    def load_tasks(self) -> List[Any]: ...
    def record_task_execution(self, task_id: str, result: Any) -> None: ...
    def get_task_history(self, task_id: str, limit: int = 50) -> List[Any]: ...
```

### 2. `antigravity.models` ↔ `antigravity.mcp` & `antigravity.sandbox`
```python
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

class ModelBackend(str, Enum):
    NEMOTRON = "nemotron"
    LIGHTWEIGHT = "lightweight"
    TRANSFORMERS = "transformers"
    ONNX = "onnx"
    AUTO = "auto"

@dataclass
class ModelConfig:
    model_id: str
    backend: ModelBackend = ModelBackend.AUTO
    model_path: Optional[str] = None
    device: str = "cpu"  # "cpu", "cuda", "auto"
    precision: str = "float32"  # "float32", "float16", "bfloat16", "int8", "int4"
    max_context_length: int = 4096
    chat_template: Optional[str] = None
    extra_params: Dict[str, Any] = field(default_factory=dict)

@dataclass
class GenerationConfig:
    max_new_tokens: int = 256
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 50
    repetition_penalty: float = 1.1
    stop_sequences: List[str] = field(default_factory=list)
    seed: Optional[int] = None

@dataclass
class ChatMessage:
    role: str  # "system", "user", "assistant"
    content: str

@dataclass
class GenerationResult:
    text: str
    tokens_generated: int
    prompt_tokens: int
    finish_reason: str  # "stop", "length", "eos"
    duration_ms: float
    metadata: Dict[str, Any] = field(default_factory=dict)

class BaseModelEngine:
    def load(self, config: ModelConfig) -> bool: ...
    def generate(self, prompt: str, gen_config: Optional[GenerationConfig] = None) -> GenerationResult: ...
    def chat(self, messages: List[ChatMessage], gen_config: Optional[GenerationConfig] = None) -> GenerationResult: ...
    def unload(self) -> None: ...
    @property
    def is_loaded(self) -> bool: ...

class LocalModelRunner:
    def __init__(self): ...
    def load_model(self, config: ModelConfig) -> BaseModelEngine: ...
    def get_model(self, model_id: str) -> Optional[BaseModelEngine]: ...
    def list_loaded_models(self) -> List[Dict[str, Any]]: ...
    def unload_model(self, model_id: str) -> bool: ...
    def generate(self, model_id: str, prompt: str, gen_config: Optional[GenerationConfig] = None) -> GenerationResult: ...
    def chat(self, model_id: str, messages: List[ChatMessage], gen_config: Optional[GenerationConfig] = None) -> GenerationResult: ...
```

## Code Layout
```
c:\Users\info\OneDrive\Dokument\GitHub\fart\
├── pyproject.toml
├── README.md
├── demo.py
├── src\
│   └── antigravity\
│       ├── __init__.py
│       ├── storage\
│       │   ├── __init__.py
│       │   ├── models.py
│       │   ├── sqlite_engine.py
│       │   ├── disk_store.py
│       │   ├── serializer.py
│       │   └── persistence_manager.py
│       ├── models\
│       │   ├── __init__.py
│       │   ├── models.py
│       │   ├── base.py
│       │   ├── sampler.py
│       │   ├── tokenizers.py
│       │   ├── nemotron.py
│       │   ├── transformer_engine.py
│       │   ├── hf_engine.py
│       │   ├── onnx_engine.py
│       │   └── runner.py
│       ├── sandbox\
│       │   ├── __init__.py
│       │   ├── base.py
│       │   ├── models.py
│       │   ├── ast_security.py
│       │   ├── builtins_sanitizer.py
│       │   ├── local_repl_worker.py
│       │   ├── local_sandbox.py
│       │   ├── e2b_sandbox.py
│       │   └── manager.py
│       ├── mcp\
│       │   ├── __init__.py
│       │   ├── protocol.py
│       │   ├── server.py
│       │   ├── tools.py
│       │   ├── schemas.py
│       │   └── runner.py
│       └── scheduler\
│           ├── __init__.py
│           ├── triggers.py
│           ├── models.py
│           ├── daemon.py
│           ├── registry.py
│           └── monitor.py
├── plugins\
│   └── antigravity-sandbox-plugin\
│       ├── plugin.json
│       ├── mcp_config.json
│       ├── hooks.json
│       ├── rules\
│       │   └── AGENTS.md
│       └── skills\
│           ├── sandbox-execution\
│           │   ├── SKILL.md
│           │   └── references\
│           ├── worker-orchestration\
│           │   ├── SKILL.md
│           │   └── references\
│           ├── snapshot-management\
│           │   ├── SKILL.md
│           │   └── references\
│           ├── local-inference\
│           │   ├── SKILL.md
│           │   └── references\
│           │       ├── nemotron-architecture.md
│           │       ├── device-and-precision.md
│           │       ├── chat-templates.md
│           │       └── generation-parameters.md
│           └── disk-persistence\
│               ├── SKILL.md
│               └── references\
│                   ├── session-persistence.md
│                   ├── snapshot-branching.md
│                   └── worker-recovery.md
└── tests\
    ├── __init__.py
    ├── conftest.py
    ├── tier1_features\
    │   ├── test_sandbox_features.py
    │   ├── test_repl_features.py
    │   ├── test_mcp_features.py
    │   ├── test_plugin_features.py
    │   ├── test_scheduler_features.py
    │   ├── test_persistence_features.py
    │   ├── test_local_model_features.py
    │   ├── test_mcp_extended_tools.py
    │   └── test_extended_plugin_skills.py
    ├── tier2_boundaries\
    │   ├── test_ast_security_boundaries.py
    │   ├── test_sandbox_timeouts_and_errors.py
    │   ├── test_scheduler_cron_edge_cases.py
    │   ├── test_mcp_protocol_boundaries.py
    │   ├── test_persistence_boundaries.py
    │   ├── test_local_model_boundaries.py
    │   └── test_mcp_extended_boundaries.py
    ├── tier3_cross_feature\
    │   ├── test_mcp_sandbox_pipeline.py
    │   ├── test_scheduler_sandbox_pipeline.py
    │   ├── test_fallback_degradation_pipeline.py
    │   ├── test_persistence_sandbox_pipeline.py
    │   ├── test_mcp_model_sandbox_pipeline.py
    │   └── test_scheduler_persistence_pipeline.py
    ├── tier4_workloads\
    │   ├── test_agent_multi_turn_analysis.py
    │   ├── test_scheduled_health_monitoring.py
    │   ├── test_artifact_data_pipeline.py
    │   ├── test_multi_turn_agent_with_local_model.py
    │   ├── test_snapshot_branching_persistence.py
    │   └── test_model_whitelisting_in_sandbox.py
    └── tier5_adversarial\
        ├── test_adversarial_security.py
        └── test_adversarial_persistence_and_models.py
```
