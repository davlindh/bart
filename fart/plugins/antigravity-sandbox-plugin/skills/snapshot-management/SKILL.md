---
name: snapshot-management
description: Create checkpoints of sandbox execution state, manage branching sessions, and restore previous states. Use when branching complex problem-solving workflows, checkpointing loaded models and datasets, or rolling back failed execution steps.
---

# Snapshot Management Skill

## Overview
The `snapshot-management` skill enables autonomous agents to capture atomic snapshots of sandbox runtime environments (including memory variables, loaded datasets, and filesystem state), restore saved checkpoints, and manage tree-based execution branches.

---

## Tool Reference

### `manage_snapshot`

**Parameters**:
- `action` *(string, required)*: Operation to perform: `"create"`, `"restore"`, `"list"`, or `"delete"`.
- `sandbox_id` *(string, optional)*: Identifier of the target sandbox. Required for `action: "create"`.
- `snapshot_id` *(string, optional)*: Identifier of the snapshot to restore or delete. Required for `action: "restore"` and `action: "delete"`.
- `name` *(string, optional)*: Human-readable label for the snapshot (used with `action: "create"`).
- `description` *(string, optional)*: Optional detailed notes describing the checkpoint state.

---

## Standard Step-by-Step Workflow

### Step 1: Create a Checkpoint Before Risky Operations
After completing an expensive computation or dataset loading phase, take a snapshot before running experimental or destructive code.

```json
{
  "tool": "manage_snapshot",
  "arguments": {
    "action": "create",
    "sandbox_id": "sb-e2b-4f91b2",
    "name": "post_dataset_cleaning",
    "description": "Cleaned records with 10k rows and computed summary metrics"
  }
}
```

**Response Example**:
```json
{
  "action": "create",
  "snapshot_id": "snap-9a02b18c",
  "sandbox_id": "sb-e2b-4f91b2",
  "name": "post_dataset_cleaning",
  "created_at": 1756430500.0,
  "status": "ready"
}
```
*Record the returned `snapshot_id` for potential rollback.*

---

### Step 2: Perform Experimental Transformations
Execute experimental modifications or complex heuristics in the sandbox:

```json
{
  "tool": "execute_code",
  "arguments": {
    "sandbox_id": "sb-e2b-4f91b2",
    "code": "# Experimental in-place filter that might drop too many rows\nfiltered_records = [r for r in raw_records if r['score'] > 95]\nraw_records = filtered_records\nprint(f'Remaining records: {len(raw_records)}')",
    "repl_mode": true
  }
}
```

---

### Step 3: Rollback on Failure or Regression
If the transformation drops too many records or corrupts data structures, instantly restore the checkpoint:

```json
{
  "tool": "manage_snapshot",
  "arguments": {
    "action": "restore",
    "sandbox_id": "sb-e2b-4f91b2",
    "snapshot_id": "snap-9a02b18c"
  }
}
```

**Response Example**:
```json
{
  "action": "restore",
  "snapshot_id": "snap-9a02b18c",
  "sandbox_id": "sb-e2b-4f91b2",
  "status": "restored",
  "message": "Sandbox execution state restored successfully to checkpoint 'post_dataset_cleaning'."
}
```

---

### Step 4: List Active Snapshots
Inspect available checkpoints to inspect branching points:

```json
{
  "tool": "manage_snapshot",
  "arguments": {
    "action": "list",
    "sandbox_id": "sb-e2b-4f91b2"
  }
}
```

---

### Step 5: Delete Obsolete Snapshots
Purge checkpoints that are no longer needed to reclaim storage:

```json
{
  "tool": "manage_snapshot",
  "arguments": {
    "action": "delete",
    "snapshot_id": "snap-9a02b18c"
  }
}
```

---

## Detailed References
- [Agent Branching & Tree Exploration Guide](references/branching.md)
