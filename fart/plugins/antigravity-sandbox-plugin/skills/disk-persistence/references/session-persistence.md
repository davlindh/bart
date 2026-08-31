# SQLite Schema & Heterogeneous Variable Codec

## 1. Storage Architecture
The disk persistence subsystem stores metadata, snapshot graphs, task registries, and small inline variables inside an SQLite database (`sandbox_states.db`), with large tensor buffers stored in a SHA-256 content-addressed directory structure (`blobs/`).

### Relational Tables:
1. `sandboxes`: Records active and persisted sandbox sessions, configuration JSON, work directories, and status.
2. `sandbox_variables`: Catalogs variable names, types, representations, inline data, and external blob references.
3. `snapshots`: Manages parent-child branch checkpoints, state vector manifests, and metadata.
4. `snapshot_variables`: Maps snapshot checkpoints to variable descriptors.
5. `scheduled_tasks`: Persists worker task triggers, cron specs, and run constraints.
6. `task_execution_records`: Logs worker execution runs, durations, outputs, and exit codes.
7. `models`: Persists model configurations, precision settings, and device placement.
8. `blob_references`: Tracks content-addressed hashes, refcounts, and byte sizes.

---

## 2. 4-Tier Variable Serialization Hierarchy

When saving namespace variables from a Python REPL, `VariableSerializer` routes each object through a 4-tier encoding strategy:

| Tier | Codec | Target Data Types | Storage Strategy |
| :--- | :--- | :--- | :--- |
| **Tier 1** | `json` | `int`, `float`, `str`, `bool`, `list`, `dict`, `None` | Serialized inline into SQLite column (`inline_data`) |
| **Tier 2** | `blob_safetensors` / `blob_npy` | NumPy `ndarray`, PyTorch `Tensor` | Saved to `blobs/{sha256}` via SafeTensors / binary `.npy` format |
| **Tier 3** | `blob_pickle` | Custom classes, dataclasses, Pandas DataFrames | Safe protocol-5 pickle stored in `blobs/{sha256}` |
| **Tier 4** | `unrestorable` | File descriptors, sockets, modules, thread locks | Serialized as non-rehydratable descriptor with `repr` string |

---

## 3. Direct Python Usage

```python
from antigravity.storage import PersistenceManager

pm = PersistenceManager(base_dir="./storage_demo")

# Save arbitrary variable dictionary
record = pm.save_sandbox(
    sandbox_id="sb-demo",
    variables={"a": 42, "data": [1, 2, 3]},
    metadata={"label": "baseline"},
)

# Reload in separate process
loaded_record, vars_dict = pm.load_sandbox("sb-demo")
assert vars_dict["a"] == 42
```
