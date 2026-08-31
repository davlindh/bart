## 2026-08-29T01:06:31Z
You are the E2E Test Writer agent for the Antigravity project.

Your Working Directory: c:\Users\info\OneDrive\Dokument\GitHub\fart\.agents\test_writer_e2e
Workspace Root: c:\Users\info\OneDrive\Dokument\GitHub\fart

Mandatory Input Files (READ FIRST):
- c:\Users\info\OneDrive\Dokument\GitHub\fart\ORIGINAL_REQUEST.md
- c:\Users\info\OneDrive\Dokument\GitHub\fart\PROJECT.md
- c:\Users\info\OneDrive\Dokument\GitHub\fart\TEST_INFRA.md
- c:\Users\info\OneDrive\Dokument\GitHub\fart\.agents\spec_miner_survey_3\survey_report.md

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All test suites and fixtures must be genuine, comprehensive, and adhere strictly to opaque-box requirements. DO NOT create dummy tests or hardcode mock passes. A teamwork_preview_auditor will independently verify your work.

Exclusively Owned Files:
- `tests/` directory (all files under `tests/`)
- `TEST_READY.md` (publish when test suite is fully authored and structured)
- `demo.py` (runnable end-to-end demonstration script)

Task Description & Requirements:
1. Implement `tests/conftest.py` with standard Pytest fixtures:
   - Clean `SandboxManager` fixture with auto-cleanup of sandboxes on teardown.
   - `LocalSandbox` fixture.
   - `MockE2BSandbox` fixture / E2B driver mock.
   - Stdio MCP client pipe fixture for testing JSON-RPC tools.
   - `ServiceWorkerDaemon` fixture.
2. Author Tier 1 - Feature Coverage Tests (≥5 tests per subsystem):
   - `tests/tier1_features/test_sandbox_features.py` (creation, execution, stdout/stderr capture, returncode, state).
   - `tests/tier1_features/test_repl_features.py` (variable persistence across turns, multi-line functions, classes, imports).
   - `tests/tier1_features/test_mcp_features.py` (JSON-RPC protocol, tool listings, create_sandbox, execute_code, manage_snapshot, spawn_worker, pause/resume/destroy).
   - `tests/tier1_features/test_plugin_features.py` (plugin.json validation, mcp_config.json schema, SKILL.md progressive disclosure validation, AGENTS.md rules).
   - `tests/tier1_features/test_scheduler_features.py` (CronTrigger parsing, TimerTrigger delta, task registration, daemon event loop, task execution, history logging).
3. Author Tier 2 - Boundary & Corner Cases (≥5 per feature domain):
   - `tests/tier2_boundaries/test_ast_security_boundaries.py` (dunder traversal attacks, forbidden imports like os/subprocess/socket, syntax errors, empty code, dangerous builtins like eval/exec/open).
   - `tests/tier2_boundaries/test_sandbox_timeouts_and_errors.py` (infinite loops killed by timeout, division by zero, memory limit simulation, crash recovery).
   - `tests/tier2_boundaries/test_scheduler_cron_edge_cases.py` (invalid cron format, past triggers, zero-interval timers, task cancellations, high concurrency).
   - `tests/tier2_boundaries/test_mcp_protocol_boundaries.py` (malformed JSON-RPC, unknown tools, missing parameters, invalid sandbox IDs, disconnected stdio).
4. Author Tier 3 - Cross-Feature Combination Tests:
   - `tests/tier3_cross_feature/test_mcp_sandbox_pipeline.py` (agent calling MCP tools to create sandbox, execute code in REPL, capture artifacts, snapshot state, destroy sandbox).
   - `tests/tier3_cross_feature/test_scheduler_sandbox_pipeline.py` (scheduler daemon triggering periodic jobs that execute code inside sandboxes and log structured history).
   - `tests/tier3_cross_feature/test_fallback_degradation_pipeline.py` (automatic fallback from E2B to LocalSandbox when API keys/network are missing, verifying full execution continuity).
5. Author Tier 4 - Real-World Application Workloads:
   - `tests/tier4_workloads/test_agent_multi_turn_analysis.py` (multi-step data science scenario: calculate summary stats, transform dataset, extract base64 chart artifact).
   - `tests/tier4_workloads/test_scheduled_health_monitoring.py` (background daemon periodically checking sandbox health metrics and recording audit trail).
   - `tests/tier4_workloads/test_artifact_data_pipeline.py` (code execution creating CSV data and image artifacts, verifying proper extraction in result).
6. Author `demo.py`:
   - An end-to-end runnable script demonstrating:
     a. Sandbox manager initialization & sandbox creation (showing fallback / local execution).
     b. Multi-turn REPL code execution maintaining state.
     c. Registering and triggering a scheduled background worker with execution history inspection.
     d. Snapshot management & clean resource destruction.
7. Create `TEST_READY.md` at project root with test coverage summary, runner commands, and feature checklist.
