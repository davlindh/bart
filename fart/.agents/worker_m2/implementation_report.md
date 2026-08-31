# Milestone 2 Implementation Report: Antigravity MCP Server Subsystem

**Document Version**: 1.0.0  
**Milestone**: M2 (Antigravity MCP Server)  
**Author**: Worker Agent (`worker_m2`)  
**Target Package**: `src/antigravity/mcp/`  
**Date**: 2026-08-29  

---

## 1. Executive Summary

Milestone 2 delivers the production-ready Model Context Protocol (MCP) server for the Antigravity platform. It exposes a standard JSON-RPC 2.0 interface over `stdio` transport, complete with strict separation of communication channels (stdout strictly reserved for protocol framing, stderr for server logs and diagnostics).

The MCP server exposes the full suite of 7 lifecycle, execution, snapshot, and background worker tools integrating with `SandboxManager` (R1) and `ServiceWorkerDaemon` (R4), backed by Pydantic argument validation models and comprehensive error handling schemas.

---

## 2. Component Architecture & Implemented Modules

### 2.1 Protocol Framing & Serialization (`src/antigravity/mcp/protocol.py`)
- **JSON-RPC 2.0 Compliance**: Standard framing for requests, responses, notifications, and error objects.
- **Error Code Domains**:
  - Standard JSON-RPC 2.0 codes: `PARSE_ERROR` (`-32700`), `INVALID_REQUEST` (`-32600`), `METHOD_NOT_FOUND` (`-32601`), `INVALID_PARAMS` (`-32602`), `INTERNAL_ERROR` (`-32603`).
  - Antigravity Domain codes: `SANDBOX_NOT_FOUND` (`-32000`), `EXECUTION_TIMEOUT` (`-32001`), `AST_SECURITY_VIOLATION` (`-32002`), `E2B_PROVIDER_ERROR` (`-32003`), `WORKER_SCHEDULE_ERROR` (`-32004`), `SNAPSHOT_CORRUPTED` (`-32005`), `TOOL_ERROR` (`-32006`).
- **Stdio Transport Isolation**:
  - `write_stdout(payload)`: Encodes JSON-RPC messages to newline-delimited strings, written directly to `sys.stdout` and flushed.
  - `log_stderr(message)`: Writes all diagnostic traces and logging strictly to `sys.stderr` to avoid corrupting protocol streams.

### 2.2 Schema Models & Tool Declarations (`src/antigravity/mcp/schemas.py`)
- **Pydantic Validation**: Models for client initialization (`InitializeParams`, `InitializeResult`), server capabilities (`ServerCapabilities`, `ServerInfo`), tool call parameters and responses (`ToolCallParams`, `ToolCallResult`, `TextContent`, `ImageContent`).
- **Pydantic Tool Input Models**:
  - `CreateSandboxInput`: Validates backend mode (`auto`, `local`, `e2b`), execution template, lifetime timeout, and environment variables.
  - `ExecuteCodeInput`: Validates `sandbox_id`, code body, language, execution timeout, and REPL persistence flag.
  - `PauseSandboxInput`: Validates sandbox ID and optional auto-snapshot flag.
  - `ResumeSandboxInput`: Validates sandbox ID and updated lifetime timeout.
  - `DestroySandboxInput`: Validates sandbox ID and force termination.
  - `ManageSnapshotInput`: Validates action (`create`, `restore`, `list`, `delete`), snapshot IDs, and checkpoint names.
  - `SpawnWorkerInput`: Validates worker name, trigger type (`cron`, `timer`), schedule spec, code payload, and max iterations.
- **Tool Schema Catalog (`TOOL_SCHEMAS`)**: Declarative JSON Schema definitions for all 7 tools published via `tools/list`.

### 2.3 Tool Registry & Handlers (`src/antigravity/mcp/tools.py`)
- **`MCPToolRegistry`**:
  - Connects tool invocations to active `SandboxManager` and `ServiceWorkerDaemon` instances.
  - Dispatches calls with strict schema validation and structured tool error handling (`isError` flag with JSON payload).
  - Handles auto-provisioning and sandbox resolution gracefully.
