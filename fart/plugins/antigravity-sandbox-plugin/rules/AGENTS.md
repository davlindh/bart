# Antigravity Sandbox & Worker Operating Directives for Autonomous Agents

These rules govern how autonomous agents interact with isolated execution sandboxes, background service workers, and execution artifacts within the Antigravity platform.

---

## 1. Execution Philosophy: "Thinking in Code"
- **Computational Rigor**: Whenever an agent encounters quantitative calculations, data transformations, multi-step logic checks, or complex file parsing, write and execute Python code in the sandbox rather than computing mentally or hallucinating results.
- **Stateful Incrementalism**: Favor executing modular code snippets in the same persistent sandbox REPL session to reuse loaded datasets, expensive library imports, and intermediate variables across conversation turns.

---

## 2. Sandbox Lifecycle & Hygiene
- **Explicit Provisioning**: Always initialize a sandbox via `create_sandbox` before executing code. Specify appropriate execution parameters (`template`, `mode`, and `timeout_seconds`).
- **Resource Management**: Active sandboxes consume compute and memory. When an exploratory subtask, analysis turn, or mission milestone is completed, immediately invoke `destroy_sandbox` to prevent resource leaks and release system resources.
- **Resource Limits**: Default sandbox inactivity timeouts are configured to 300 seconds. Keep long-running background tasks out of interactive REPL loops and delegate them to background workers.

---

## 3. AST Security Constraints & Local Fallback Safety
- **Dual-Engine Model**: The engine seamlessly routes execution to E2B Firecracker microVMs when configured, and falls back to a secure local AST-validated sandbox in air-gapped or keyless environments.
- **AST Security Rules (Local Sandbox)**:
  - **Whitelisted Standard Libraries**: Approved safe modules include `math`, `datetime`, `json`, `re`, `collections`, `itertools`, `random`, `string`, `hashlib`, `statistics`, `dataclasses`, `enum`, `typing`, `urllib.parse`, `copy`, and data science packages (`numpy`, `pandas`, `polars`, `scipy`, `matplotlib`, `seaborn`).
  - **Prohibited Modules**: Direct system manipulation modules such as `os`, `sys`, `subprocess`, `shutil`, `socket`, `ctypes`, `builtins`, `importlib`, and `threading` are blocked.
  - **Forbidden Builtins & Dunders**: Dynamic code evaluation (`eval`, `exec`, `compile`, `open`, `globals`, `locals`, `__import__`) and introspective dunder escapes (`__subclasses__`, `__bases__`, `__mro__`, `__code__`, `__globals__`, `gi_frame`, `cr_frame`, `ag_frame`, `tb_frame`) are strictly prohibited and will trigger an `AST_SECURITY_VIOLATION`.
- **Zero Bypass Tolerance**: Never attempt to obfuscate forbidden calls through string manipulation or dynamic attribute resolution (`getattr`, `setattr`).

---

## 4. REPL Session State Retention Guidelines
- **Variable Persistence**: Variables, functions, and class definitions defined in prior execution turns remain active in the sandbox REPL context for subsequent calls within the same `sandbox_id`.
- **State Pollution Prevention**: Avoid redefining core variable names across unrelated computational steps. Use clean namespace conventions.
- **State Reset Protocol**: If the REPL environment becomes corrupted by invalid code or conflicting state, reset or re-create the sandbox rather than attempting ad-hoc manual cleanups.

---

## 5. Checkpointing & Snapshot Management
- **Pre-Mutation Checkpoints**: Before executing destructive, experimental, or memory-intensive transformations on loaded datasets, create a snapshot via `manage_snapshot(action="create", sandbox_id=...)`.
- **Atomic Rollback**: If an experimental execution step produces errors or unexpected regressions, restore the sandbox state using `manage_snapshot(action="restore", snapshot_id=...)`.
- **Branching Exploration**: Autonomous agents can branch their problem-solving trajectories across multiple snapshots to evaluate competing hypotheses.

---

## 6. Background Worker & Daemon Orchestration
- **No Blocking Sleeps**: Never run infinite loops, event loops, or blocking `time.sleep()` calls inside the interactive REPL.
- **Worker Delegation**: For recurring monitoring, periodic data polling, scheduled health checks, or asynchronous delayed tasks, use `spawn_worker`.
- **Trigger Types**:
  - `cron`: Standard 5-field cron expression (e.g., `*/5 * * * *` for every 5 minutes).
  - `timer`: Duration intervals (e.g., `300s`, `10m`) for one-shot delayed execution.
