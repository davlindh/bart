## 2026-08-29T06:27:09Z
You are a Worker implementing Milestone M7: Antigravity Extended MCP Tools & Customization Plugin Skill Suite (Requirement R4 and sandbox alias update).

Read:
- c:\Users\info\OneDrive\Dokument\GitHub\fart\.agents\ORIGINAL_REQUEST.md
- c:\Users\info\OneDrive\Dokument\GitHub\fart\PROJECT.md
- c:\Users\info\OneDrive\Dokument\GitHub\fart\.agents\spec_miner_survey_r4_r5\analysis.md

Your Working Directory is:
c:\Users\info\OneDrive\Dokument\GitHub\fart\.agents\worker_m7

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Scope and Write Ownership:
You own and must implement/update the following files:
1. `src/antigravity/sandbox/base.py`: Add `destroy = terminate` alias so both `destroy()` and `terminate()` work on `BaseSandbox`.
2. `src/antigravity/mcp/protocol.py`: Add domain error codes for models and persistence (`MODEL_NOT_FOUND = -32010`, `MODEL_LOAD_ERROR = -32011`, `MODEL_INFERENCE_ERROR = -32012`, `PERSISTENCE_NOT_FOUND = -32020`, `PERSISTENCE_WRITE_ERROR = -32021`, `PERSISTENCE_READ_ERROR = -32022`).
3. `src/antigravity/mcp/schemas.py`: Implement Pydantic input schemas (`LoadModelInput`, `ModelGenerateInput`, `ModelChatInput`, `PersistSandboxInput`, `RestoreSandboxDiskInput`, `ListPersistedSandboxesInput`) and add their full JSON schemas to `TOOL_SCHEMAS` (total 13 tools).
4. `src/antigravity/mcp/tools.py`: Implement the 6 new tool handlers (`_handle_load_model`, `_handle_model_generate`, `_handle_model_chat`, `_handle_persist_sandbox`, `_handle_restore_sandbox_disk`, `_handle_list_persisted_sandboxes`), initialize `LocalModelRunner` and `PersistenceManager` in `MCPToolRegistry`, and register all 13 tools in `self._tools`. Ensure robust error handling returning MCP-compliant error payloads on exceptions.
5. `plugins/antigravity-sandbox-plugin/plugin.json`: Update `"skills"` array to include `"skills/local-inference"` and `"skills/disk-persistence"`.
6. `plugins/antigravity-sandbox-plugin/rules/AGENTS.md`: Add comprehensive guidance sections for Local Model Inference (hardware detection, Nemotron formatting, temperature/sampling, memory cleanup) and Disk-Backed Persistence (WAL store, snapshot branching, variable serialization, state restoration).
7. `plugins/antigravity-sandbox-plugin/skills/local-inference/SKILL.md` + references:
   - `skills/local-inference/SKILL.md`
   - `skills/local-inference/references/nemotron-architecture.md`
   - `skills/local-inference/references/device-and-precision.md`
   - `skills/local-inference/references/chat-templates.md`
   - `skills/local-inference/references/generation-parameters.md`
8. `plugins/antigravity-sandbox-plugin/skills/disk-persistence/SKILL.md` + references:
   - `skills/disk-persistence/SKILL.md`
   - `skills/disk-persistence/references/session-persistence.md`
   - `skills/disk-persistence/references/snapshot-branching.md`
   - `skills/disk-persistence/references/worker-recovery.md`

Verification Requirement:
Run tests to verify that MCP tools and plugin configurations work properly.
Document commands and results in your handoff report at `c:\Users\info\OneDrive\Dokument\GitHub\fart\.agents\worker_m7\handoff.md`.
Send a completion message when finished.
