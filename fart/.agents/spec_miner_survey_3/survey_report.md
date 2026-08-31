# Phase 0 Specification Survey Report: Antigravity MCP Server, MicroVM Sandbox & Verification Harness

**Date**: 2026-08-29  
**Agent**: `spec_miner_survey_3`  
**Milestone**: Phase 0 (Survey & Scope Mapping)  
**Corpus / Workspace**: `c:\Users\info\OneDrive\Dokument\GitHub\fart`  

---

## Executive Summary

This report establishes the technical foundation, architecture specifications, packaging requirements, and verification harness (Requirement R5) for the **Antigravity MCP Server and Customization Plugin**. The system provides hardware-isolated and local fallback code execution via E2B Firecracker microVMs and an autonomous background service worker daemon for agentic workflows.

The findings synthesize authoritative architectural guidance from `Öppen Källkod För Virtuella Maskiner.md`, the requirements defined in `ORIGINAL_REQUEST.md`, standard Model Context Protocol (MCP) JSON-RPC specifications, and enterprise testing methodologies.

---

## 1. Virtual Machine & Isolation Architecture Analysis

Based on `Öppen Källkod För Virtuella Maskiner.md` and cloud virtualization best practices:

### 1.1 The Dual-Layer Execution Stack for Autonomous A(S)GI
Modern agentic AI architectures require dynamic runtime code generation (e.g., Hugging Face `smolagents` `CodeAgent` or Antigravity tool calling). Agents "think in code" by composing functions, importing packages, and orchestrating execution graphs in real time.
- **Top Layer**: Agent reasoning, prompt interpretation, tool dispatch, and static validation (AST security verification).
- **Bottom Layer**: Machine virtualization and isolated compute substrates (E2B Firecracker microVMs, Kata Containers, WebAssembly, or isolated fallback sub-processes).

### 1.2 Isolation Platform Taxonomy & Comparative Trade-offs

| Isolation Technology | Isolation Level | Cold Start Latency | Kernel / Runtime Architecture | State & Snapshot Capabilities | Optimal Use Case in System |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **E2B Firecracker MicroVM** | Hardware-level (KVM) | ~150–200 ms | Dedicated minimal Linux kernel per microVM instance | Full memory & rootfs snapshots (`createSnapshot`), pause/resume in memory | **Primary production execution engine** for untrusted agent code & complex AI workloads. |
| **Local Fallback Sandbox (Restricted AST + Process)** | Process & AST constraint | < 10 ms | Shared host OS kernel, restricted subprocess environment | Transient process memory or in-process REPL dictionary | **Zero-dependency offline fallback** when E2B API keys or internet access are unavailable. |
| **Kata Containers (K8s CRI)** | Hardware-level (KVM/QEMU) | 1–3 s | Dedicated guest Linux kernel per Pod | Kubernetes Persistent Volumes (PV/PVC) | Enterprise self-hosted cluster deployment. |
| **KubeVirt** | Full VM Virtualization | 5–15 s | Full OS VM managed as K8s CRD | Standard VM disk image snapshots | Complex OS environments, GPU pass-through. |
| **WebAssembly (WasmEdge / WAMR)** | Bytecode Sandbox | < 10 ms | Application runtime sandbox (no guest OS kernel) | Static Wasm context & linear memory export | Ultra-low latency, deterministic background service workers. |

### 1.3 Security Boundary & Threat Model
1. **Host Compromise Risk (CVE-2025-9959 lesson)**: Pure AST validation (like default `smolagents` `LocalPythonExecutor`) does not provide an OS-level security boundary. Malicious code can exploit Python introspection (`__class__.__bases__`), `ctypes`, or memory corruption to escape AST filters.
2. **Defense-in-Depth Architecture**:
   - **Tier A (Static AST Analysis)**: Filter forbidden AST nodes (`Import`, `ImportFrom`, `Call` to `eval`/`exec`/`open`/`__import__`) before running local fallback code.
   - **Tier B (Subprocess & Quota Isolation)**: Execute local code in a separate subprocess with strict timeout limits (`subprocess.run(..., timeout=N)`), restricted environment variables, and memory bounds.
   - **Tier C (MicroVM Hardware Isolation)**: For E2B mode, execute code inside a dedicated Firecracker microVM where kernel-level isolation (KVM) guarantees complete host decoupling.
   - **Tier D (Network & File System Sandboxing)**: Restrict file system write access to transient scratch directories (`/tmp` or dedicated sandbox workspace) and enforce network egress policies.

