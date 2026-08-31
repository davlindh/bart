# Scheduled Worker & Daemon Recovery Protocol

## 1. Durable Worker Task Lifecycle
`ServiceWorkerDaemon` integrates directly with SQLite storage to ensure background worker tasks and execution history logs persist across daemon shutdowns, process crashes, and machine restarts.

---

## 2. Crash Recovery Workflow

1. **Task Registration**: When `spawn_worker` registers a task (e.g. cron `*/15 * * * *`), the schedule specification and code payload are committed to the `scheduled_tasks` table.
2. **Daemon Crash / Restart**: Upon daemon restart:
   - Daemon invokes `PersistenceManager.load_tasks()`.
   - Rehydrates active tasks (`TaskStatus.SCHEDULED`).
   - Recalculates `next_run_at` based on current system time and the trigger specification.
3. **Execution History Continuity**: Completed and failed execution records are preserved in `task_execution_records`. Historical runs can be queried via `get_task_history(task_id)` without gap loss.

---

## 3. Worker Durability Example

```python
from antigravity.storage import PersistenceManager
from antigravity.scheduler import ServiceWorkerDaemon
from antigravity.scheduler.models import ScheduledTask, TaskTriggerType

# 1. Daemon 1 registers recurring job
pm = PersistenceManager()
daemon1 = ServiceWorkerDaemon()
daemon1.register_task(
    ScheduledTask(
        task_id="task-monitor-01",
        name="Telemetry Heartbeat",
        trigger_type=TaskTriggerType.CRON,
        trigger_spec="*/5 * * * *",
        code="print('HEALTH_OK')",
    )
)

# 2. Simulate daemon restart
daemon2 = ServiceWorkerDaemon()
# Tasks automatically recovered from SQLite
recovered_tasks = pm.load_tasks()
assert len(recovered_tasks) >= 1
assert any(t.task_id == "task-monitor-01" for t in recovered_tasks)
```