- **Exposed 7 MCP Tools**:
  1. `create_sandbox`: Provisions Firecracker or Local sandbox via `SandboxManager`.
  2. `execute_code`: Executes code statefully across REPL turns, capturing stdout, stderr, exit code, execution time, and base64 artifacts.
  3. `pause_sandbox`: Freezes sandbox state and optionally creates state snapshot.
  4. `resume_sandbox`: Unfreezes execution context and refreshes lifetime timeout.
  5. `destroy_sandbox`: Terminates sandbox microVM/process and cleans temporary assets.
  6. `manage_snapshot`: Checkpoints, restores, lists, or deletes execution memory snapshots.
  7. `spawn_worker`: Registers background cron/timer tasks with `ServiceWorkerDaemon`.

### 2.4 MCP Stdio Server (`src/antigravity/mcp/server.py`)
- **`AntigravityMCPServer`**:
  - Async event loop processing stdio messages non-blockingly (`run_stdio`).
  - Supports `initialize`, `notifications/initialized`, `ping`, `tools/list`, and `tools/call`.
  - Provides both asynchronous (`handle_request_async`, `dispatch`) and synchronous (`handle_request`) dispatch interfaces for client sessions.

### 2.5 CLI Runner & Entry Point (`src/antigravity/mcp/runner.py`)
- **Entry Point `antigravity-mcp-server`**:
  - CLI argument parser supporting `--mode`, `--default-timeout`, and `--log-level`.
  - Logging configured exclusively on `sys.stderr`.
  - Async server lifecycle management with cleanup of all sandboxes on exit.

---

## 3. Verification & Test Results

The implementation was validated against all MCP test tiers:
- **Tier 1 (Feature Coverage)**: `tests/tier1_features/test_mcp_features.py` (6 tests: handshake, catalog, sandbox create/destroy, code execution, snapshot management, worker spawning).
- **Tier 2 (Boundary Cases)**: `tests/tier2_boundaries/test_mcp_protocol_boundaries.py` (6 tests: unknown RPC methods, unknown tools, missing required arguments, invalid IDs, ping/pong, sequential RPC requests).
- **Tier 3 (Cross-Feature Pipeline)**: `tests/tier3_cross_feature/test_mcp_sandbox_pipeline.py` (1 end-to-end test verifying multi-turn REPL persistence, snapshot creation, and sandbox cleanup through the MCP protocol).

### Test Summary:
```
tests/tier1_features/test_mcp_features.py::TestMcpFeatures::test_mcp_initialize_handshake PASSED
tests/tier1_features/test_mcp_features.py::TestMcpFeatures::test_mcp_tools_list_exposes_all_required_tools PASSED
tests/tier1_features/test_mcp_features.py::TestMcpFeatures::test_mcp_create_and_destroy_sandbox_tools PASSED
tests/tier1_features/test_mcp_features.py::TestMcpFeatures::test_mcp_execute_code_tool_call PASSED
tests/tier1_features/test_mcp_features.py::TestMcpFeatures::test_mcp_manage_snapshot_tool_call PASSED
tests/tier1_features/test_mcp_features.py::TestMcpFeatures::test_mcp_spawn_worker_tool_call PASSED
tests/tier2_boundaries/test_mcp_protocol_boundaries.py::TestMcpProtocolBoundaries::test_unknown_method_call_returns_method_not_found PASSED
tests/tier2_boundaries/test_mcp_protocol_boundaries.py::TestMcpProtocolBoundaries::test_call_unknown_tool_returns_error PASSED
tests/tier2_boundaries/test_mcp_protocol_boundaries.py::TestMcpProtocolBoundaries::test_execute_code_missing_required_arguments PASSED
tests/tier2_boundaries/test_mcp_protocol_boundaries.py::TestMcpProtocolBoundaries::test_destroy_sandbox_with_invalid_id PASSED
tests/tier2_boundaries/test_mcp_protocol_boundaries.py::TestMcpProtocolBoundaries::test_ping_pong_health_check PASSED
tests/tier2_boundaries/test_mcp_protocol_boundaries.py::TestMcpProtocolBoundaries::test_batch_or_sequential_rpc_requests PASSED
tests/tier3_cross_feature/test_mcp_sandbox_pipeline.py::TestMcpSandboxPipeline::test_full_mcp_agent_sandbox_lifecycle_pipeline PASSED

13 passed in 2.19s (100% PASS RATE)
```

No regressions occurred in existing sandbox or adversarial test suites.
