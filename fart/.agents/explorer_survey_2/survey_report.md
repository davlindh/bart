# Antigravity MCP Server & Customization Plugin Technical Survey & Architecture Specification

**Document Version**: 1.0.0  
**Phase**: Phase 0 — Survey & Scope Mapping  
**Author**: Explorer Subagent (`explorer_survey_2`)  
**Targets**: Requirement R2 (Antigravity MCP Server) & Requirement R3 (Antigravity Customization Plugin & Skill Suite)  
**Date**: 2026-08-29  

---

## 1. Executive Summary & Problem Scope

Modern autonomous agents require isolated, dynamic code execution environments ("thinking in code", Hugging Face `smolagents` paradigm) paired with background job scheduling and state persistence. The goal of Requirements **R2** and **R3** is to build the integration and customization layer connecting the **Antigravity AI Platform** with:
1. **Firecracker MicroVM Sandbox & Execution Engine (R1)**: E2B hardware-isolated microVMs with seamless local fallback AST sandboxes.
2. **Scheduled Background Service Worker Daemon (R4)**: Recurring cron jobs and one-shot timers.

This specification details:
- **Requirement R2 (Antigravity MCP Server)**: A high-performance Model Context Protocol (MCP) server communicating over `stdio` using standard JSON-RPC 2.0 framing. It exposes 7 core lifecycle and execution tools (`create_sandbox`, `execute_code`, `pause_sandbox`, `resume_sandbox`, `destroy_sandbox`, `manage_snapshot`, `spawn_worker`), implements real-time stdout/stderr streaming, structured artifact capture (charts, tables, files), and robust error domains.
- **Requirement R3 (Antigravity Customization Plugin & Skill Suite)**: Packaging according to the Antigravity Plugin Specification (`plugin.json`, `mcp_config.json`, `rules/AGENTS.md`, `hooks.json`), complete with 3 modular skills (`sandbox-execution`, `worker-orchestration`, `snapshot-management`) utilizing progressive disclosure (YAML frontmatter + reference guides).

---

## 2. Requirement R2: Antigravity MCP Server Architecture

### 2.1 Transport & Communication Protocol

The Antigravity MCP Server adheres to the **Model Context Protocol (MCP) Specification (2024-11-05)** using the **Stdio Transport**.

```
+-------------------------------------------------------------------------+
|                        Antigravity Language Server                      |
+-------------------------------------------------------------------------+
         | stdin (JSON-RPC 2.0 requests)         ^ stdout (JSON-RPC 2.0 responses)
         |                                       |
         v                                       |
+-------------------------------------------------------------------------+
|                  Antigravity MCP Server Process (Python)                |
|  +-------------------------------------------------------------------+  |
|  |                 Stdio JSON-RPC 2.0 Dispatcher                     |  |
|  +-------------------------------------------------------------------+  |
|         |                                      |                        |
|         v                                      v                        |
|  +-----------------------+           +-----------------------+          |
|  |   Tool Registry       |           |  Streaming / Loggers  |          |
|  +-----------------------+           +-----------------------+          |
|         |                                      |                        |
|         +-------------------+------------------+                        |
|                             |                                           |
|                             v                                           |
|  +-------------------------------------------------------------------+  |
|  |   Sandbox Manager Bridge (R1)   |  Worker Daemon Bridge (R4)      |  |
|  +-------------------------------------------------------------------+  |
+-------------------------------------------------------------------------+
         |                                       |
         v (stderr: Diagnostics & Server Logs ONLY)
```

#### Key Transport Invariants:
1. **Stdio Protocol Framing**:
   - Messages are transmitted line-by-line using newline-delimited JSON (`\n`) or standard JSON-RPC 2.0 framing over standard input (`stdin`) and standard output (`stdout`).
   - `stdout` is **strictly reserved** for JSON-RPC 2.0 communication. No debug prints, external library logs, or uncaught warnings may touch `stdout`.
   - All server logging, diagnostic traces, and internal warnings are redirected to `stderr`.
2. **Asynchronous Non-Blocking Dispatch**:
   - Built on `asyncio` with concurrent request handling.
   - Long-running execution or tool calls run in background tasks and emit progress/log notifications without deadlocking the stdio reader.

---

### 2.2 MCP Lifecycle Handshake & Capabilities

#### Handshake Sequence:
1. **`initialize` Request**:
   ```json
   {
     "jsonrpc": "2.0",
     "id": 1,
     "method": "initialize",
     "params": {
       "protocolVersion": "2024-11-05",
       "capabilities": {
         "roots": { "listChanged": true },
         "sampling": {}
       },
       "clientInfo": {
         "name": "antigravity-client",
         "version": "2.0.0"
       }
     }
   }
   ```
