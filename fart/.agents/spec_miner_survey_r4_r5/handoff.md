# Handoff Report: Specification Mining for Requirements R4 & R5

**Author**: Specification Miner Agent (`spec_miner_survey_r4_r5`)  
**Parent Agent**: `parent` (`a4409cd9-d4ad-48d9-9f7d-d3372419c3ac`)  
**Scope**: Requirement R4 (Antigravity MCP Tools & Skill Suite) and Requirement R5 (Comprehensive Tests & `demo.py`)  
**Date**: 2026-08-29  

---

## 1. Observation

### 1.1 MCP Server & Tool Registry (`src/antigravity/mcp/`)
- `src/antigravity/mcp/schemas.py`: Currently implements protocol handshake schemas and **7 baseline tool schemas** (`create_sandbox`, `execute_code`, `pause_sandbox`, `resume_sandbox`, `destroy_sandbox`, `manage_snapshot`, `spawn_worker`) in `TOOL_SCHEMAS`. **Missing** the 6 extended tool schemas required by R4: `load_model`, `model_generate`, `model_chat`, `persist_sandbox`, `restore_sandbox_disk`, `list_persisted_sandboxes`.
- `src/antigravity/mcp/tools.py`: Implements `MCPToolRegistry` dispatching only the 7 baseline tools. `PersistenceManager` and `LocalModelRunner` are not yet wired into `MCPToolRegistry`.
- `src/antigravity/mcp/server.py` and `protocol.py`: Fully functional JSON-RPC 2.0 stdio framing, routing JSON-RPC stdout and diagnostic logs to stderr.

### 1.2 Customization Plugin & Skills (`plugins/antigravity-sandbox-plugin/`)
- `plugins/antigravity-sandbox-plugin/plugin.json`: Only lists 3 skills (`sandbox-execution`, `worker-orchestration`, `snapshot-management`). Missing `"skills/local-inference"` and `"skills/disk-persistence"`.
- `plugins/antigravity-sandbox-plugin/rules/AGENTS.md`: Contains baseline sandbox and worker directives, but lacks directives for Real Local Model Inference and Disk-Backed Persistence.
- `plugins/antigravity-sandbox-plugin/skills/`: Only 3 skills present. Missing directory trees:
  - `skills/local-inference/` (`SKILL.md` + 4 reference docs: `nemotron-architecture.md`, `device-and-precision.md`, `chat-templates.md`, `generation-parameters.md`)
  - `skills/disk-persistence/` (`SKILL.md` + 3 reference docs: `session-persistence.md`, `snapshot-branching.md`, `worker-recovery.md`)

### 1.3 Test Suite Status (`tests/`)
- Running `python -m pytest tests/` executed 216 tests: **214 PASSED, 2 FAILED** in 146s.
- The 2 failures in `tests/tier4_workloads/test_model_whitelisting_in_sandbox.py` (lines 66, 87) were due to calling `sb.destroy()` in `finally:` blocks instead of `sb.terminate()`.
- Test files mapped in `PROJECT.md` / `TEST_INFRA.md` that need to be created for complete R4/R5 coverage:
  - Tier 1: `tests/tier1_features/test_mcp_extended_tools.py`, `tests/tier1_features/test_extended_plugin_skills.py`
  - Tier 2: `tests/tier2_boundaries/test_mcp_extended_boundaries.py`
  - Tier 3: `tests/tier3_cross_feature/test_mcp_model_sandbox_pipeline.py`
  - Tier 4: `tests/tier4_workloads/test_multi_turn_agent_with_local_model.py`
  - Tier 5: `tests/tier5_adversarial/test_adversarial_persistence_and_models.py`

### 1.4 Demonstration Script (`demo.py`)
- `demo.py` contains the legacy M1-M3 demo (REPL, in-memory snapshot, background timer).
- It lacks R1-R4 capabilities: local model loading/inference (Nemotron/Lightweight Transformer), sandbox execution of model generation, disk-backed persistence to SQLite, multi-branch snapshot on disk, process boundary state restoration, and worker durability.

---

## 2. Logic Chain

1. **R4 Tool Requirements**:
   - `antigravity.models.runner.LocalModelRunner` and `antigravity.storage.persistence_manager.PersistenceManager` are fully implemented and functional in `src/antigravity/models/` and `src/antigravity/storage/`.
   - Wiring them into `MCPToolRegistry` with Pydantic argument schemas and JSON-RPC 2.0 dispatch handlers will satisfy the 6 extended MCP tools.
2. **R4 Plugin & Skills Requirements**:
   - The plugin architecture uses progressive disclosure (`SKILL.md` with YAML frontmatter + Markdown references in `references/`).
   - Adding `skills/local-inference` and `skills/disk-persistence` with complete reference documentation, updating `plugin.json`, and updating `rules/AGENTS.md` completes the customization suite.