- **Worker Isolation**: Each background worker executes tasks within isolated sandbox instances, logging execution history to the daemon's ring buffer for inspection.

---

## 7. Artifact Extraction & Handling
- **Plot and Chart Capture**: When using visualization libraries (`matplotlib.pyplot`, `seaborn`, `plotly`), calling `plt.show()` automatically captures the figure as a base64-encoded `image/png` or SVG artifact returned in the tool response.
- **Tabular Data Capture**: Intermediate DataFrames and result matrices evaluated in REPL expressions are serialized into CSV/JSON tabular artifacts.
- **Generated File Sweep**: Files written to `/tmp/artifacts/` or the sandbox working directory are automatically indexed, MIME-typed, and returned in the structured tool execution result.

---

## 8. Error Recovery & Self-Correction Protocols
- **Structured Error Feedback**: Execution errors return `isError: true` accompanied by full Python tracebacks. Read the traceback line numbers and exception classes to formulate minimal, targeted fixes.
- **Timeout Watchdog**: Code execution exceeding `timeout_seconds` will be interrupted cleanly. Break long-running batch jobs into smaller chunks or delegate them to background service workers.
- **Fallback Transparency**: If microVM provisioning fails due to network or credential unavailability, the system automatically falls back to the local sandbox while maintaining consistent execution contracts.

---

## 9. Local Model Inference Directives
- **Hardware Awareness & Device Selection**: Check available compute hardware before requesting `device="cuda"`. In CPU-only environments, select `device="cpu"` or default to `device="auto"`. Use quantized formats (`int8`, `int4`, or `fp16`) on memory-constrained systems.
- **Model Lifecycle & Memory Management**: Resident open-weight models consume substantial RAM/VRAM. Do not hold multiple large models loaded simultaneously unless required for pipeline execution. Unload inactive models or offload unused checkpoints. In long-running REPL workflows, explicitly release tensors and call `gc.collect()` when finished.
- **Chat Templating & Formatting**: When invoking `model_chat`, always specify the appropriate template (`nemotron`, `chatml`, `llama3`, `mistral`) matching the loaded checkpoint family to prevent token degradation. For NVIDIA Nemotron models (e.g. `nvidia/Nemotron-Mini-4B-Instruct`), use the Nemotron chat template with proper `<extra_id_0>System`, `<extra_id_1>User`, and `<extra_id_1>Assistant` token roles.
- **Sampling & Temperature Tuning**: For deterministic reasoning, structured JSON generation, and code synthesis, set `temperature=0.0` or low temperatures (`0.1 - 0.3`) with `top_p=0.95`. For creative ideation, set `temperature=0.7 - 0.9`. Apply `repetition_penalty=1.1` to prevent degenerative token repetition loops.
- **In-Sandbox Model Execution**: In addition to tool calls (`load_model`, `model_generate`, `model_chat`), sandboxed Python scripts can directly import `antigravity.models.LocalModelRunner` and execute local inference natively without triggering AST security violations.

---

## 10. Disk Persistence & Session Durability Directives
- **Session Checkpointing**: Periodically call `persist_sandbox` to serialize active REPL namespaces, variable registries, and filesystem state into SQLite storage (`.antigravity/storage/` or custom `storage_path`). Always persist state before complex multi-step computations, context transfers, or worker delegation.
- **WAL Store & Concurrency**: The persistence subsystem operates using SQLite Write-Ahead Logging (WAL) and atomic file commits. Multi-threaded workers and daemon processes can write checkpoint records concurrently without database lock corruption.
- **Heterogeneous Variable Serialization**: The 4-tier serialization hierarchy automatically saves JSON-compatible objects, NumPy/PyTorch tensors via safetensors/npy, and safe Python primitives. Avoid storing unpickleable system handles (open file descriptors, network sockets, thread locks) in global REPL variables intended for disk serialization.
- **Snapshot Branching & Tree Navigation**: Capture snapshot states using `manage_snapshot(action="create")` or `PersistenceManager.save_snapshot()`. Use parent snapshot pointers to maintain a directed acyclic graph (DAG) of exploration branches. Navigate and restore alternative hypotheses using `manage_snapshot(action="restore")`.
- **State Restoration & Process Boundaries**: When restarting a workflow or transferring execution to a fresh worker process, query `list_persisted_sandboxes` to inspect available saved checkpoints, and restore state with `restore_sandbox_disk` to resume computation seamlessly with zero data loss.