2. **`initialize` Response**:
   ```json
   {
     "jsonrpc": "2.0",
     "id": 1,
     "result": {
       "protocolVersion": "2024-11-05",
       "capabilities": {
         "tools": { "listChanged": true },
         "logging": {},
         "resources": { "subscribe": true, "listChanged": true }
       },
       "serverInfo": {
         "name": "antigravity-sandbox-mcp",
         "version": "1.0.0"
       }
     }
   }
   ```
3. **`notifications/initialized` Notification**:
   ```json
   {
     "jsonrpc": "2.0",
     "method": "notifications/initialized",
     "params": {}
   }
   ```
4. **`ping` Request**:
   ```json
   {
     "jsonrpc": "2.0",
     "id": 2,
     "method": "ping",
     "params": {}
   }
   ```
   *Response*: `{"jsonrpc": "2.0", "id": 2, "result": {}}`

---

### 2.3 Detailed Tool Specifications & Schemas

The MCP server exposes 7 core tools via `tools/list` and `tools/call`.

```
=============================================================================
                          MCP SERVER TOOL REGISTRY
=============================================================================
1. create_sandbox      -> Provision MicroVM (E2B) or Local Fallback Sandbox
2. execute_code        -> Execute Python/Bash in REPL or Script Mode
3. pause_sandbox       -> Freeze memory state & release compute resources
4. resume_sandbox      -> Unfreeze and resume execution state
5. destroy_sandbox     -> Purge sandbox & cleanup temporary assets
6. manage_snapshot     -> Checkpoint, restore, list, or delete memory snapshots
7. spawn_worker        -> Register scheduled background daemon / timer tasks
=============================================================================
```

---

#### 1. `create_sandbox`

**Purpose**: Provisions a new isolated execution sandbox. Seamlessly attempts E2B Firecracker microVM provisioning; if API keys are not present or network fails, automatically falls back to secure local AST-isolated sandbox unless configured otherwise.

**Input Schema (`inputSchema`)**:
```json
{
  "type": "object",
  "properties": {
    "template": {
      "type": "string",
      "description": "Template or base environment (e.g. 'python-3.11', 'data-science', 'base').",
      "default": "python-3.11"
    },
    "timeout_seconds": {
      "type": "integer",
      "description": "Inactivity lifetime timeout in seconds after which sandbox auto-destroys.",
      "default": 300,
      "minimum": 10,
      "maximum": 3600
    },
    "env_vars": {
      "type": "object",
      "additionalProperties": { "type": "string" },
      "description": "Environment variables to inject into sandbox context."
    },
    "mode": {
      "type": "string",
      "enum": ["auto", "e2b", "local_fallback"],
      "description": "Execution isolation backend. 'auto' selects E2B if available, falling back to local sandbox.",
      "default": "auto"
    },
    "memory_limit_mb": {
      "type": "integer",
      "description": "Memory limit in MB (local sandbox enforcement or custom template sizing).",
      "default": 512
    }
  },
  "required": []
}
```

**Output Payload (embedded in `tools/call` response text/json)**:
```json
{
  "sandbox_id": "sbx-9f4a1c2b-83e4-4d8e-b150-e8f00123a456",
  "mode_selected": "e2b",
  "status": "ready",
  "created_at": "2026-08-29T01:05:00Z",
  "expires_at": "2026-08-29T01:10:00Z",
  "capabilities": ["repl", "filesystem", "network", "snapshot", "pause_resume"],
  "template": "python-3.11",
  "metadata": {
    "provider": "E2B Firecracker MicroVM",
    "vm_ip": "172.16.0.42"
  }
}
```

---

#### 2. `execute_code`

**Purpose**: Executes Python or shell code in the targeted sandbox. Supports persistent REPL sessions (variables, imports, and definitions survive across consecutive calls) and captures stdout, stderr, return values, and rich artifacts (images, charts, dataframes, generated files).

**Input Schema (`inputSchema`)**:
```json
{
  "type": "object",
  "properties": {
    "sandbox_id": {
      "type": "string",
      "description": "Identifier of the active sandbox."
    },
    "code": {
      "type": "string",
      "description": "Python or shell code block to execute."
    },
    "language": {
      "type": "string",
      "enum": ["python", "bash", "sh"],
      "default": "python",
      "description": "Execution language interpreter."
    },
    "timeout_seconds": {
      "type": "integer",
      "description": "Execution timeout for this code block in seconds.",
      "default": 60,
      "minimum": 1,
      "maximum": 600
    },
    "repl_mode": {
      "type": "boolean",
      "description": "If true, maintains REPL variable and import state. If false, runs in fresh subprocess.",
      "default": true
    },
    "stream_output": {
      "type": "boolean",
      "description": "If true, emits progressive MCP notifications during long-running execution.",
      "default": false
    }
  },
  "required": ["sandbox_id", "code"]
}
```