---

## 2. Project Packaging, Environment & Directory Layout

### 2.1 Python Environment & Tooling Specification
- **Python Version**: `>= 3.10` (Targeting host environment: `Python 3.11.9`)
- **Packaging Standard**: Modern PEP 517/518/621 `pyproject.toml` with `setuptools` or `hatchling`.
- **Installed Dependencies on Host**:
  - `pydantic` (`>=2.0`, currently `2.13.4`)
  - `pytest` (`>=8.0`, currently `9.1.1`)
  - `typing_extensions` (`4.16.0`)
- **Required Core Dependencies**:
  - `pydantic>=2.0.0` — Strict data validation and schema generation for MCP tools and worker jobs.
  - `croniter>=2.0.0` (with built-in pure-Python fallback scheduler) — Standard 5-field cron parsing.
  - `e2b>=1.0.0` / `e2b-code-interpreter>=1.0.0` (with clean mock/fallback when offline) — Firecracker SDK.
  - `typing-extensions>=4.8.0` — Advanced type hints.

### 2.2 Standard Directory Layout Specification

```
c:\Users\info\OneDrive\Dokument\GitHub\fart/
├── pyproject.toml                         # Project metadata, dependencies, build configuration
├── README.md                              # High-level architecture and quickstart guide
├── src/
│   └── antigravity_mcp/
│       ├── __init__.py                    # Top-level package exports
│       ├── config.py                      # Global configuration (E2B keys, timeouts, sandbox defaults)
│       ├── sandbox/
│       │   ├── __init__.py                # Sandbox package exports
│       │   ├── base.py                    # BaseSandbox ABC, ExecutionResult, ExecutionArtifact
│       │   ├── e2b_sandbox.py             # E2B Firecracker MicroVM driver
│       │   ├── fallback_sandbox.py        # AST-validated local fallback sandbox
│       │   ├── repl_manager.py            # Persistent REPL state tracking engine
│       │   └── security.py                # AST security parser, whitelist verifier, code sanitizer
│       ├── mcp/
│       │   ├── __init__.py                # MCP package exports
│       │   ├── server.py                  # MCP Server (JSON-RPC 2.0 stdio engine)
│       │   ├── protocols.py               # MCP protocol models (JsonRpcRequest, ToolDefinition)
│       │   └── tools.py                   # MCP tool handlers (create_sandbox, execute_code, etc.)
│       ├── worker/
│       │   ├── __init__.py                # Worker package exports
│       │   ├── daemon.py                  # Service Worker Daemon process orchestrator
│       │   ├── scheduler.py               # Cron & timer scheduler engine
│       │   ├── job.py                     # Job definitions, state transitions, execution history
│       │   └── runner.py                  # Sandboxed job execution wrapper
│       └── plugin/
│           ├── __init__.py                # Plugin package exports
│           └── manifest.py                # Plugin metadata, skill discovery, and configuration
├── plugins/
│   └── antigravity-code-sandbox/
│       ├── plugin.json                    # Antigravity Plugin manifest
│       └── skills/
│           └── code-sandbox/
│               └── SKILL.md               # Antigravity progressive disclosure skill definition
├── tests/
│   ├── __init__.py
│   ├── conftest.py                        # Pytest fixtures (mocks, temp sandboxes, clients)
│   ├── test_tier1_features/               # Tier 1: Feature Coverage (>=5 tests per component)
│   │   ├── test_sandbox_e2b.py
│   │   ├── test_sandbox_fallback.py
│   │   ├── test_repl_state.py
│   │   ├── test_mcp_tools.py
│   │   ├── test_plugin_skill.py
│   │   └── test_worker_daemon.py
│   ├── test_tier2_boundaries/             # Tier 2: Boundary & Corner Cases
│   │   ├── test_ast_security.py
│   │   ├── test_timeouts_limits.py
│   │   ├── test_invalid_cron.py
│   │   ├── test_disconnected_stdio.py
│   │   └── test_missing_credentials.py
│   ├── test_tier3_combinations/           # Tier 3: Cross-Feature Combinations
│   │   ├── test_mcp_to_sandbox.py
│   │   ├── test_worker_to_sandbox.py
│   │   └── test_fallback_transitions.py
│   ├── test_tier4_agent_workloads/        # Tier 4: Real-world Agent Workload Scenarios
│   │   ├── test_repl_data_analysis.py
│   │   ├── test_cron_health_monitoring.py
│   │   └── test_artifact_generation.py
│   └── e2e/
│       └── test_end_to_end.py             # Complete integrated end-to-end test suite
└── demo.py                                # Runnable End-to-End demonstration script
```

