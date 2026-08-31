"""Cross-feature integration tests: Scheduler TaskRegistry persistence and crash recovery."""

import tempfile
import time
from pathlib import Path
import pytest

from antigravity.scheduler.models import (
    ScheduledTask,
    TaskExecutionRecord,
    TaskStatus,
    TaskTriggerType,
)
from antigravity.scheduler.registry import TaskRegistry
from antigravity.storage.models import StorageConfig
from antigravity.storage.persistence_manager import PersistenceManager


@pytest.fixture
def temp_storage_dir():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
        yield Path(tmpdir)


class TestSchedulerPersistencePipeline:
    def test_task_registry_write_through_and_hydration(self, temp_storage_dir):
        config = StorageConfig(base_dir=str(temp_storage_dir))
        pm = PersistenceManager(config)

        registry1 = TaskRegistry(max_history_per_task=20, persistence_manager=pm)

        # 1. Register tasks
        t1 = ScheduledTask(
            task_id="task_cron_1",
            name="Daily Report",
            trigger_type=TaskTriggerType.CRON,
            trigger_spec="0 0 * * *",
            code="print('daily report')",
            status=TaskStatus.SCHEDULED,
        )
        t2 = ScheduledTask(
            task_id="task_timer_1",
            name="Heartbeat",
            trigger_type=TaskTriggerType.TIMER,
            trigger_spec="30",
            code="print('heartbeat')",
            status=TaskStatus.SCHEDULED,
        )

        registry1.register(t1)
        registry1.register(t2)

        # 2. Record executions
        exec1 = TaskExecutionRecord(
            task_id="task_timer_1",
            stdout="heartbeat ok",
            duration_ms=12.5,
            exit_code=0,
        )
        registry1.record_execution("task_timer_1", exec1)

        # Mark t1 as RUNNING (simulating process death mid-run)
        registry1.update_status("task_cron_1", TaskStatus.RUNNING)
        pm.close()

        # 3. Simulate process crash & restart with a fresh TaskRegistry
        pm2 = PersistenceManager(StorageConfig(base_dir=str(temp_storage_dir)))
        registry2 = TaskRegistry(max_history_per_task=20, persistence_manager=pm2, auto_hydrate=True)

        try:
            assert registry2.count() == 2

            # Verify task_timer_1
            t2_restored = registry2.get("task_timer_1")
            assert t2_restored is not None
            assert t2_restored.run_count == 1
            history_t2 = registry2.get_history("task_timer_1")
            assert len(history_t2) == 1
            assert history_t2[0].stdout == "heartbeat ok"

            # Verify crashed task_cron_1 was recovered
            t1_restored = registry2.get("task_cron_1")
            assert t1_restored is not None
            # Must be reset from RUNNING back to SCHEDULED
            assert t1_restored.status == TaskStatus.SCHEDULED
            history_t1 = registry2.get_history("task_cron_1")
            assert len(history_t1) == 1
            assert "Daemon process restarted while task was running" in history_t1[0].error
        finally:
            pm2.close()