**Output Payload**:
```json
{
  "status": "success",
  "exit_code": 0,
  "execution_time_ms": 142.5,
  "stdout": "Calculated 1000 data points.\nTrend slope: 2.45\n",
  "stderr": "",
  "return_value": "2.45",
  "artifacts": [
    {
      "artifact_id": "art-001",
      "artifact_type": "image/png",
      "name": "trend_chart.png",
      "mime_type": "image/png",
      "data_base64": "iVBORw0KGgoAAAANSUhEUgAA...",
      "metadata": {
        "title": "Model Performance Curve",
        "dpi": 300
      }
    },
    {
      "artifact_id": "art-002",
      "artifact_type": "data/csv",
      "name": "metrics.csv",
      "mime_type": "text/csv",
      "data_base64": "c3RlcCx2YWx1ZQoxLDAuOTUKMiwwLjk4Cg==",
      "metadata": {
        "rows": 2,
        "columns": ["step", "value"]
      }
    }
  ],
  "sandbox_state": {
    "active_variables": ["data", "model", "slope", "metrics_df"],
    "memory_used_mb": 48.2
  }
}
```

---

#### 3. `pause_sandbox`

**Purpose**: Pauses an active sandbox, freezing execution and memory state to conserve system resources while retaining session state for future resumption.

**Input Schema (`inputSchema`)**:
```json
{
  "type": "object",
  "properties": {
    "sandbox_id": {
      "type": "string",
      "description": "Identifier of the active sandbox to pause."
    },
    "auto_snapshot": {
      "type": "boolean",
      "description": "Whether to create a persistent disk snapshot before pausing.",
      "default": true
    }
  },
  "required": ["sandbox_id"]
}
```

**Output Payload**:
```json
{
  "sandbox_id": "sbx-9f4a1c2b-83e4-4d8e-b150-e8f00123a456",
  "status": "paused",
  "paused_at": "2026-08-29T01:07:30Z",
  "snapshot_id": "snp-1a2b3c4d-5678",
  "message": "Sandbox successfully paused in-memory and state snapshotted."
}
```

---

#### 4. `resume_sandbox`

**Purpose**: Resumes a paused sandbox, unfreezing its memory context or reloading its snapshot without losing REPL state.

**Input Schema (`inputSchema`)**:
```json
{
  "type": "object",
  "properties": {
    "sandbox_id": {
      "type": "string",
      "description": "Identifier of the paused sandbox to resume."
    },
    "timeout_seconds": {
      "type": "integer",
      "description": "New inactivity timeout in seconds following resumption.",
      "default": 300
    }
  },
  "required": ["sandbox_id"]
}
```

**Output Payload**:
```json
{
  "sandbox_id": "sbx-9f4a1c2b-83e4-4d8e-b150-e8f00123a456",
  "status": "ready",
  "resumed_at": "2026-08-29T01:08:15Z",
  "expires_at": "2026-08-29T01:13:15Z",
  "message": "Sandbox successfully resumed and ready for code execution."
}
```

---

#### 5. `destroy_sandbox`

**Purpose**: Completely terminates the sandbox, killing associated microVM or local processes and purging all temporary workspace directories.

**Input Schema (`inputSchema`)**:
```json
{
  "type": "object",
  "properties": {
    "sandbox_id": {
      "type": "string",
      "description": "Identifier of the sandbox to destroy."
    },
    "force": {
      "type": "boolean",
      "description": "Force kill if a command is currently executing.",
      "default": true
    }
  },
  "required": ["sandbox_id"]
}
```

**Output Payload**:
```json
{
  "sandbox_id": "sbx-9f4a1c2b-83e4-4d8e-b150-e8f00123a456",
  "status": "destroyed",
  "duration_active_seconds": 215.4,
  "freed_resources": {
    "memory_mb": 512,
    "disk_cleaned": true
  }
}
```

---

#### 6. `manage_snapshot`

**Purpose**: Provides full snapshot lifecycle management (create, restore, list, delete) for checkpointing execution states, branching agent workflows, or rolling back failed code steps.

**Input Schema (`inputSchema`)**:
```json
{
  "type": "object",
  "properties": {
    "action": {
      "type": "string",
      "enum": ["create", "restore", "list", "delete"],
      "description": "Snapshot management action to execute."
    },
    "sandbox_id": {
      "type": "string",
      "description": "Sandbox ID (required for 'create', optional for others)."
    },
    "snapshot_id": {
      "type": "string",
      "description": "Snapshot ID (required for 'restore' and 'delete')."
    },
    "name": {
      "type": "string",
      "description": "Human-readable label for snapshot (for 'create')."
    },
    "description": {
      "type": "string",
      "description": "Detailed description of saved state (for 'create')."
    }
  },
  "required": ["action"]
}
```