---

## 3. Features Discovered

| # | Category | Feature | Description | Inputs | Outputs | Error Behavior | Discovered Via |
|---|----------|---------|-------------|--------|---------|----------------|----------------|
| 1 | Sandbox Engine | `create_sandbox` | Provisions a new Firecracker microVM sandbox (E2B) or local fallback sandbox. | `template: Optional[str]`, `timeout: int`, `mode: Optional[str]` ("e2b"\|"fallback"\|"auto") | `sandbox_id: str`, `mode: str`, `status: str`, `created_at: str` | Raises `SandboxProvisionError` if resource limits exceeded; falls back cleanly if API key missing. | `ORIGINAL_REQUEST.md` (R1), `Öppen Källkod För Virtuella Maskiner.md` |
| 2 | Sandbox Engine | `execute_code` | Executes Python code inside the active sandbox environment and captures outputs. | `sandbox_id: str`, `code: str`, `timeout: Optional[int]`, `session_id: Optional[str]` | `stdout: str`, `stderr: str`, `exit_code: int`, `artifacts: List[Dict]`, `execution_time_ms: float` | Returns non-zero `exit_code` with `stderr` on Python exceptions; raises `ExecutionTimeoutError` on timeout. | `ORIGINAL_REQUEST.md` (R1), `Öppen Källkod För Virtuella Maskiner.md` |
| 3 | Sandbox Engine | `destroy_sandbox` | Terminates and purges the microVM / local sandbox resources, releasing memory and file handles. | `sandbox_id: str` | `success: bool`, `destroyed_at: str` | Returns `false` or raises `SandboxNotFoundError` if sandbox ID is invalid. | `ORIGINAL_REQUEST.md` (R1, R2) |
| 4 | Sandbox Engine | `pause_sandbox` / `resume_sandbox` | Freezes/resumes the microVM execution state or serializes session state to conserve resources. | `sandbox_id: str` | `status: str` ("paused"\|"running"), `timestamp: str` | Raises `SandboxStateError` if sandbox is already destroyed or in incompatible state. | `Öppen Källkod För Virtuella Maskiner.md` §1.2 |
| 5 | Sandbox Engine | `create_snapshot` | Takes an atomic point-in-time snapshot of the sandbox filesystem and memory state. | `sandbox_id: str`, `snapshot_name: Optional[str]` | `snapshot_id: str`, `size_bytes: int`, `created_at: str` | Raises `SnapshotError` if sandbox is busy or snapshot storage is unavailable. | `Öppen Källkod För Virtuella Maskiner.md` §1.2 |
| 6 | REPL State | `repl_execute` | Executes code within a stateful REPL session, preserving variables, imports, and functions across turns. | `sandbox_id: str`, `code: str`, `reset_session: bool` | `stdout: str`, `stderr: str`, `result_value: Any`, `variables_defined: List[str]` | Captures runtime traceback in `stderr`, preserves existing state prior to failed step. | `ORIGINAL_REQUEST.md` (R1), `Öppen Källkod För Virtuella Maskiner.md` §2 |
| 7 | REPL State | `reset_repl` | Clears all in-memory variables and state in the REPL session without destroying the microVM container. | `sandbox_id: str` | `status: str` ("reset_complete"), `cleared_symbols: int` | Raises `SandboxNotFoundError` if sandbox does not exist. | `ORIGINAL_REQUEST.md` (R1) |
| 8 | Security | `ast_validate_code` | Parses code into an AST tree and verifies against unauthorized imports, dunder traversal, and dangerous calls. | `code: str`, `allowed_imports: List[str]` | `is_safe: bool`, `violations: List[str]` | Returns `is_safe=False` with detailed violation descriptions (e.g., `ProhibitedImport: os`). | `Öppen Källkod För Virtuella Maskiner.md` §1.1 |
| 9 | MCP Server | `mcp_stdio_server` | Implements the Model Context Protocol JSON-RPC 2.0 transport over stdin/stdout. | Stdin stream of JSON-RPC requests (`initialize`, `tools/list`, `tools/call`) | Stdout stream of JSON-RPC responses | Returns JSON-RPC standard error objects (`-32600 Invalid Request`, `-32601 Method not found`). | `ORIGINAL_REQUEST.md` (R2) |
| 10 | MCP Server | `tools/list` | Exposes full catalog of Antigravity sandbox and worker management tools with JSON Schema definitions. | `None` (or cursor pagination) | `tools: List[ToolDefinition]` containing `name`, `description`, `inputSchema` | Returns standard MCP error response if server is uninitialized. | `ORIGINAL_REQUEST.md` (R2) |
| 11 | MCP Server | `tools/call` | Dispatches execution requests to corresponding sandbox, snapshot, or worker routines. | `name: str`, `arguments: Dict[str, Any]` | `content: List[TextContent | ImageContent]`, `isError: bool` | Returns `isError=True` with formatted error message in `content` if tool execution fails. | `ORIGINAL_REQUEST.md` (R2) |
| 12 | Plugin Suite | `plugin_manifest` | Standardized Antigravity plugin manifest (`plugin.json`) declaring capabilities, MCP server entrypoint, and config. | File path `plugins/.../plugin.json` | Parsed `PluginManifest` schema object | Fails schema validation if required fields (`name`, `version`, `mcpServers`) are missing. | `ORIGINAL_REQUEST.md` (R3) |
| 13 | Plugin Suite | `skill_definition` | Antigravity `SKILL.md` defining triggers, workflows, and progressive disclosure guidelines for code execution. | File path `plugins/.../SKILL.md` | Structured markdown with YAML frontmatter | Logs warning if skill triggers are missing or syntax is invalid. | `ORIGINAL_REQUEST.md` (R3) |
| 14 | Worker Daemon | `spawn_worker_daemon` | Initializes the background service worker manager thread/process with job queue and scheduler. | `config: WorkerConfig` (e.g. max_concurrency, poll_interval) | `daemon_id: str`, `status: str` ("running"), `active_jobs: int` | Raises `DaemonStartupError` if port/resource is locked. | `ORIGINAL_REQUEST.md` (R4) |
| 15 | Worker Daemon | `schedule_job` | Schedules a recurring (cron) or one-shot (timer) autonomous task to execute code in sandboxes. | `job_id: Optional[str]`, `cron: Optional[str]`, `delay_seconds: Optional[float]`, `code: str`, `sandbox_id: Optional[str]` | `job_id: str`, `next_run_at: str`, `job_type: str` | Raises `InvalidCronError` or `InvalidIntervalError` on malformed schedule specs. | `ORIGINAL_REQUEST.md` (R4) |
| 16 | Worker Daemon | `get_job_status` / `list_jobs` | Retrieves current status, metrics, and past execution logs for registered background jobs. | `job_id: Optional[str]`, `filter_status: Optional[str]` | `jobs: List[JobStatus]` (with `execution_history`, `last_run`, `next_run`, `runs_completed`) | Returns empty list if no matching jobs found; raises error if specific job ID is invalid. | `ORIGINAL_REQUEST.md` (R4) |
| 17 | Worker Daemon | `cancel_job` | Cancels a scheduled or currently running background worker job and releases associated sandboxes. | `job_id: str` | `success: bool`, `cancelled_at: str` | Returns `false` or raises `JobNotFoundError` if job ID does not exist. | `ORIGINAL_REQUEST.md` (R4) |
| 18 | Verification | `e2e_verification_harness` | Automated test suite verifying sandbox provisioning, safety, fallback, MCP stdio, and worker lifecycle. | Test suite runner CLI (`pytest -v tests/`) | Pytest test results report, exit code 0 on 100% pass | Fails with detailed failure trace and diagnostic assertion errors. | `ORIGINAL_REQUEST.md` (R5) |
| 19 | Verification | `runnable_demo` | Interactive CLI demo script showcasing sandbox creation, REPL execution, worker scheduling, and teardown. | Execution command (`python demo.py`) | Formatted console output showing step-by-step verification and summary JSON | Exits with code 1 if any pipeline step fails. | `ORIGINAL_REQUEST.md` (R5) |

