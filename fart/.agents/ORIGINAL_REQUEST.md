# Original User Request

## 2026-08-29T02:35:47Z

<USER_REQUEST>
Build a production-grade disk-backed local persistence layer and a real local model inference engine (supporting NVIDIA Nemotron-Mini, NeMo architectures, and lightweight Transformer/GGUF/ONNX models without mock placeholders) integrated into the Antigravity Sandbox, MCP Server, and Service Worker platform.

Working directory: c:\Users\info\OneDrive\Dokument\GitHub\fart
Integrity mode: development

Reference material:
- Öppen Källkod För Virtuella Maskiner.md
- Antigravity Customization Guide (Skills, Rules, Plugins, MCP Tools)

## Requirements

### R1. Disk-Backed Local Persistence Store (src/antigravity/storage/)
Implement an SQLite and directory-backed persistence engine (PersistenceManager, DiskStateStore) that persists sandbox sessions, multi-branch snapshot state vectors, variable tables, scheduled worker task histories, and model configurations across restarts and process boundaries.

### R2. Real Local Model Inference Engine (src/antigravity/models/)
Implement a real local inference engine (LocalModelRunner, NemotronEngine) supporting NVIDIA Nemotron (e.g. nvidia/Nemotron-Mini-4B-Instruct, NeMo checkpoints) and lightweight real Transformer/GGUF/ONNX models using real weight loading, tokenization, chat templating, and CPU/GPU device placement. Do not use mock stubs.

### R3. Sandbox Integration & Security Whitelist
Integrate local model execution inside LocalSandbox with optimized memory handling and module whitelisting (torch, transformers, tokenizers, safetensors, onnxruntime, accelerate) in ast_security.py and builtins_sanitizer.py, enabling sandboxed scripts and background service workers to execute local model generation directly.

### R4. Antigravity MCP Tools & Skill Suite
Expose new MCP tools (load_model, model_generate, model_chat, persist_sandbox, restore_sandbox_disk, list_persisted_sandboxes) and package progressive disclosure skills (skills/local-inference/SKILL.md, skills/disk-persistence/SKILL.md) in the Antigravity customization plugin.

### R5. Comprehensive Verification & Test Suite
Provide full automated test suites (pytest) and an updated end-to-end demo script verifying disk persistence round-trips, real local model loading/inference, memory cleanup, and MCP tool execution.

## Acceptance Criteria

### Local Disk Persistence
- [ ] Sandbox state, snapshots, and variable registries can be serialized to disk (SQLite + filesystem) and restored in a completely new process.
- [ ] Service worker task registry and execution logs persist across daemon restarts.

### Real Local Model Execution
- [ ] Real local model runner successfully loads real weights/tokenizers and performs text generation and chat completions.
- [ ] Supports NVIDIA Nemotron / NeMo architecture specifications and lightweight models with configurable CPU / CUDA device selection.
- [ ] No mock model implementations are used for core inference execution.

### Sandbox & MCP Integration
- [ ] LocalSandbox can execute local model generation and inference scripts without AST security false-positives.
- [ ] MCP tools (load_model, model_generate, persist_sandbox, restore_sandbox_disk) return valid JSON-RPC responses.

### Verification
- [ ] pytest passes 100% of unit and integration tests across persistence, local model inference, sandbox execution, and MCP tools.
- [ ] demo.py demonstrates persisting a sandbox session to disk, loading a real local model, generating output, and restoring state.
</USER_REQUEST>