**Output Payload (for `action: "create"`)**:
```json
{
  "action": "create",
  "snapshot_id": "snp-90ab-12cd",
  "sandbox_id": "sbx-9f4a1c2b-83e4-4d8e-b150-e8f00123a456",
  "name": "post-model-training",
  "created_at": "2026-08-29T01:06:00Z",
  "size_bytes": 1048576,
  "status": "ready"
}
```

**Output Payload (for `action: "list"`)**:
```json
{
  "action": "list",
  "snapshots": [
    {
      "snapshot_id": "snp-90ab-12cd",
      "sandbox_id": "sbx-9f4a1c2b-83e4-4d8e-b150-e8f00123a456",
      "name": "post-model-training",
      "created_at": "2026-08-29T01:06:00Z",
      "status": "ready"
    }
  ]
}
```

---

#### 7. `spawn_worker`

**Purpose**: Dispatches a background service worker task to the scheduled background daemon (R4). Supports recurring cron schedules, one-shot duration timers, and event triggers that execute in dedicated sandboxes.

**Input Schema (`inputSchema`)**:
```json
{
  "type": "object",
  "properties": {
    "task_name": {
      "type": "string",
      "description": "Descriptive name for the background worker task."
    },
    "code": {
      "type": "string",
      "description": "Executable Python code or script payload to run."
    },
    "trigger_type": {
      "type": "string",
      "enum": ["cron", "timer", "immediate"],
      "description": "Trigger modality: 'cron' for recurring schedule, 'timer' for one-shot delay, 'immediate' for async background run."
    },
    "trigger_spec": {
      "type": "string",
      "description": "Standard 5-field cron expression (e.g. '*/5 * * * *') or ISO duration / seconds (e.g. '300s', '10m')."
    },
    "max_iterations": {
      "type": "integer",
      "description": "Maximum number of executions before auto-terminating (for cron triggers).",
      "default": 0
    },
    "sandbox_template": {
      "type": "string",
      "description": "Template to spawn for the worker's execution environment.",
      "default": "python-3.11"
    },
    "env_vars": {
      "type": "object",
      "additionalProperties": { "type": "string" },
      "description": "Environment variables passed into worker sandbox."
    },
    "timeout_seconds": {
      "type": "integer",
      "description": "Max runtime allowed per execution run.",
      "default": 120
    }
  },
  "required": ["task_name", "code", "trigger_type", "trigger_spec"]
}
```

**Output Payload**:
```json
{
  "worker_id": "wrk-77a1b2c3-4d5e-6f70",
  "task_name": "data-pipeline-sync",
  "status": "scheduled",
  "trigger_type": "cron",
  "trigger_spec": "*/5 * * * *",
  "created_at": "2026-08-29T01:05:30Z",
  "next_run_at": "2026-08-29T01:10:00Z",
  "sandbox_template": "python-3.11",
  "message": "Background worker registered with daemon scheduler."
}
```

---

### 2.4 Real-Time Output Streaming & Artifact Extraction

#### Real-Time Streaming over MCP:
1. **Progress Tokens (`notifications/progress`)**:
   When `stream_output: true` or a progress token is passed by the client, intermediate notifications are sent:
   ```json
   {
     "jsonrpc": "2.0",
     "method": "notifications/progress",
     "params": {
       "progressToken": "tok-123",
       "progress": 45,
       "total": 100,
       "message": "Training step 450/1000 complete..."
     }
   }
   ```
2. **Server-Side Log Messages (`notifications/message`)**:
   Used to stream live stdout chunks to the client terminal:
   ```json
   {
     "jsonrpc": "2.0",
     "method": "notifications/message",
     "params": {
       "level": "info",
       "logger": "sandbox.stdout",
       "data": "Epoch 1/10 - loss: 0.342\n"
     }
   }
   ```

#### Artifact Extraction Engine:
- **Matplotlib / Seaborn / Plotly Detection**: The execution engine intercepts `plt.show()` and `plotly.io.show()` hooks inside the REPL kernel, automatically serializing active figures into base64-encoded PNGs and SVGs before clearing the canvas.
- **DataFrames**: Pandas and Polars DataFrames evaluated as expressions or saved to files are automatically serialized into CSV and interactive JSON data tables.
- **Generated File Harvesting**: Any files written to `/tmp/artifacts/` inside the microVM or local fallback directory are indexed, mime-typed, and attached to the tool call result.

---

### 2.5 Error Handling & Fault Domain Schemas

The MCP server differentiates between protocol-level JSON-RPC errors and domain-level sandbox execution errors.

