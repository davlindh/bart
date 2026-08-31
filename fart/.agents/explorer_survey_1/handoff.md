# Handoff Report: Technical Survey for R1 & R4

**From:** Explorer Survey Agent 1 (`explorer_survey_1`)  
**To:** Orchestrator (`orchestrator_1`)  
**Milestone:** Phase 0 (Survey & Scope Mapping)  
**Date:** 2026-08-29  

---

## 1. Observation

1. **Input Requirements:**
   - In `c:\Users\info\OneDrive\Dokument\GitHub\fart\ORIGINAL_REQUEST.md`:
     - Line 16-17: "### R1. MicroVM Sandbox & Execution Engine: Build a Python execution engine integrating E2B Firecracker microVM sandboxes with support for persistent REPL state, dynamic script execution, and a secure local fallback sandbox when E2B API keys or network access are unavailable."
     - Line 25-26: "### R4. Scheduled Background Service Worker Daemon: Implement a lightweight service worker manager and scheduler supporting recurring cron jobs and one-shot timer triggers for background agent tasks, event processing, and health monitoring."
     - Line 34-36: Acceptance criteria specify structured stdout/stderr, execution artifacts, exit status, AST validation & timeouts on local fallback, and persistent REPL state across sequential turns.
     - Line 44-45: Service worker daemon must register, trigger, and inspect scheduled jobs (cron expressions and duration timers), executing tasks in isolated sandboxes and logging histories.
2. **Reference Architecture:**
   - In `c:\Users\info\OneDrive\Dokument\GitHub\fart\Öppen Källkod För Virtuella Maskiner.md`:
     - Lines 12-13: Smolagents `CodeAgent` allows dynamic code execution with `additional_authorized_imports`, noting that simple local AST execution without hardware isolation has security vulnerabilities (e.g. CVE-2025-9959).
     - Lines 17-19: E2B provides hardware isolation via KVM/Firecracker with sub-200ms cold start, custom templates, pause/resume, and snapshotting (`createSnapshot()`).
     - Lines 26-27: Code interpreter maintains persistent REPL sessions across sequential turns; service workers run as event-driven execution processes.
3. **Workspace State:**
   - Directory listing shows a clean repository containing only `ORIGINAL_REQUEST.md`, `Öppen Källkod För Virtuella Maskiner.md`, and the `.agents/` metadata directory. No existing implementation code is present.

---

## 2. Logic Chain

1. **Dual-Tier Sandbox Architecture (R1):**
   - *Premise:* Based on Observation 1 (lines 16-17) and Observation 2 (lines 12-19), the execution engine must support cloud Firecracker microVMs when available, but MUST fail over seamlessly to a secure local sandbox when offline, without API keys, or in air-gapped CI.
   - *Deduction:* The engine requires a unified abstraction (`BaseSandbox`) with two implementations: `E2BSandbox` (wrapping `e2b-code-interpreter`) and `LocalSandbox` (using AST parsing + subprocess worker).
2. **Local Sandbox Security Strategy:**
   - *Premise:* Observation 2 (line 13) emphasizes that simple `eval`/`exec` AST filters can be breached via Python object model traversal (e.g. `__subclasses__`, `__globals__`).
   - *Deduction:* `LocalSandbox` requires a multi-layered defense:
     1. AST validation rejecting forbidden node types, module imports not in the whitelist, and any attribute lookups accessing dunder names starting with `__`.
     2. Sanitized runtime `__builtins__` removing `open`, `eval`, `exec`, `compile`, `globals`, `locals`, and wrapping `__import__` and `getattr`.
     3. Dedicated subprocess execution to isolate memory, prevent infinite loops via process-level timeouts, and isolate process signals.
3. **Multi-Turn Persistent REPL Mechanics:**
   - *Premise:* Observation 1 (line 36) requires REPL session state persistence across turns (`x = 10` followed by `y = x * 2`).
   - *Deduction:* In `LocalSandbox`, running standalone ephemeral scripts via `subprocess.run` on each turn would lose namespace variables unless pickled. However, pickle fails on unpicklable objects (lambdas, closures, open handles). Therefore, a long-lived subprocess worker communicating over JSON-RPC stdin/stdout that retains a live `session_globals` dictionary in memory is the optimal, robust architecture.
4. **Service Worker Daemon Architecture (R4):**
   - *Premise:* Observation 1 (lines 25-26, 44-45) requires cron expressions, duration timers, task registration, sandbox isolation, and execution logging.
   - *Deduction:* The daemon should utilize an AsyncIO non-blocking event loop managing a priority queue ordered by `next_run_at`. Trigger calculations use standard 5-field cron parsing (via `croniter` or built-in fallback) and one-shot delta timers. Worker jobs are dispatched to isolated sandboxes provisioned via `SandboxManager`, bounded by concurrency semaphores and timeouts, and logged to an execution history ring buffer.

---

## 3. Caveats

- **Operating System Subprocess Limits:** On Windows, POSIX-specific resource controls (`resource.setrlimit`) are not available. Local sandbox resource containment on Windows relies on `subprocess` execution timeouts, stream buffer limits, and process tree termination (`taskkill` / `Process.kill()`).
- **E2B API Key Availability:** In local development or automated CI environments without an `E2B_API_KEY`, E2B tests must either be skipped or mocked, with all core functionality validated against the `LocalSandbox` backend.
- **AST Whitelisting Strictness:** Highly restrictive AST whitelisting prevents unsafe code execution, but also prevents valid advanced Python features (e.g. complex metaclasses or file IO). The whitelist is intentionally scoped to data analysis, mathematical modeling, JSON processing, and agent logic.

---

## 4. Conclusion

The technical survey and design for R1 (MicroVM Sandbox & Execution Engine) and R4 (Scheduled Background Service Worker Daemon) is complete and fully documented in `survey_report.md`.
- **R1 Module Plan:** `antigravity.sandbox` implementing `BaseSandbox`, `E2BSandbox`, `LocalSandbox`, `ASTSecurityValidator`, `SanitizedBuiltins`, and `SandboxManager`.
- **R4 Module Plan:** `antigravity.scheduler` implementing `ServiceWorkerDaemon`, `ScheduledTask`, `CronTrigger`, `TimerTrigger`, `TaskRegistry`, and `HealthMonitor`.
- The architecture is modular, decoupled, cross-platform, testable, and ready for decomposition into Phase 1 implementation tasks.

---

## 5. Verification Method

To independently verify this survey and its findings:
1. **Inspect Report Artifacts:**
   - View `c:\Users\info\OneDrive\Dokument\GitHub\fart\.agents\explorer_survey_1\survey_report.md` to review the complete specifications, API contracts, data models, error tables, and module structures.
2. **Review AST & Security Specs:**
   - Confirm AST node whitelists and blocked dunder tables in Section 2.2 of `survey_report.md`.
3. **Review Class Signatures:**
   - Verify `BaseSandbox`, `ExecutionResult`, `ScheduledTask`, and `BaseSchedulerDaemon` interface definitions in Section 4 of `survey_report.md`.
4. **Subsequent Test Invalidation Condition:**
   - Once implemented in Milestone 1 & 2, run `pytest tests/test_sandbox/` and `pytest tests/test_scheduler/`. All tests must pass with 100% success on both Local and E2B (mocked/live) backends.
