# Multi-Branch Snapshot Directed Acyclic Graphs (DAGs)

## 1. Branching Exploration for Autonomous Agents
Complex problem solving frequently requires exploring multiple hypothesis trees without losing intermediate computational results. The snapshot DAG allows agents to fork state vectors into isolated branches.

```
       [root_snapshot] (Data Ingestion)
          /         \
         v           v
  [branch_linear]  [branch_tree] (Random Forest)
     (Regression)        |
                         v
                   [branch_tuned] (Optimized Hyperparameters)
```

---

## 2. Managing Snapshot Trees

### Create Root Snapshot
```json
{
  "tool": "manage_snapshot",
  "arguments": {
    "action": "create",
    "sandbox_id": "sb-ml-01",
    "name": "raw_dataset_loaded",
    "description": "Base dataset before normalization."
  }
}
```

### Fork & Explore Branch A
```json
{
  "tool": "execute_code",
  "arguments": {
    "sandbox_id": "sb-ml-01",
    "code": "from sklearn.preprocessing import StandardScaler\nscaler = StandardScaler()\nX_scaled = scaler.fit_transform(X)\nmodel_type = 'scaled_linear'",
    "repl_mode": true
  }
}
```
Create checkpoint on Branch A:
```json
{
  "tool": "manage_snapshot",
  "arguments": {
    "action": "create",
    "sandbox_id": "sb-ml-01",
    "name": "branch_linear_standardized"
  }
}
```

### Roll Back to Root & Explore Branch B
```json
{
  "tool": "manage_snapshot",
  "arguments": {
    "action": "restore",
    "sandbox_id": "sb-ml-01",
    "snapshot_id": "snap-root-id"
  }
}
```

---

## 3. Persistent DAG Inspection
`PersistenceManager.get_snapshot_tree(sandbox_id)` yields the complete hierarchy of nodes, parent references, branch names, and creation timestamps, enabling systematic tree traversal and branch comparison.