#### Error Code Matrix:

| Error Code | Constant | Description | Remediation / Fallback |
| :--- | :--- | :--- | :--- |
| **`-32700`** | `PARSE_ERROR` | Malformed JSON on stdin | Client retransmits valid JSON |
| **`-32600`** | `INVALID_REQUEST` | Missing `jsonrpc` or `id` | Standard JSON-RPC validation |
| **`-32601`** | `METHOD_NOT_FOUND` | Unknown MCP method | Query `tools/list` |
| **`-32602`** | `INVALID_PARAMS` | Schema violation in arguments | Inspect tool schema |
| **`-32603`** | `INTERNAL_ERROR` | Unhandled server exception | Inspect server stderr log |
| **`-32000`** | `SANDBOX_NOT_FOUND` | Sandbox ID expired or destroyed | Call `create_sandbox` |
| **`-32001`** | `EXECUTION_TIMEOUT` | Code ran longer than timeout | Optimize code or increase timeout |
| **`-32002`** | `AST_SECURITY_VIOLATION` | Local fallback detected forbidden node | Remove forbidden imports/calls |
| **`-32003`** | `E2B_PROVIDER_ERROR` | E2B API rate limit or outage | Auto-fallback to local sandbox |
| **`-32004`** | `WORKER_SCHEDULE_ERROR` | Invalid cron/timer specification | Fix cron format (5 fields) |
| **`-32005`** | `SNAPSHOT_CORRUPTED` | Snapshot serialization failure | Take fresh snapshot |

#### Structured Tool Call Error Format:
In MCP, execution errors (e.g. Python `ZeroDivisionError` or `SyntaxError`) are returned with `isError: true` inside a valid JSON-RPC response so the model can read the traceback and self-correct:
```json
{
  "jsonrpc": "2.0",
  "id": 5,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "ExecutionError: Traceback (most recent call last):\n  File \"<repl>\", line 3, in <module>\nZeroDivisionError: division by zero"
      }
    ],
    "isError": true
  }
}
```

---

## 3. Requirement R3: Antigravity Customization Plugin & Skill Suite

### 3.1 Plugin Packaging Standard & Directory Layout

The plugin follows the Antigravity Plugin Specification mounted under `.agents/plugins/antigravity-sandbox-plugin/` or `plugins/antigravity-sandbox-plugin/`.

```text
plugins/antigravity-sandbox-plugin/
├── plugin.json                 # Core plugin manifest declaring identity & version
├── mcp_config.json             # MCP server stdio registration
├── hooks.json                  # Lifecycle safety hooks (PreToolUse & Stop)
├── rules/
│   └── AGENTS.md               # Autonomous agent execution guidelines & policies
└── skills/
    ├── sandbox-execution/
    │   ├── SKILL.md            # Progressive disclosure runbook for sandbox & REPL
    │   ├── references/
    │   │   ├── artifacts.md    # Chart/table extraction guide
    │   │   └── fallback.md     # Local AST fallback capabilities & limits
    │   └── examples/
    │       ├── data_analysis.py# Example end-to-end data workflow
    │       └── repl_state.py   # Example persistent REPL variable workflow
    ├── worker-orchestration/
    │   ├── SKILL.md            # Background worker scheduling & cron guide
    │   └── references/
    │       └── cron_syntax.md  # Reference for cron expressions & durations
    └── snapshot-management/
        ├── SKILL.md            # State checkpointing & branching runbook
        └── references/
            └── branching.md    # Agent state rollback strategies
```

---

### 3.2 Plugin Manifest (`plugin.json`)

```json
{
  "name": "antigravity-sandbox-plugin",
  "version": "1.0.0",
  "description": "High-security E2B Firecracker microVM execution engine with local AST fallback and background worker daemon scheduler for autonomous agents.",
  "author": {
    "name": "Antigravity Team",
    "email": "antigravity-dev@google.com"
  },
  "repository": "https://github.com/google-antigravity/antigravity-sandbox-plugin",
  "license": "Apache-2.0",
  "keywords": [
    "antigravity",
    "mcp",
    "sandbox",
    "e2b",
    "firecracker",
    "microvm",
    "repl",
    "service-workers",
    "scheduler"
  ]
}
```

---

### 3.3 Plugin MCP Configuration (`mcp_config.json`)

Registers the Python MCP server with the Language Server via stdio transport:

```json
{
  "mcpServers": {
    "antigravity-sandbox": {
      "command": "python",
      "args": ["-m", "antigravity_mcp.server"],
      "env": {
        "PYTHONUNBUFFERED": "1",
        "E2B_API_KEY": "${env:E2B_API_KEY}",
        "ANTIGRAVITY_SANDBOX_MODE": "auto",
        "ANTIGRAVITY_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

---

### 3.4 Workspace Rules (`rules/AGENTS.md`)

These rules are loaded when the plugin is active and govern autonomous agent behavior:

```markdown
# Antigravity Sandbox & Execution Engine Operating Directives