---

## 4. Edge Cases & Boundary Conditions

| # | Feature / Boundary | Input / Condition | Expected / Observed System Behavior |
|---|-------------------|-------------------|--------------------------------------|
| 1 | Sandbox Execution | Empty code string (`""` or `"   \n\t"`) | Returns `stdout=""`, `stderr=""`, `exit_code=0`, `execution_time_ms < 5`. No container crash or hanging process. |
| 2 | Sandbox Execution | Python syntax error (e.g., `def broken_func(:`) | Returns `exit_code=1`, structured `stderr` containing `SyntaxError: invalid syntax` with line number. REPL state remains intact. |
| 3 | Sandbox Execution | Infinite loop (e.g., `while True: pass`) with `timeout=2` | Execution is forcefully terminated after 2.0 seconds. Returns `exit_code=124` / `ExecutionTimeoutError`, resources reclaimed. |
| 4 | Fallback Sandbox | AST Forbidden Import (e.g., `import os`, `import subprocess`) | AST validator blocks execution before running. Returns `is_safe=False`, `stderr="ASTSecurityViolation: import of 'os' is prohibited in fallback sandbox"`. |
| 5 | Fallback Sandbox | Dunder Introspection Breakout (e.g., `().__class__.__bases__[0].__subclasses__()`) | AST security visitor detects attribute access to `__class__`/`__subclasses__` or private dunders and rejects with `SecurityViolation`. |
| 6 | Fallback Sandbox | Dynamic evaluation call (e.g., `eval("1 + 1")` or `exec("x=1")`) | AST validator detects `Call` to forbidden builtin functions (`eval`, `exec`, `__import__`, `open`) and rejects execution. |
| 7 | Fallback Sandbox | Memory exhaustion attempt (e.g., `x = 'A' * (10**9)`) | Memory limits or subprocess bounds catch memory error, returns `MemoryError` or process termination without crashing host. |
| 8 | E2B Sandbox | Missing / Invalid `E2B_API_KEY` | System detects missing/invalid key, logs diagnostic warning, and automatically falls back to `FallbackSandbox` with full REPL support. |
| 9 | REPL State | Sequential execution variable dependency (`x = 10` then `print(x * 2)`) | Step 2 correctly reads `x=10` from Step 1 context and outputs `20`. |
| 10 | REPL State | Runtime exception during step 2 (`y = 1 / 0`) followed by step 3 (`print(x)`) | Step 2 outputs `ZeroDivisionError` to `stderr`. Step 3 executes successfully and prints `10` (previous state preserved despite intermediate error). |
| 11 | REPL State | Function definition and redefinition across multiple turns | Functions defined in earlier turns remain callable in subsequent turns; re-defining a function smoothly overwrites previous definition. |
| 12 | MCP Server | Malformed JSON-RPC message on stdin (e.g., `{"jsonrpc": "2.0", "method": "create_sandbox"` without closing bracket) | MCP server returns standard JSON-RPC parse error `{"jsonrpc": "2.0", "error": {"code": -32700, "message": "Parse error"}, "id": null}` without dropping connection. |
| 13 | MCP Server | Unknown MCP method call (e.g., `method: "unsupported_tool"`) | Returns JSON-RPC error `{"code": -32601, "message": "Method not found"}`. |
| 14 | MCP Server | Tool call with invalid schema arguments (e.g., `execute_code` with `timeout="not_a_number"`) | Pydantic validation fails before execution, returns `isError=True` with schema validation error details. |
| 15 | MCP Server | Stdio pipe disconnect / EOF on stdin | Server loop cleanly detects EOF, shuts down active sandboxes, stops worker threads, and exits with code 0. |
| 16 | Worker Daemon | Invalid Cron syntax (e.g., `"99 99 * * *"` or `"every 5 minutes"`) | Scheduler rejects job registration with `InvalidCronExpressionError`, descriptive diagnostic message returned. |
| 17 | Worker Daemon | Sub-second timer / High frequency bursts (e.g., `delay_seconds=0.01`) | Scheduler handles minimal delay, triggers task accurately, prevents thread pool starvation or recursion overflow. |
| 18 | Worker Daemon | Worker task throws unhandled exception during background run | Daemon captures exception in job's execution history log (`status="failed"`, `error_traceback=...`), daemon continues scheduling subsequent jobs. |
| 19 | Worker Daemon | Sandbox destroyed while worker job is queued | Worker cleanly checks sandbox availability before run; if missing, recreates sandbox or marks job run failed with clear cause. |
| 20 | Concurrency | Simultaneous execution requests to the same sandbox session | Sandbox session employs thread-safe execution locks (`threading.Lock` / `asyncio.Lock`) ensuring serial execution without corrupting state. |

