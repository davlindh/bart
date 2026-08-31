---
name: worker-orchestration
description: Schedule and manage background service workers with cron expressions and one-shot duration timers. Use when scheduling periodic health checks, recurring data pipelines, delayed background tasks, or asynchronous daemon jobs.
---

# Worker Orchestration Skill

## Overview
The `worker-orchestration` skill provides autonomous agents with the ability to dispatch asynchronous, non-blocking tasks to the Antigravity Scheduled Background Service Worker Daemon. Workers execute code payloads in isolated sandbox environments on recurring schedules (`cron`) or delayed intervals (`timer`) without blocking the primary conversational flow.

---

## Tool Reference

### `spawn_worker`

**Parameters**:
- `task_name` *(string, required)*: Descriptive label for the background worker task.
- `code` *(string, required)*: Python code block to be executed on each trigger.
- `trigger_type` *(string, required)*: Modality of execution: `"cron"` (recurring schedule), `"timer"` (duration delay), or `"immediate"` (asynchronous background task).
- `trigger_spec` *(string, required)*: Standard 5-field cron expression (e.g., `"*/10 * * * *"`) or interval in seconds/duration (e.g., `"300s"`, `"10m"`, `"60"`).
- `max_iterations` *(integer, optional, default: 0 = unlimited)*: Maximum number of runs before auto-completing.
- `sandbox_template` *(string, optional, default: "python-3.11")*: Base sandbox template for worker execution.
- `env_vars` *(object, optional)*: Key-value map of environment variables passed into the worker sandbox.
- `timeout_seconds` *(integer, optional, default: 120)*: Maximum execution runtime allowed per individual run.

---

## Standard Scheduling Patterns

### Pattern 1: Recurring Health Check (Cron Trigger)
Schedule an automated system or API health probe every 5 minutes:

```json
{
  "tool": "spawn_worker",
  "arguments": {
    "task_name": "api_health_monitor",
    "trigger_type": "cron",
    "trigger_spec": "*/5 * * * *",
    "code": "import time, json\nstatus = {'check_time': time.time(), 'status': 'UP', 'latency_ms': 42}\nprint(f'Health Check Result: {json.dumps(status)}')",
    "max_iterations": 288,
    "timeout_seconds": 30
  }
}
```

**Response Example**:
```json
{
  "worker_id": "wrk-8f92a10b",
  "task_name": "api_health_monitor",
  "status": "scheduled",
  "trigger_type": "cron",
  "trigger_spec": "*/5 * * * *",
  "created_at": 1756430400.0,
  "next_run_at": 1756430700.0,
  "message": "Background worker successfully registered with scheduler daemon."
}
```

---

### Pattern 2: Delayed One-Shot Action (Timer Trigger)
Schedule a task to execute after a fixed cooldown period (e.g. 10 minutes):

```json
{
  "tool": "spawn_worker",
  "arguments": {
    "task_name": "cooldown_cache_invalidation",
    "trigger_type": "timer",
    "trigger_spec": "600s",
    "code": "print('10-minute cooldown expired. Invalidating cached aggregation indices.')",
    "timeout_seconds": 60
  }
}
```

---

### Pattern 3: Periodic Data Ingestion Pipeline
Run a daily batch synchronization job at 02:00 UTC:

```json
{
  "tool": "spawn_worker",
  "arguments": {
    "task_name": "daily_sync_job",
    "trigger_type": "cron",
    "trigger_spec": "0 2 * * *",
    "code": "print('Starting daily ETL synchronization...')\n# Ingest, transform, and persist records\nprint('Daily ETL synchronization complete.')",
    "timeout_seconds": 300
  }
}
```

---

## Worker Execution & Lifecycle Rules

1. **Task Idempotence**: Background worker scripts must be self-contained and idempotent. Ensure variables and imports required for execution are included in the code block.
2. **History Ring Buffer**: Each execution run logs its stdout, stderr, exit code, and execution duration into the daemon's bounded ring buffer.
3. **Graceful Error Handling**: If an individual run encounters a runtime error, the error is recorded in the task history, and the scheduler proceeds to calculate the next trigger time according to the schedule.

---

## Detailed References
- [Cron Syntax & Timer Formats Reference](references/cron-syntax.md)
