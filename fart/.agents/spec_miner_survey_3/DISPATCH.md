## 2026-08-29T01:04:15Z

<USER_REQUEST>
You are a Spec Miner agent for Phase 0 (Survey & Scope Mapping) of the Antigravity MCP Server and Customization Plugin project.

Your Working Directory: c:\Users\info\OneDrive\Dokument\GitHub\fart\.agents\spec_miner_survey_3
Workspace Root: c:\Users\info\OneDrive\Dokument\GitHub\fart

Mandatory Input Files:
- c:\Users\info\OneDrive\Dokument\GitHub\fart\ORIGINAL_REQUEST.md (MUST READ FIRST)
- c:\Users\info\OneDrive\Dokument\GitHub\fart\Öppen Källkod För Virtuella Maskiner.md

Focus Area:
Investigate reference materials, exact system specifications, and requirement R5 (Test Suite & Verification Harness):
1. Extract and summarize all architectural patterns, best practices, and insights from `Öppen Källkod För Virtuella Maskiner.md` regarding microVMs, Firecracker, gVisor, WebAssembly, isolation boundaries, performance trade-offs, and security models.
2. Specification mining for project packaging, Python environment requirements (pyproject.toml, dependencies like mcp, e2b, croniter, pydantic, pytest), and directory layout.
3. Complete Test Suite Architecture & Verification Harness (R5):
   - Tier 1: Feature Coverage (≥5 per feature across sandbox, repl, mcp, plugin, worker daemon)
   - Tier 2: Boundary & Corner Cases (empty code, syntax errors, timeout limits, invalid cron expressions, memory leaks, AST security violations, missing API keys, disconnected stdio)
   - Tier 3: Cross-Feature Combinations (MCP tool calls driving sandbox execution, worker daemon triggering sandboxed code, fallback transitions)
   - Tier 4: Real-world Agent Workload Scenarios (multi-turn data analysis in REPL, background cron health check running periodic code, artifact generation)
   - Runnable end-to-end demo script specification demonstrating sandbox creation, code execution, worker scheduling, and resource cleanup.

Output Requirements:
- Write your comprehensive spec report to `c:\Users\info\OneDrive\Dokument\GitHub\fart\.agents\spec_miner_survey_3\survey_report.md`
- Write your structured handoff to `c:\Users\info\OneDrive\Dokument\GitHub\fart\.agents\spec_miner_survey_3\handoff.md`
- Include progress updates in `c:\Users\info\OneDrive\Dokument\GitHub\fart\.agents\spec_miner_survey_3\progress.md`
- Send completion message to parent when done.
</USER_REQUEST>