---

## 5. Complete Test Suite Architecture & Verification Harness (R5)

Requirement R5 demands a comprehensive automated test suite (`pytest`) verifying all system capabilities across 4 rigorous tiers plus an end-to-end runnable demo script.

### 5.1 Tier 1: Feature Coverage (≥5 Tests per Component)

#### Subsystem 1: Sandbox Engine (`tests/test_tier1_features/test_sandbox_e2b.py` & `test_sandbox_fallback.py`)
1. **`test_sandbox_creation`**: Verifies sandbox initialization, returns unique `sandbox_id`, initial state `RUNNING`, and proper mode annotation ("e2b" or "fallback").
2. **`test_sandbox_execute_basic_python`**: Runs basic arithmetic (`print(2 + 2)`) and asserts `stdout == "4\n"`, `exit_code == 0`, `stderr == ""`.
3. **`test_sandbox_execute_multiline_script`**: Runs multi-line script with standard library imports (`import json, math; print(json.dumps({'pi': round(math.pi, 2)}))`), asserts valid JSON output.
4. **`test_sandbox_stderr_capture`**: Runs code raising standard exceptions (`raise ValueError("custom error")`), asserts `exit_code != 0`, `stderr` contains `"ValueError: custom error"`.
5. **`test_sandbox_destroy_cleanup`**: Verifies `destroy_sandbox()` terminates the runtime, releases memory/locks, and subsequent execution requests to destroyed ID fail gracefully.
6. **`test_sandbox_auto_mode_fallback`**: Verifies that when mode is `auto` and E2B is unavailable, engine automatically routes to `FallbackSandbox`.

