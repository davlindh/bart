# Original User Request

## 2026-08-29T01:03:30Z

Build an Antigravity MCP Server and Customization Plugin that provides isolated code execution via E2B Firecracker microVMs (with a local fallback sandbox) and orchestrates scheduled background service workers for autonomous agents.

Working directory: c:\Users\info\OneDrive\Dokument\GitHub\fart
Integrity mode: development

Reference material:
- Öppen Källkod För Virtuella Maskiner.md
- Antigravity Customization System (Skills, Rules, Plugins, MCP Servers)

## Requirements

### R1. MicroVM Sandbox & Execution Engine
Build a Python execution engine integrating E2B Firecracker microVM sandboxes with support for persistent REPL state, dynamic script execution, and a secure local fallback sandbox when E2B API keys or network access are unavailable.

### R2. Antigravity MCP Server
Implement a Model Context Protocol (MCP) server that exposes tools for sandbox lifecycle management (create_sandbox, execute_code, pause_sandbox, resume_sandbox, destroy_sandbox) and captures real-time outputs and artifacts.

### R3. Antigravity Customization Plugin & Skill Suite
Package the MCP server, Antigravity skills (SKILL.md), and workspace rules into a ready-to-use Antigravity customization plugin (.agents/ or plugins/) enabling seamless agent progressive disclosure and tool dispatch.

### R4. Scheduled Background Service Worker Daemon
Implement a lightweight service worker manager and scheduler supporting recurring cron jobs and one-shot timer triggers for background agent tasks, event processing, and health monitoring.

### R5. Test Suite & Verification Harness
Provide comprehensive automated test suites (pytest) verifying sandbox provisioning, code execution safety, fallback transitions, MCP protocol compliance, and scheduled worker execution.

## Acceptance Criteria

### Execution & Sandbox Safety
- [ ] Sandbox engine successfully executes Python code and returns structured stdout, stderr, execution artifacts, and exit status.
- [ ] Local fallback sandbox executes code securely with AST validation and timeouts when external microVM services are offline.
- [ ] REPL session maintains state across sequential code executions.

### MCP Server & Tool Integration
- [ ] MCP server implements standard MCP JSON-RPC protocol over stdio.
- [ ] All declared tools (create_sandbox, execute_code, manage_snapshot, spawn_worker) respond with valid MCP tool results and error schemas.
- [ ] Antigravity plugin manifest and skill definition (SKILL.md) correctly document tool parameters and usage workflows.

### Service Worker & Scheduler
- [ ] Service worker daemon can register, trigger, and inspect scheduled jobs (cron expressions and duration timers).
- [ ] Workers execute tasks in isolated sandboxes and log execution histories.

### Verification
- [ ] pytest passes 100% of unit and integration tests across all components.
- [ ] A runnable end-to-end demo script demonstrates creating a sandbox, running agent code, scheduling a worker, and cleaning up resources.