## 1. Execution Philosophy: "Thinking in Code"
- Whenever a problem requires complex calculations, data transformations, multi-step iterations, or file parsing, write and execute Python code in the sandbox rather than guessing or computing mentally.
- Prefer executing modular code blocks in the same persistent sandbox session to reuse loaded datasets, imports, and variables.

## 2. Sandbox Lifecycle Hygiene
- Always call `create_sandbox` before initiating a series of code execution steps.
- Set appropriate `timeout_seconds` based on expected workload.
- When an exploratory sub-task or mission milestone is completed, immediately call `destroy_sandbox` to prevent resource leaks.
- For multi-stage experiments where intermediate calculations must be preserved before trying risky operations, take a snapshot using `manage_snapshot(action="create")`.

## 3. Fallback Awareness & Security Compliance
- The execution engine automatically falls back to local AST-isolated sandboxes if E2B Firecracker microVMs are unreachable or unauthenticated.
- When running in local fallback mode:
  - Do not attempt unauthorized filesystem traversals or host-modifying subprocesses.
  - Rely on authorized standard library modules (`math`, `datetime`, `json`, `re`, `collections`, `itertools`) and approved data science packages (`numpy`, `pandas`).

## 4. Background Workers & Long-Running Tasks
- Never run infinite loops or blocking sleeps in the interactive REPL.
- To schedule recurring health checks, monitoring pipelines, or periodic sync tasks, use `spawn_worker` with a 5-field cron expression or duration timer.
- Inspect worker status and logs before terminating agent sessions.
```

---

### 3.5 Antigravity Skills Specifications (`SKILL.md`)

Antigravity uses **Progressive Disclosure**: only `name` and `description` are loaded into system prompts initially. The full `SKILL.md` is loaded only when triggered by relevant tasks. Bulky reference materials are isolated in `references/`.

---

#### Skill 1: `sandbox-execution` (`skills/sandbox-execution/SKILL.md`)

```markdown
---
name: sandbox-execution
description: Comprehensive runbook for isolated Python code execution in E2B Firecracker microVMs and local AST sandboxes. Use when generating, executing, or debugging Python code, analyzing datasets, generating charts/artifacts, or managing REPL variable state.
---

# Sandbox Execution Runbook

## Overview
This skill guides you through provisioning isolated sandboxes, running REPL code blocks, managing persistent state, and retrieving visual or tabular artifacts.

## Standard Execution Flow

### Step 1: Initialize Sandbox
Create a sandbox before running code:
```json
{
  "tool": "create_sandbox",
  "args": {
    "template": "python-3.11",
    "timeout_seconds": 300,
    "mode": "auto"
  }
}
```
Record the returned `sandbox_id`.

### Step 2: Execute Code with Persistent REPL
Execute code incrementally. Variables and functions defined in previous steps remain in memory:
```python
# Step A: Load and inspect data
import pandas as pd
import numpy as np

df = pd.DataFrame({
    'timestamp': pd.date_range('2026-01-01', periods=5, freq='D'),
    'value': [10.5, 12.3, 11.8, 14.2, 15.0]
})
print(df.describe())
```

```python
# Step B: Generate Chart (automatically captured as an artifact)
import matplotlib.pyplot as plt

plt.figure(figsize=(8, 4))
plt.plot(df['timestamp'], df['value'], marker='o', color='teal')
plt.title('Value Progression')
plt.grid(True)
plt.show() # Intercepted and returned as artifact_type "image/png"
```

### Step 3: Handle Fallback & Errors
If the execution returns `isError: true`:
1. Read the error traceback carefully.
2. If `AST_SECURITY_VIOLATION` is returned, check for unauthorized module imports and replace them with standard equivalents.
3. Fix syntax or logic bugs and re-execute.

### Step 4: Cleanup
When finished, destroy the sandbox:
```json
{
  "tool": "destroy_sandbox",
  "args": {
    "sandbox_id": "sbx-..."
  }
}
```

## References & Examples
- [Artifact Extraction Details](references/artifacts.md)
- [Local Fallback Sandbox Capabilities](references/fallback.md)
- [Example: Data Analysis Pipeline](examples/data_analysis.py)
```

---

#### Skill 2: `worker-orchestration` (`skills/worker-orchestration/SKILL.md`)

```markdown
---
name: worker-orchestration
description: Runbook for scheduling and orchestrating background service workers, recurring cron tasks, and timer triggers in isolated sandboxes. Use when the user requests periodic monitoring, background data ingestion, scheduled health checks, or asynchronous job execution.
---

