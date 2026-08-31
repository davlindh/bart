# Progress - spec_miner_survey_r4_r5

Last visited: 2026-08-29T06:25:30Z
Status: In Progress

## Current Step
- Surveying R4 (MCP Tools, Skills, Rules, Schemas) and R5 (Tests Tiers 1-5, Demo).
- Pytest running across existing test suite (216 tests).

## Findings Summary
1. **Requirement R4: Antigravity MCP Tools & Skill Suite**:
   - `src/antigravity/mcp/schemas.py`: Currently has 7 tools (`create_sandbox`, `execute_code`, `pause_sandbox`, `resume_sandbox`, `destroy_sandbox`, `manage_snapshot`, `spawn_worker`). Needs 6 new Pydantic input schemas and 6 new tool schema definitions in `TOOL_SCHEMAS`:
     - `load_model`
     - `model_generate`
     - `model_chat`
     - `persist_sandbox`
     - `restore_sandbox_disk`
     - `list_persisted_sandboxes`
   - `src/antigravity/mcp/tools.py`: Needs handlers `_handle_load_model`, `_handle_model_generate`, `_handle_model_chat`, `_handle_persist_sandbox`, `_handle_restore_sandbox_disk`, `_handle_list_persisted_sandboxes` registered in `self._tools` in `MCPToolRegistry`, wired to `LocalModelRunner` and `PersistenceManager`.
   - `plugins/antigravity-sandbox-plugin/plugin.json`: Needs `"skills"` array expanded to include `"skills/local-inference"` and `"skills/disk-persistence"`.
   - `plugins/antigravity-sandbox-plugin/rules/AGENTS.md`: Needs expanded operating directives for local model inference and disk-backed persistence.
   - `plugins/antigravity-sandbox-plugin/skills/`: Needs creation of:
     - `skills/local-inference/SKILL.md` + references (`nemotron-architecture.md`, `device-and-precision.md`, `chat-templates.md`, `generation-parameters.md`).
     - `skills/disk-persistence/SKILL.md` + references (`session-persistence.md`, `snapshot-branching.md`, `worker-recovery.md`).

2. **Requirement R5: Comprehensive Tests & Demo**:
   - Existing tests: 216 tests passing across existing modules.
   - Missing test suites for complete coverage:
     - Tier 1: `test_mcp_extended_tools.py`, `test_extended_plugin_skills.py`
     - Tier 2: `test_mcp_extended_boundaries.py`
     - Tier 3: `test_mcp_model_sandbox_pipeline.py`
     - Tier 4: `test_multi_turn_agent_with_local_model.py`
     - Tier 5: `test_adversarial_persistence_and_models.py`
   - `demo.py`: Needs update to demonstrate local model loading, generation, sandbox execution with persistence, multi-branch snapshot on disk, process boundary state restoration, and worker durability.