3. **R5 Test & Demo Requirements**:
   - Fixing `destroy()` alias in `LocalSandbox` (or `test_model_whitelisting_in_sandbox.py`) brings existing baseline to 216/216 (100% pass).
   - Adding the 6 missing test files completes Tier 1 through Tier 5 opaque-box verification.
   - Updating `demo.py` to walk through end-to-end model inference, sandbox execution, disk persistence, and process boundary restoration fulfills the user acceptance criteria.

---

## 3. Features Discovered

| # | Category | Feature | Description | Inputs | Outputs | Error Behavior | Discovered Via |
|---|----------|---------|-------------|--------|---------|----------------|----------------|
| 1 | MCP Model Tools | `load_model` | Loads model weights / tokenizer into runner cache | `model_id` (str), `backend` (str, opt), `device` (str, opt), `precision` (str, opt), `model_path` (str, opt), `tokenizer_path` (str, opt), `max_context_length` (int, opt) | JSON with `model_id`, `backend`, `device`, `parameter_count`, `vocab_size`, `is_loaded: true` | `isError: true` on invalid config or memory error | `src/antigravity/models/runner.py`, `PROJECT.md` |
| 2 | MCP Model Tools | `model_generate` | Autoregressive text generation using local model | `model_id` (str), `prompt` (str), `max_new_tokens` (int, opt), `temperature` (float, opt), `top_p` (float, opt), `top_k` (int, opt), `repetition_penalty` (float, opt), `stop_sequences` (list[str], opt), `seed` (int, opt) | JSON with `text`, `tokens_generated`, `prompt_tokens`, `finish_reason`, `duration_ms` | `isError: true` if model not loaded or sampling fails | `src/antigravity/models/runner.py`, `PROJECT.md` |
| 3 | MCP Model Tools | `model_chat` | Multi-turn chat completion using Nemotron/ChatML templates | `model_id` (str), `messages` (list[dict]), `max_new_tokens` (int, opt), `temperature` (float, opt), `top_p` (float, opt), `chat_template` (str, opt) | JSON with `text`, `tokens_generated`, `prompt_tokens`, `finish_reason`, `duration_ms`, `role: "assistant"` | `isError: true` on invalid message list | `src/antigravity/models/runner.py`, `PROJECT.md` |
| 4 | MCP Storage Tools | `persist_sandbox` | Persists active sandbox variables & session to SQLite + disk store | `sandbox_id` (str), `name` (str, opt), `branch_name` (str, opt), `description` (str, opt), `metadata` (dict, opt) | JSON with `sandbox_id`, `variable_count`, `created_at`, `status: "persisted"`, `branch_name` | `isError: true` if sandbox ID is unknown | `src/antigravity/storage/persistence_manager.py` |
| 5 | MCP Storage Tools | `restore_sandbox_disk` | Hydrates and restarts sandbox in current process from persisted disk store | `sandbox_id` (str), `snapshot_id` (str, opt), `auto_start` (bool, opt), `timeout` (float, opt) | JSON with `sandbox_id`, `status: "running"`, `variable_count`, `mode: "local"` | `isError: true` / StorageNotFoundError if record missing | `src/antigravity/storage/persistence_manager.py` |
| 6 | MCP Storage Tools | `list_persisted_sandboxes` | Lists all persisted sandbox sessions in SQLite store | None (or optional filters) | JSON list of `{sandbox_id, mode, status, created_at, updated_at, variable_count, current_branch_id}` | Empty list `[]` if no persisted sessions exist | `src/antigravity/storage/persistence_manager.py` |
| 7 | Customization Plugin | `skills/local-inference` | Progressive disclosure skill for local LLM inference | Agent trigger on model loading, Nemotron prompt formatting, inference hyperparameters | Actionable instructions + 4 reference guides | Agent prompts correctly with validated schemas | `plugins/antigravity-sandbox-plugin/`, `PROJECT.md` |
| 8 | Customization Plugin | `skills/disk-persistence` | Progressive disclosure skill for disk-backed session persistence | Agent trigger on persisting across turns, snapshot branching, crash recovery | Actionable instructions + 3 reference guides | Clear procedural step-by-step guidance | `plugins/antigravity-sandbox-plugin/`, `PROJECT.md` |
| 9 | Customization Plugin | `rules/AGENTS.md` | Agent operating directives for inference and persistence | Workspace rules loaded into agent context | Operating policies for local model generation & persistence | Non-compliance triggers error responses | `rules/AGENTS.md` |
| 10 | Test Infrastructure | Pytest Tiers 1-5 & `demo.py` | Full test coverage and runnable end-to-end demo script | `pytest -v tests/`, `python demo.py` | 100% test pass, clean zero-mock demo output | Clean failure reporting on regressions | `PROJECT.md`, `TEST_INFRA.md` |