# Worker Orchestration Runbook

## Overview
The Worker Orchestration skill enables autonomous agents to delegate background tasks to the Scheduled Background Service Worker Daemon (R4) without blocking the primary conversational flow.

## Scheduling Patterns

### Pattern 1: Recurring Cron Task
Schedule a task to run periodically (e.g. every 10 minutes):
```json
{
  "tool": "spawn_worker",
  "args": {
    "task_name": "database-health-monitor",
    "trigger_type": "cron",
    "trigger_spec": "*/10 * * * *",
    "code": "import requests\nres = requests.get('https://api.internal/health')\nprint(f'Status: {res.status_code}')",
    "max_iterations": 50
  }
}
```

### Pattern 2: One-Shot Timer Delay
Schedule a task to execute after a fixed delay:
```json
{
  "tool": "spawn_worker",
  "args": {
    "task_name": "delayed-report-generation",
    "trigger_type": "timer",
    "trigger_spec": "600s",
    "code": "print('Starting batch aggregation after 10 min cooldown...')"
  }
}
```

## References
- [Cron Syntax & Duration Guide](references/cron_syntax.md)
```

---

#### Skill 3: `snapshot-management` (`skills/snapshot-management/SKILL.md`)

```markdown
---
name: snapshot-management
description: Runbook for creating, restoring, and managing sandbox execution state snapshots. Use when branching complex agent problem-solving workflows, checkpointing expensive computations, or rolling back failed execution steps.
---

# Snapshot Management Runbook

## Overview
Snapshots preserve the exact in-memory variables, loaded models, filesystem state, and REPL context of a running sandbox.

## Workflow: Checkpoint & Rollback

1. **Create Checkpoint**:
   ```json
   {
     "tool": "manage_snapshot",
     "args": {
       "action": "create",
       "sandbox_id": "sbx-...",
       "name": "baseline-dataset-loaded"
     }
   }
   ```
2. **Execute Experimental Code**: Run exploratory or risky transformations.
3. **Rollback on Failure**: If the transformation corrupts state or produces invalid results:
   ```json
   {
     "tool": "manage_snapshot",
     "args": {
       "action": "restore",
       "snapshot_id": "snp-..."
     }
   }
   ```

## References
- [Branching Strategies](references/branching.md)
```

---

### 3.6 Lifecycle Hooks (`hooks.json`)

```json
{
  "sandbox-safety-guard": {
    "enabled": true,
    "PreToolUse": [
      {
        "matcher": "execute_code",
        "hooks": [
          {
            "type": "command",
            "command": "python -m antigravity_mcp.hooks.safety_precheck",
            "timeout": 5
          }
        ]
      }
    ],
    "Stop": [
      {
        "type": "command",
        "command": "python -m antigravity_mcp.hooks.verify_active_sandboxes",
        "timeout": 5
      }
    ]
  }
}
```

---

## 4. Module Decomposition & Implementation Architecture

```
antigravity_mcp/
├── __init__.py
├── __main__.py                   # Entry point: python -m antigravity_mcp
├── server.py                     # Main MCP Server implementation & stdio loop
├── protocol/
│   ├── __init__.py
│   ├── jsonrpc.py                # JSON-RPC 2.0 parser, serializer, & error codes
│   ├── transport.py              # Async Stdio transport reader/writer
│   └── dispatcher.py             # Method router (initialize, ping, tools/*)
├── schemas/
│   ├── __init__.py
│   ├── mcp_types.py              # Pydantic models for Tool, Resource, Prompt, CallToolResult
│   ├── sandbox_models.py         # Schemas for create, pause, resume, destroy, snapshot
│   ├── execution_models.py       # Schemas for execute_code, artifacts, results
│   └── worker_models.py          # Schemas for spawn_worker, cron triggers
├── tools/
│   ├── __init__.py
│   ├── base.py                   # Abstract BaseTool class
│   ├── sandbox_tools.py          # create_sandbox, pause_sandbox, resume_sandbox, destroy_sandbox
│   ├── execution_tools.py        # execute_code tool implementation
│   ├── snapshot_tools.py         # manage_snapshot tool implementation
│   └── worker_tools.py           # spawn_worker tool implementation
├── streaming/
│   ├── __init__.py
│   ├── chunker.py                # Stream chunker for stdout/stderr
│   ├── artifact_extractor.py     # Base64 image/chart & CSV/table serializer
│   └── notifier.py               # MCP notifications/progress & notifications/message dispatcher
└── hooks/
    ├── __init__.py
    ├── safety_precheck.py        # Hook script for PreToolUse AST validation
    └── verify_active_sandboxes.py# Hook script for Stop lifecycle validation
