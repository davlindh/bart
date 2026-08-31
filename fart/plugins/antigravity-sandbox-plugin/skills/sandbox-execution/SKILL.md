---
name: sandbox-execution
description: Execute code in secure E2B Firecracker microVMs or local AST-validated sandboxes with persistent REPL state and artifact capture. Use when running Python/Bash scripts, performing multi-turn data analysis, generating charts and tables, or managing sandbox lifecycle.
---

# Sandbox Execution Skill

## Overview
The `sandbox-execution` skill enables autonomous agents to execute Python and shell code safely within isolated execution environments. The underlying architecture automatically provisions E2B Firecracker microVMs or falls back to a high-security local AST-validated sandbox with persistent REPL sessions, real-time output capture, and structured artifact extraction.

---

## Tool Reference

| Tool | Primary Purpose | Required Parameters | Optional Parameters |
| :--- | :--- | :--- | :--- |
| `create_sandbox` | Provision a new isolated sandbox | None | `template`, `mode` (`auto`, `local`, `e2b`), `timeout_seconds`, `env_vars`, `memory_limit_mb` |
| `execute_code` | Run code with persistent REPL state | `sandbox_id`, `code` | `language` (`python`, `bash`), `timeout_seconds`, `repl_mode`, `stream_output` |
| `pause_sandbox` | Suspend sandbox compute to save resources | `sandbox_id` | `auto_snapshot` |
| `resume_sandbox` | Resume a suspended sandbox | `sandbox_id` | `timeout_seconds` |
| `destroy_sandbox` | Terminate sandbox and purge assets | `sandbox_id` | `force` |

---

## Standard Step-by-Step Workflow

### Step 1: Provision the Sandbox
Before executing any code, call `create_sandbox` to allocate an isolated execution context.

```json
{
  "tool": "create_sandbox",
  "arguments": {
    "mode": "auto",
    "template": "python-3.11",
    "timeout_seconds": 300
  }
}
```

**Response Example**:
```json
{
  "sandbox_id": "sb-e2b-4f91b2",
  "mode": "local",
  "status": "running",
  "created_at": 1756430400.0,
  "timeout": 300.0
}
```
*Always store the returned `sandbox_id` for subsequent execution turns.*

---

### Step 2: Stateful Multi-Turn Code Execution
Use `execute_code` with `repl_mode: true` to execute Python blocks where variables, imports, and definitions persist across consecutive calls.

#### Turn 1: Ingestion & Data Preparation
```json
{
  "tool": "execute_code",
  "arguments": {
    "sandbox_id": "sb-e2b-4f91b2",
    "code": "import math, json\nraw_data = [12.5, 14.8, 18.2, 22.0, 25.4]\nmean_val = sum(raw_data) / len(raw_data)\nprint(f'Mean: {mean_val:.2f}')",
    "repl_mode": true
  }
}
```
*Output*: `Mean: 18.58`

#### Turn 2: Downstream Transformation (Reusing State from Turn 1)
```json
{
  "tool": "execute_code",
  "arguments": {
    "sandbox_id": "sb-e2b-4f91b2",
    "code": "variance = sum((x - mean_val)**2 for x in raw_data) / len(raw_data)\nstd_dev = math.sqrt(variance)\nprint(f'Standard Deviation: {std_dev:.2f}')",
    "repl_mode": true
  }
}
```
*Output*: `Standard Deviation: 4.67`

---

### Step 3: Visual & Tabular Artifact Capture
When generating figures with `matplotlib` or tabular outputs with `pandas`, artifacts are automatically captured and returned in the structured response.

```json
{
  "tool": "execute_code",
  "arguments": {
    "sandbox_id": "sb-e2b-4f91b2",
    "code": "import matplotlib.pyplot as plt\nplt.figure(figsize=(6, 3))\nplt.plot(raw_data, marker='o', color='crimson')\nplt.title('Metric Trend')\nplt.show()",
    "repl_mode": true
  }
}
```

The response includes `artifacts` with base64 PNG data:
```json
{
  "stdout": "",
  "stderr": "",
  "exit_code": 0,
  "artifacts": [
    {
      "name": "figure_1.png",
      "mime_type": "image/png",
      "data_base64": "iVBORw0KGgoAAAANSUhEUgAA...",
      "artifact_type": "image/png"
    }
  ]
}
```

---

### Step 4: Pausing and Resuming Compute
For long-lived interactive workflows with idle periods between user interactions, pause the sandbox to conserve compute resources:

```json
{
  "tool": "pause_sandbox",
  "arguments": {
    "sandbox_id": "sb-e2b-4f91b2",
    "auto_snapshot": true
  }
}
```

When new inputs arrive, resume the sandbox seamlessly:
```json
{
  "tool": "resume_sandbox",
  "arguments": {
    "sandbox_id": "sb-e2b-4f91b2",
    "timeout_seconds": 300
  }
}
```

---

### Step 5: Handling Execution Errors & Fallback
If an error occurs during execution:
1. **Traceback Analysis**: Examine the returned Python stack trace to diagnose syntax, key, or value errors.
2. **AST Security Violations**: When operating under local fallback mode, imports of forbidden system packages (`os`, `sys`, `subprocess`) or dynamic dunder escapes (`__subclasses__`) trigger `AST_SECURITY_VIOLATION`. Rewrite using approved standard library modules (`math`, `datetime`, `json`, `collections`).
3. **Execution Timeouts**: If a long calculation times out, optimize algorithms, utilize vectorization (`numpy`), or partition into smaller execution chunks.

---

### Step 6: Sandbox Teardown
Always release resources when the task or conversation completes:

```json
{
  "tool": "destroy_sandbox",
  "arguments": {
    "sandbox_id": "sb-e2b-4f91b2",
    "force": true
  }
}
```

---

## Detailed References
- [REPL Persistence & Namespace Patterns](references/repl-patterns.md)
- [Artifact Extraction & Serialization Guide](references/artifact-extraction.md)
