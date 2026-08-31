# Milestone M7 Handoff Report: Antigravity Extended MCP Tools & Customization Plugin Skill Suite

## 1. Observation
- **Baseline Investigation**:
  - `src/antigravity/sandbox/base.py` defined `terminate()` without a `destroy()` alias method, causing tests invoking `sandbox.destroy()` to raise `AttributeError: 'LocalSandbox' object has no attribute 'destroy'`.
  - `src/antigravity/mcp/protocol.py` lacked model and persistence domain error codes (`-32010` to `-32022`).
  - `src/antigravity/mcp/schemas.py` and `src/antigravity/mcp/tools.py` supported 7 baseline lifecycle and worker tools, but lacked the 6 extended model and persistence tools (`load_model`, `model_generate`, `model_chat`, `persist_sandbox`, `restore_sandbox_disk`, `list_persisted_sandboxes`).
  - `plugins/antigravity-sandbox-plugin/plugin.json` declared only 3 skills.
  - `plugins/antigravity-sandbox-plugin/skills/` lacked `local-inference/` and `disk-persistence/` skill suites.
  - `plugins/antigravity-sandbox-plugin/rules/AGENTS.md` lacked Sections 9 and 10 detailing local model inference and disk persistence directives.
- **Modifications Implemented**:
  1. `src/antigravity/sandbox/base.py`: Implemented `def destroy(self) -> None: self.terminate()` alias on `BaseSandbox`.
  2. `src/antigravity/mcp/protocol.py`: Added `MODEL_NOT_FOUND = -32010`, `MODEL_LOAD_ERROR = -32011`, `MODEL_INFERENCE_ERROR = -32012`, `PERSISTENCE_NOT_FOUND = -32020`, `PERSISTENCE_WRITE_ERROR = -32021`, `PERSISTENCE_READ_ERROR = -32022`, their `ERROR_MESSAGES` mappings, and exception classes.
  3. `src/antigravity/mcp/schemas.py`: Implemented Pydantic input schemas (`LoadModelInput`, `ModelGenerateInput`, `ChatMessageItem`, `ModelChatInput`, `PersistSandboxInput`, `RestoreSandboxDiskInput`, `ListPersistedSandboxesInput`) and added their JSON Schema declarations to `TOOL_SCHEMAS` (13 tools total).
  4. `src/antigravity/mcp/tools.py`: Integrated `PersistenceManager` and `LocalModelRunner` into `MCPToolRegistry`, registered all 13 tools, and implemented the 6 handlers (`_handle_load_model`, `_handle_model_generate`, `_handle_model_chat`, `_handle_persist_sandbox`, `_handle_restore_sandbox_disk`, `_handle_list_persisted_sandboxes`) with robust MCP domain error handling.
  5. `plugins/antigravity-sandbox-plugin/plugin.json`: Added `"skills/local-inference"` and `"skills/disk-persistence"` to skills array, updated keywords and bumped version to `0.2.0`.
  6. `plugins/antigravity-sandbox-plugin/rules/AGENTS.md`: Added Section 9 ("Local Model Inference Directives") and Section 10 ("Disk Persistence & Session Durability Directives").
  7. `plugins/antigravity-sandbox-plugin/skills/local-inference/`: Authored `SKILL.md` and 4 reference guides (`nemotron-architecture.md`, `device-and-precision.md`, `chat-templates.md`, `generation-parameters.md`).
  8. `plugins/antigravity-sandbox-plugin/skills/disk-persistence/`: Authored `SKILL.md` and 3 reference guides (`session-persistence.md`, `snapshot-branching.md`, `worker-recovery.md`).
  9. Added automated test suites:
     - `tests/tier1_features/test_mcp_extended_tools.py`
     - `tests/tier1_features/test_extended_plugin_skills.py`
     - `tests/tier2_boundaries/test_mcp_extended_boundaries.py`
     - `tests/tier3_cross_feature/test_mcp_model_sandbox_pipeline.py`

## 2. Logic Chain
- Providing `destroy()` as a direct alias for `terminate()` on `BaseSandbox` satisfies both API conventions across all sandbox subclasses (`LocalSandbox`, `E2BSandbox`).
- Mapping domain-specific errors (`ModelNotFoundError`, `PersistenceNotFoundError`, etc.) in `call_tool` produces well-structured JSON-RPC error responses rather than unhandled server crashes.
- Lazily initializing `PersistenceManager` and `LocalModelRunner` inside `MCPToolRegistry` preserves zero-overhead startup and seamless backward compatibility with existing tests and servers.
- Progressive disclosure skills (`skills/local-inference` and `skills/disk-persistence`) combined with Section 9/10 workspace directives in `AGENTS.md` instruct agents on device placement, Nemotron formatting, WAL concurrency, and snapshot DAG navigation.

## 3. Caveats
- When hardware acceleration (CUDA) is unavailable, `LocalModelRunner` executes on CPU or via the mathematical lightweight transformer engine.
- SQLite WAL mode ensures concurrent read/write durability across daemon processes; temporary memory-only SQLite databases (`:memory:`) do not persist across process boundaries unless a file path or directory is provided.

## 4. Conclusion
Milestone M7 (Requirement R4 and sandbox alias update) is completely implemented and verified. All 13 MCP tools function correctly with structured JSON-RPC responses, the customization plugin packages all 5 skills and rules, and 100% of tests pass across all tiers.

## 5. Verification Method
Execute the following verification command in the project root:
```bash
python -m pytest
```
**Observed Result**:
```
collected 231 items
======================= 231 passed in 204.66s (0:03:24) =======================
```
All 231 test items across Tiers 1–5 pass without error.
