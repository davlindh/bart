## 2026-08-29T01:10:55Z
You are Challenger 2 for Milestone 1 (M1: MicroVM Sandbox & Execution Engine).

Working Directory: c:\Users\info\OneDrive\Dokument\GitHub\fart\.agents\challenger_m1_2
Workspace Root: c:\Users\info\OneDrive\Dokument\GitHub\fart

Mandatory Input Files (READ FIRST):
- c:\Users\info\OneDrive\Dokument\GitHub\fart\ORIGINAL_REQUEST.md
- c:\Users\info\OneDrive\Dokument\GitHub\fart\PROJECT.md
- c:\Users\info\OneDrive\Dokument\GitHub\fart\TEST_INFRA.md
- c:\Users\info\OneDrive\Dokument\GitHub\fart\.agents\worker_m1\handoff.md

Task:
1. Empirically challenge sandbox lifecycle resilience, concurrency, timeouts, memory stress, and crash recovery:
   - Infinite loop timeouts (`while True: pass`).
   - Deep recursion / stack overflow.
   - Subprocess abrupt termination (simulate crash / kill worker process) and recovery.
   - Rapid concurrent sandbox creation and destruction via `SandboxManager`.
   - Snapshot creation and multi-branch restoration.
2. Document all empirical tests and results.
3. Write your report to `c:\Users\info\OneDrive\Dokument\GitHub\fart\.agents\challenger_m1_2\challenge_report.md` and handoff report with verdict (APPROVE or REQUEST_CHANGES) to `c:\Users\info\OneDrive\Dokument\GitHub\fart\.agents\challenger_m1_2\handoff.md`.
4. Send completion message to parent.
