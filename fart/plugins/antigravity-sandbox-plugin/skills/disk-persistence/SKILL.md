---
name: disk-persistence
description: Persist and restore sandbox REPL sessions, multi-branch snapshot trees, variable registries, and scheduled worker histories to durable disk storage (SQLite + filesystem) across restarts and process boundaries. Use when checkpointing data science sessions, resuming long-running analysis, branching state vectors, or recovering daemon jobs.
---

# Disk Persistence Skill

## Overview
The `disk-persistence` skill provides durable, process-independent state persistence for the Antigravity platform. Backed by `PersistenceManager`, SQLite in Write-Ahead Logging (WAL) mode, and a content-addressed filesystem blob store, this subsystem allows autonomous agents to serialize complex runtime state (dataframes, ML tensors, snapshot trees, worker schedules) to disk and restore them in new processes with zero data loss.

---

## Tool Reference

| Tool | Primary Purpose | Required Parameters | Optional Parameters |
| :--- | :--- | :--- | :--- |
| `persist_sandbox` | Serialize active sandbox session and variables to disk | `sandbox_id` | `storage_path`, `name`, `description`, `include_variables`, `include_snapshots`, `include_filesystem` |
| `restore_sandbox_disk` | Rehydrate a persisted sandbox session into an active REPL | None | `persisted_id`, `sandbox_id`, `storage_path`, `target_mode`, `restore_variables`, `restore_snapshots`, `new_sandbox_id` |
| `list_persisted_sandboxes` | Catalog all persisted sessions and snapshot vectors on disk | None | `storage_path`, `filter_name`, `limit`, `offset`, `include_details` |
| `manage_snapshot` | Create, restore, list, or delete snapshot state branches | `action` | `sandbox_id`, `snapshot_id`, `name`, `description` |

---

## Standard Step-by-Step Workflow

### Step 1: Compute & Accumulate State in Sandbox
Execute computational workloads in an active sandbox session:

```json
{
  "tool": "execute_code",
  "arguments": {
    "sandbox_id": "sb-research-01",
    "code": "import numpy as np, pandas as pd\nmatrix = np.random.randn(100, 10)\ndf = pd.DataFrame(matrix, columns=[f'feat_{i}' for i in range(10)])\nsummary_stats = df.describe().to_dict()\nprint('DATA_READY: shape =', df.shape)",
    "repl_mode": true
  }
}
```

---

### Step 2: Persist Sandbox Session to Disk
Serialize the REPL namespace and state metadata into SQLite:

```json
{
  "tool": "persist_sandbox",
  "arguments": {
    "sandbox_id": "sb-research-01",
    "name": "financial-feature-matrix-v1",
    "description": "Preprocessed 100x10 feature dataset and summary statistics dictionary.",
    "include_variables": true
  }
}
```

**Response Example**:
```json
{
  "sandbox_id": "sb-research-01",
  "persisted_id": "sb-research-01",
  "name": "financial-feature-matrix-v1",
  "status": "persisted",
  "variable_count": 3,
  "created_at": 1756432000.0,
  "updated_at": 1756432000.0
}
```

---

### Step 3: Inspect Persisted Catalog
When resuming work or exploring historical sessions, list stored records:

```json
{
  "tool": "list_persisted_sandboxes",
  "arguments": {
    "filter_name": "financial",
    "limit": 10
  }
}
```

**Response Example**:
```json
{
  "total_count": 1,
  "offset": 0,
  "limit": 10,
  "sandboxes": [
    {
      "sandbox_id": "sb-research-01",
      "mode": "local",
      "status": "running",
      "created_at": 1756432000.0,
      "updated_at": 1756432000.0,
      "variable_count": 3,
      "metadata": {
        "name": "financial-feature-matrix-v1",
        "description": "Preprocessed 100x10 feature dataset and summary statistics dictionary."
      }
    }
  ]
}
```

---

### Step 4: Restore Session Across Process Boundaries
Restore the persisted session into a new active sandbox environment:

```json
{
  "tool": "restore_sandbox_disk",
  "arguments": {
    "persisted_id": "sb-research-01",
    "target_mode": "local",
    "restore_variables": true
  }
}
```

**Response Example**:
```json
{
  "sandbox_id": "sb-research-01",
  "restored_from": "sb-research-01",
  "mode": "local",
  "status": "running",
  "variable_count": 3
}
```

---

### Step 5: Verify Continuous Execution
Immediately execute subsequent turns against restored variables:

```json
{
  "tool": "execute_code",
  "arguments": {
    "sandbox_id": "sb-research-01",
    "code": "print('REHYDRATED_COLUMNS =', list(df.columns[:3]))\nprint('MATRIX_MEAN =', round(float(matrix.mean()), 4))",
    "repl_mode": true
  }
}
```
*Output*: `REHYDRATED_COLUMNS = ['feat_0', 'feat_1', 'feat_2']`, `MATRIX_MEAN = -0.0142`

---

## Detailed References
- [SQLite Schema & Heterogeneous Variable Codec](references/session-persistence.md)
- [Multi-Branch Snapshot Directed Acyclic Graphs (DAGs)](references/snapshot-branching.md)
- [Scheduled Worker & Daemon Recovery Protocol](references/worker-recovery.md)