#### Subsystem 2: Persistent REPL Session (`tests/test_tier1_features/test_repl_state.py`)
1. **`test_repl_variable_persistence`**: Step 1 sets `x = 100`; Step 2 runs `print(x + 23)`; asserts `stdout == "123\n"`.
2. **`test_repl_function_persistence`**: Step 1 defines `def add(a, b): return a + b`; Step 2 calls `print(add(5, 7))`; asserts `stdout == "12 Moulding..." -> "12\n"`.
3. **`test_repl_import_persistence`**: Step 1 executes `import math`; Step 2 runs `print(math.sqrt(16))`; asserts `stdout == "4.0\n"`.
4. **`test_repl_state_isolation_between_sessions`**: Session A sets `var_a = 'alice'`; Session B sets `var_b = 'bob'`; asserts Session B cannot read `var_a`.
5. **`test_repl_reset_state`**: Step 1 sets `temp_val = 99`; Step 2 calls `reset_repl()`; Step 3 evaluates `print(temp_val)` and asserts `NameError` in `stderr`.

#### Subsystem 3: MCP Protocol & Tools (`tests/test_tier1_features/test_mcp_tools.py`)
1. **`test_mcp_initialize_handshake`**: Sends `initialize` request; asserts protocol version, server capabilities (`tools: {}`), and server info.
2. **`test_mcp_tools_list_catalog`**: Sends `tools/list`; asserts tool catalog contains all required tools (`create_sandbox`, `execute_code`, `destroy_sandbox`, `manage_snapshot`, `spawn_worker`, `schedule_job`, `get_job_status`).
3. **`test_mcp_create_sandbox_tool_call`**: Sends `tools/call` for `create_sandbox`; asserts valid ToolResult text with JSON containing `sandbox_id`.
4. **`test_mcp_execute_code_tool_call`**: Sends `tools/call` for `execute_code` with valid Python code; asserts ToolResult containing stdout and exit code.
5. **`test_mcp_manage_snapshot_tool_call`**: Sends `tools/call` for `manage_snapshot` (pause, resume, snapshot); asserts valid status response.
6. **`test_mcp_tool_call_validation_error`**: Sends `tools/call` with invalid arguments; asserts `isError == True` with descriptive validation error.