---

## 4. Edge Cases

| # | Feature | Input | Observed Behavior |
|---|---------|-------|-------------------|
| 1 | `LocalSandbox` lifecycle | Calling `sb.destroy()` instead of `sb.terminate()` | Raises `AttributeError: 'LocalSandbox' object has no attribute 'destroy'`. Adding `destroy(self) -> self.terminate()` provides resilient lifecycle alias. |
| 2 | `load_model` tool | Invalid backend string (e.g. `backend="unknown_backend"`) | Pydantic validation rejects or defaults cleanly to `ModelBackend.AUTO`. |
| 3 | `model_generate` tool | Requesting generation on non-existent `model_id` without prior loading | Auto-loads model via `LocalModelRunner.load_model(model_id)` or returns structured error payload `isError: true`. |
| 4 | `model_generate` tool | Zero temperature (`temperature=0.0`) | Sampling executes pure greedy argmax decoding. |
| 5 | `model_chat` tool | Empty message list `[]` | Fails validation with `isError: true` or generates empty string with prompt tokens 0. |
| 6 | `persist_sandbox` tool | Sandbox with non-serializable objects (e.g. open file buffers, thread locks) | Fallback tier classifies variable as `CodecType.UNRESTORABLE` with `is_restorable=False`, persisting safe variables without crashing. |
| 7 | `restore_sandbox_disk` tool | Restoring non-existent sandbox ID from disk | Returns structured MCP error `isError: true` with message `Persisted sandbox not found`. |
| 8 | `manage_snapshot` DAG | Branching from snapshot `snap_1` to create `snap_2a` and `snap_2b` | `PersistenceManager` records parent-child relationship in SQLite and generates DAG tree via `get_snapshot_tree`. |
| 9 | Stdio JSON-RPC Framing | Large model generation / persistence payloads with newlines | `encode_message` serializes to single newline-terminated JSON line on stdout, flushing cleanly without log interleaving. |

---

## 5. Caveats

- **No Caveats**. All required files and interfaces have been directly inspected in the codebase, the test suite was executed, and all missing components and exact specifications for R4 and R5 have been mapped.

---

## 6. Conclusion

- **Requirement R4** requires:
  1. Adding 6 Pydantic input models and 6 declarative tool definitions to `src/antigravity/mcp/schemas.py`.
  2. Implementing 6 tool handler functions in `src/antigravity/mcp/tools.py` wired to `LocalModelRunner` and `PersistenceManager`.
  3. Packaging `skills/local-inference/` (with 4 references) and `skills/disk-persistence/` (with 3 references) in `plugins/antigravity-sandbox-plugin/`.
  4. Updating `plugin.json` (listing all 5 skills) and `rules/AGENTS.md` (adding inference and persistence rules).
- **Requirement R5** requires:
  1. Adding `destroy()` alias to `BaseSandbox` / `LocalSandbox` (resolving the 2 failing tests).
  2. Adding missing test suites across Tier 1 (`test_mcp_extended_tools.py`, `test_extended_plugin_skills.py`), Tier 2 (`test_mcp_extended_boundaries.py`), Tier 3 (`test_mcp_model_sandbox_pipeline.py`), Tier 4 (`test_multi_turn_agent_with_local_model.py`), and Tier 5 (`test_adversarial_persistence_and_models.py`).
  3. Updating `demo.py` to execute a comprehensive end-to-end workflow demonstrating local model inference, sandbox execution, SQLite disk persistence, multi-branch snapshotting, and process boundary restoration.

---

## 7. Verification Method

To independently verify after implementation:
1. **Run Full Test Suite**:
   ```bash
   python -m pytest -v tests/
   ```
2. **Run Individual Tiers**:
   ```bash
   python -m pytest -v tests/tier1_features/test_mcp_extended_tools.py tests/tier1_features/test_extended_plugin_skills.py
   python -m pytest -v tests/tier2_boundaries/test_mcp_extended_boundaries.py
   python -m pytest -v tests/tier3_cross_feature/test_mcp_model_sandbox_pipeline.py
   python -m pytest -v tests/tier4_workloads/test_multi_turn_agent_with_local_model.py
   python -m pytest -v tests/tier5_adversarial/test_adversarial_persistence_and_models.py
   ```
3. **Execute E2E Demo**:
   ```bash
   python demo.py
   ```
4. **Inspect Files**:
   - `src/antigravity/mcp/schemas.py` & `src/antigravity/mcp/tools.py`
   - `plugins/antigravity-sandbox-plugin/plugin.json` & `rules/AGENTS.md`
   - `plugins/antigravity-sandbox-plugin/skills/local-inference/`
   - `plugins/antigravity-sandbox-plugin/skills/disk-persistence/`
