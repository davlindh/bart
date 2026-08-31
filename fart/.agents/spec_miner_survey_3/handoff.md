# Handoff Report: Phase 0 Specification Survey & Test Architecture (R5)

**Agent**: `spec_miner_survey_3`  
**Recipient**: `orchestrator_1` (Conversation ID: `c74fc08f-2125-4775-b9f1-d764acb37ebf`)  
**Workspace**: `c:\Users\info\OneDrive\Dokument\GitHub\fart`  
**Date**: 2026-08-29  

---

## 1. Observation

1. **Source Documents**:
   - `ORIGINAL_REQUEST.md`: Defines 5 core requirements (R1: MicroVM Sandbox & Execution Engine, R2: Antigravity MCP Server, R3: Antigravity Customization Plugin & Skill Suite, R4: Scheduled Background Service Worker Daemon, R5: Test Suite & Verification Harness) and acceptance criteria requiring 100% pytest pass and a runnable demo script (`ORIGINAL_REQUEST.md:14-50`).
   - `Öppen Källkod För Virtuella Maskiner.md`: Details modern agent execution architectures, combining reasoning frameworks (e.g. Hugging Face `smolagents`) with virtualization substrates (E2B Firecracker microVMs with ~150-200ms cold start, hardware KVM isolation, snapshots, and persistent REPL state). Emphasizes that local AST sandboxing (like `smolagents` `LocalPythonExecutor`) does not provide a true OS security boundary (vulnerabilities like CVE-2025-9959) and must be supplemented with microVM or isolated subprocess defense-in-depth (`Öppen Källkod För Virtuella Maskiner.md:1-61`).
2. **Host Environment**:
   - Python version: `Python 3.11.9` (`tags/v3.11.9:de54cf5`, 64-bit).
   - Pre-installed packages: `pytest 9.1.1`, `pydantic 2.13.4`, `packaging 26.3`, `pluggy 1.6.0`, `typing_extensions 4.16.0`.
3. **Workspace State**:
   - Workspace root currently contains `ORIGINAL_REQUEST.md` and `Öppen Källkod För Virtuella Maskiner.md`.
   - `.agents/` metadata directory initialized for agent coordination.

---

## 2. Logic Chain

1. **Isolation Architecture Requirement**: From Observation 1 (`Öppen Källkod För Virtuella Maskiner.md:13, 17, 33-40`), executing untrusted dynamic agent code requires a layered defense. For production / cloud execution, E2B Firecracker microVMs provide hardware-level KVM isolation, <200ms cold start, and state snapshots. For local offline environments where `E2B_API_KEY` is not present, a fallback sandbox with multi-level AST validation, prohibited dunder access detection, and subprocess execution timeouts is required to satisfy R1.
2. **Standard Packaging & Layout**: From Observation 2, Python 3.11 with `pydantic 2.13.4` and `pytest 9.1.1` is available on the system. Adopting a PEP 517/518/621 `pyproject.toml` layout with `src/antigravity_mcp`, `plugins/`, and `tests/` cleanly separates core library code from Antigravity plugin definitions and verification suites.
3. **Verification Harness Design (R5)**: To satisfy R5 and ensure 100% reliability:
   - *Tier 1 (Feature Coverage)*: Requires ≥5 tests per subsystem (Sandbox Engine, REPL Persistence, MCP Protocol/Tools, Plugin/Skill, and Worker Daemon) totaling ≥26 unit tests.
   - *Tier 2 (Boundary & Corner Cases)*: Probes edge cases including syntax errors, empty code, AST security breakouts (dunder traversal, forbidden imports), timeouts, invalid cron syntax, memory limits, and stdio disconnects.
   - *Tier 3 (Cross-Feature Combinations)*: Validates MCP-to-Sandbox tool pipelines, worker daemon driving sandboxed tasks, and fallback transitions.
   - *Tier 4 (Real-world Agent Workloads)*: Tests multi-turn REPL data analysis, periodic background cron health checks, and artifact file generation.
   - *Runnable Demo Script (`demo.py`)*: Integrates sandbox creation, multi-step code execution, worker scheduling, and clean resource teardown.

---

## 3. Caveats

1. **E2B MicroVM Cloud Access**: External E2B Firecracker microVM provisioning requires a valid `E2B_API_KEY` and outbound internet connectivity. All tests must verify both full E2B driver paths (with mocking where credentials are not provisioned) and the standalone `FallbackSandbox` to ensure the test suite passes 100% in all environments.
2. **Cron Scheduler Dependencies**: While `croniter` is standard for cron parsing, the worker scheduler implementation should incorporate a self-contained fallback parser to ensure resilience across different Python runtime distributions.

---

## 4. Conclusion

The specification mining and architectural mapping for Phase 0 is complete.
1. The VM isolation architecture, security threat model, and trade-off taxonomy are fully documented.
2. The project directory layout, Python packaging spec (`pyproject.toml`), and dependency requirements are established.
3. A comprehensive feature catalog (19 features) and edge case matrix (20 boundary cases) have been formulated.
4. The 4-tier test suite architecture (R5) and runnable `demo.py` specification have been detailed in `survey_report.md`.
The orchestrator can now proceed to Phase 1 decomposition and dual-track implementation.

---

## 5. Verification Method

1. **Inspect Survey Report**:
   - Check `c:\Users\info\OneDrive\Dokument\GitHub\fart\.agents\spec_miner_survey_3\survey_report.md` for complete feature and edge case tables, isolation comparative analysis, and 4-tier test matrices.
2. **Inspect Briefing & Progress**:
   - Check `c:\Users\info\OneDrive\Dokument\GitHub\fart\.agents\spec_miner_survey_3\BRIEFING.md` and `progress.md`.
3. **Execution Verification (Downstream Milestones)**:
   - When implementation commences, verify with:
     ```powershell
     python -m pytest -v tests/
     python demo.py
     ```