#### Subsystem 4: Antigravity Plugin & Skill Suite (`tests/test_tier1_features/test_plugin_skill.py`)
1. **`test_plugin_manifest_schema`**: Loads `plugins/antigravity-code-sandbox/plugin.json`; validates schema fields (`name`, `version`, `description`, `mcpServers`).
2. **`test_skill_markdown_frontmatter`**: Loads `plugins/antigravity-code-sandbox/skills/code-sandbox/SKILL.md`; validates YAML frontmatter (`name`, `description`).
3. **`test_skill_trigger_coverage`**: Verifies `SKILL.md` contains trigger keywords (e.g., "execute python", "run code", "sandbox", "microvm", "worker").
4. **`test_skill_parameter_consistency`**: Asserts parameters documented in `SKILL.md` match MCP tool schema properties exactly.
5. **`test_plugin_discovery_and_registration`**: Asserts plugin manifest discovery helper detects and registers all skills in plugin directories.

#### Subsystem 5: Worker Daemon & Scheduler (`tests/test_tier1_features/test_worker_daemon.py`)
1. **`test_worker_daemon_start_stop`**: Starts worker daemon thread; asserts `daemon.is_running() == True`; stops daemon and asserts clean shutdown.
2. **`test_schedule_one_shot_timer_job`**: Schedules a job with `delay_seconds=0.1`; asserts job executes and updates status to `COMPLETED`.
3. **`test_schedule_recurring_cron_job`**: Schedules a cron job with `cron="* * * * *"`; asserts `next_run_at` is calculated correctly.
4. **`test_worker_job_execution_history`**: Executes job; asserts execution history log records start time, end time, exit code, and stdout.
5. **`test_cancel_scheduled_job`**: Schedules a future job; calls `cancel_job(job_id)`; asserts job status changes to `CANCELLED` and never triggers.

---

### 5.2 Tier 2: Boundary & Corner Cases

Test file location: `tests/test_tier2_boundaries/`
1. **`test_ast_security.py`**:
   - Tests blocked modules: `os`, `sys`, `subprocess`, `socket`, `pty`, `shutil`, `builtins`.
   - Tests blocked functions: `eval()`, `exec()`, `open()`, `__import__()`, `getattr()` on dunders.
   - Tests dunder escape attempts: `().__class__.__base__.__subclasses__()`.
2. **`test_timeouts_limits.py`**:
   - Tests infinite loop termination (`while True: pass`) at 1-second timeout.
   - Tests sleep timeout (`import time; time.sleep(10)`) at 1-second timeout.
   - Tests massive stdout buffer limit protection (e.g., printing 100MB of text).
3. **`test_invalid_cron.py`**:
   - Tests invalid field counts (`* * *`), out-of-range values (`60 * * * *`), invalid letters (`abc * * * *`).
   - Tests negative timer delays (`delay_seconds = -5`).
4. **`test_disconnected_stdio.py`**:
   - Tests handling of unexpected EOF on stdin.
   - Tests malformed JSON payload handling without crashing the server loop.
   - Tests partial JSON chunks streamed across multiple buffer reads.