```

---

## 5. Integration Contracts with Subsystems R1 & R4

### 5.1 Bridge Contract with Execution Engine (R1)

```python
class ISandboxExecutionEngine(ABC):
    """Interface exposed by R1 engine to R2 MCP Server."""
    
    @abstractmethod
    async def create_sandbox(self, req: CreateSandboxRequest) -> SandboxInstance:
        """Provisions E2B microVM or fallback sandbox."""
        ...

    @abstractmethod
    async def execute_code(self, req: ExecuteCodeRequest) -> ExecutionResult:
        """Executes code in REPL kernel and returns stdout, stderr, and artifacts."""
        ...

    @abstractmethod
    async def pause_sandbox(self, sandbox_id: str) -> PauseResult:
        ...

    @abstractmethod
    async def resume_sandbox(self, sandbox_id: str) -> ResumeResult:
        ...

    @abstractmethod
    async def destroy_sandbox(self, sandbox_id: str, force: bool = True) -> DestroyResult:
        ...

    @abstractmethod
    async def manage_snapshot(self, req: SnapshotRequest) -> SnapshotResult:
        ...
```

### 5.2 Bridge Contract with Scheduled Worker Daemon (R4)

```python
class IWorkerSchedulerDaemon(ABC):
    """Interface exposed by R4 daemon to R2 MCP Server."""
    
    @abstractmethod
    async def register_worker(self, req: SpawnWorkerRequest) -> WorkerRegistrationResult:
        """Registers scheduled job with background cron/timer scheduler."""
        ...

    @abstractmethod
    async def get_worker_status(self, worker_id: str) -> WorkerStatusResult:
        ...

    @abstractmethod
    async def cancel_worker(self, worker_id: str) -> bool:
        ...
```

---

## 6. Edge Cases, Failure Modes & Test Strategy for R5

### 6.1 Critical Edge Cases & Failure Recovery Matrix

| Scenario / Edge Case | Root Cause / Condition | Expected Server Behavior | Test Target |
| :--- | :--- | :--- | :--- |
| **Missing E2B API Key** | `E2B_API_KEY` not in env or invalid | If `mode="auto"`, log warning to stderr and provision `LocalFallbackSandbox`. If `mode="e2b"`, return error `-32003`. | `test_fallback_on_missing_api_key` |
| **E2B API Timeout / Network Drop** | Remote REST/gRPC handshake timeout | Catch timeout, gracefully fallback or report `isError: true` with error code `-32003`. | `test_e2b_network_timeout` |
| **Infinite Loop / Hang in Code** | `while True: pass` executed | `timeout_seconds` watchdog triggers, kills subprocess or signals kernel interrupt, returns status `timeout`. | `test_execution_timeout_watchdog` |
| **Memory Exhaustion (OOM)** | Huge allocation (e.g. `[0] * 10**9`) | Sandbox memory cgroup/limit kills process, returns exit code 137, server remains responsive. | `test_memory_limit_oom` |
| **Unsafe AST Injection** | Code uses `os.system("rm -rf /")` in local fallback | AST parser rejects unauthorized AST nodes before evaluation, returns `AST_SECURITY_VIOLATION`. | `test_ast_security_filter` |
| **Persistent REPL State Integrity** | Variable defined in step 1 used in step 2 | Step 2 accesses variable seamlessly; if kernel crashed, reports clean state reset. | `test_repl_state_persistence` |
| **Malformed JSON-RPC Input** | Incomplete line or syntax error on stdin | Server writes standard JSON-RPC `-32700 Parse error` to stdout and continues listening. | `test_jsonrpc_parse_error` |
| **Concurrent Tool Calls** | Simultaneous `execute_code` calls to different sandboxes | `asyncio` dispatcher handles both sandboxes concurrently without cross-talk. | `test_concurrent_execution` |

---

## 7. Strategic Recommendations for Implementation

1. **Stdio Protocol Hygiene**: Utilize pure Python standard library `asyncio` with explicit UTF-8 newline handling (`sys.stdin.buffer.readline` / `sys.stdout.buffer.write`) or `mcp` SDK to prevent Windows CRLF encoding corruptions.
2. **Pydantic Validation**: Use Pydantic v2 (already verified available in environment) for strict JSON schema generation and validation for all tool inputs and outputs.
3. **Artifact Serialization**: Package figures and tables directly into structured MCP tool results using standard base64 data URIs and inline text tables for immediate model legibility.
4. **Plugin Structure**: Mount under `plugins/antigravity-sandbox-plugin/` and ensure all markdown documentation follows the concise progressive disclosure pattern with deep references.

---
*Report compiled by explorer_survey_2 for Phase 0 Survey & Scope Mapping.*