5. **`test_missing_credentials.py`**:
   - Tests system initialization with `E2B_API_KEY=""` or invalid keys.
   - Verifies transparent fallback to local AST sandbox with warning log.

---

### 5.3 Tier 3: Cross-Feature Combinations

Test file location: `tests/test_tier3_combinations/`
1. **`test_mcp_to_sandbox.py`**:
   - Full MCP protocol workflow: `initialize` -> `tools/call(create_sandbox)` -> `tools/call(execute_code, step 1: defs)` -> `tools/call(execute_code, step 2: calls)` -> `tools/call(destroy_sandbox)`.
2. **`test_worker_to_sandbox.py`**:
   - Worker daemon schedules a recurring job that executes Python code inside a dedicated sandbox on each tick, logging execution results to history.
3. **`test_fallback_transitions.py`**:
   - Verifies explicit dynamic switching between `e2b` mode and `fallback` mode within the same MCP server lifecycle.
4. **`test_worker_snapshot_pipeline.py`**:
   - Worker executes code -> manages snapshot -> pauses sandbox -> resumes on next event -> executes next code step.

---

### 5.4 Tier 4: Real-world Agent Workload Scenarios

Test file location: `tests/test_tier4_agent_workloads/`
1. **`test_repl_data_analysis.py` (Multi-turn Data Analysis)**:
   - **Turn 1**: Load/generate synthetic tabular data (records dictionary), calculate mean, median, and variance.
   - **Turn 2**: Filter records meeting threshold criteria, generate summary dataframe-like structure.
   - **Turn 3**: Generate visual summary / ASCII / Base64 chart representation and return structured artifact.
2. **`test_cron_health_monitoring.py` (Background Health Check Worker)**:
   - Registers a periodic worker running every second checking system metrics (disk/memory mock).
   - Simulates 3 successful cycles followed by 1 simulated alert condition.
   - Asserts worker captures alert in log and marks state accurately.
3. **`test_artifact_generation.py` (Autonomous Artifact Pipeline)**:
   - Code execution writes a file artifact (`output.json` or `report.csv`).
   - Sandbox captures generated artifact file, encodes it, and returns structured `ExecutionArtifact` metadata in the result.

---

### 5.5 Runnable End-to-End Demo Script Specification (`demo.py`)

The project root must include a standalone, runnable script `demo.py` that can be executed directly via `python demo.py`.

#### Demo Workflow Steps:
1. **Banner & Initialization**: Prints system configuration, detected execution mode (`E2B Firecracker` or `Local Fallback Sandbox`), and active Python runtime.
2. **Sandbox Creation**: Programmatically invokes sandbox engine to create a secure sandbox session.
3. **Multi-Step REPL Execution**:
   - Step A: Injects data generation logic and helper functions into the REPL.
   - Step B: Calls helper functions and performs statistical calculations.
   - Step C: Generates a structured artifact and prints formatted table outputs.
4. **Worker Daemon Orchestration**:
   - Launches the background `WorkerDaemon`.
   - Schedules a 1-second one-shot job and a recurring heartbeat task.
   - Awaits execution completion and displays job execution histories.
5. **Resource Teardown**:
   - Cancels scheduled jobs and stops the worker daemon.
   - Destroys sandbox instances and cleans up temporary files.
6. **Summary & Verification Matrix**:
   - Outputs a clean JSON summary verification report showing 100% success across all components.

---

## 6. Synthesis & Strategic Recommendations for Implementation

1. **Self-Contained Fallback**: Ensure the `FallbackSandbox` has zero external cloud dependencies and functions cleanly in air-gapped or non-E2B environments, while strictly enforcing AST security and subprocess timeouts.
2. **Standard-Compliant MCP Protocol**: Implement JSON-RPC 2.0 over stdio without external heavyweight frameworks, allowing seamless integration with any MCP client (Claude Desktop, Cursor, Antigravity).
3. **Robust Scheduling**: Use a pure-Python cron scheduler with fallback algorithms to eliminate OS-specific cron dependencies.
4. **Comprehensive Test Suite**: Organize tests into the 4-tier directory hierarchy with automated pytest execution passing 100%.

---
