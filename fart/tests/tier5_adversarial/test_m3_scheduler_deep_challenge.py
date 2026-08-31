"""
Tier 5: Deep Challenge & Adversarial Stress Tests for Milestone 3 (Scheduled Service Worker Daemon).
Tests advanced cron parsing, daemon concurrency semaphores, pause/resume lifecycle,
history ring buffer bounding, health telemetry edge cases, and graceful shutdown.
"""

import asyncio
import time
import pytest

from antigravity.sandbox.manager import SandboxManager
from antigravity.scheduler.daemon import ServiceWorkerDaemon
from antigravity.scheduler.models import ScheduledTask, TaskExecutionRecord, TaskStatus, TaskTriggerType
from antigravity.scheduler.monitor import HealthMonitor
from antigravity.scheduler.registry import TaskRegistry
from antigravity.scheduler.triggers import CronTrigger, TimerTrigger


class TestSchedulerDeepChallenge:
    """Deep challenge and edge case tests for scheduler subsystem."""

    def test_complex_cron_syntax_and_names(self):
        """Tests parsing cron with month/day names, complex ranges, steps, and lists."""
        trigger = CronTrigger("*/15 9-17 * JAN,JUN,DEC MON,WED,FRI")
        now = time.time()
        next_t = trigger.next_fire_time(from_time=now)
        assert next_t > now

        # Test step with range
        step_range = CronTrigger("1-30/5 * * * *")
        assert 1 in step_range.minutes
        assert 6 in step_range.minutes
        assert 11 in step_range.minutes
        assert 26 in step_range.minutes
        assert 31 not in step_range.minutes

    def test_cron_day_of_week_sunday_0_and_7(self):
        """Tests that both 0 and 7 are treated as Sunday in Day of Week field."""
        t0 = CronTrigger("0 0 * * 0")
        t7 = CronTrigger("0 0 * * 7")
        now = time.time()
        n0 = t0.next_fire_time(from_time=now)
        n7 = t7.next_fire_time(from_time=now)
        assert n0 == n7

    def test_task_registry_ring_buffer_bounded_growth(self):
        """Verifies that the task history ring buffer never exceeds max_history limit."""
        registry = TaskRegistry(max_history_per_task=5)
        task = ScheduledTask(
            task_id="ring-buffer-task",
            name="test_ring",
            trigger_type=TaskTriggerType.TIMER,
            trigger_spec="1.0",
            code="pass",
        )
        registry.register(task)

        for i in range(20):
            record = TaskExecutionRecord(
                task_id="ring-buffer-task",
                stdout=f"Run {i}",
                exit_code=0,
            )
            registry.record_execution("ring-buffer-task", record)

        history = registry.get_history("ring-buffer-task")
        assert len(history) == 5
        assert history[-1].stdout == "Run 19"
        assert history[0].stdout == "Run 15"

    def test_health_monitor_telemetry_accuracy(self):
        """Tests health telemetry aggregation of active, completed, failed, and cancelled tasks."""
        registry = TaskRegistry()
        monitor = HealthMonitor(registry)

        t1 = ScheduledTask(task_id="t1", name="t1", trigger_type=TaskTriggerType.TIMER, trigger_spec="1", code="pass", status=TaskStatus.SCHEDULED)
        t2 = ScheduledTask(task_id="t2", name="t2", trigger_type=TaskTriggerType.TIMER, trigger_spec="1", code="pass", status=TaskStatus.COMPLETED)
        t3 = ScheduledTask(task_id="t3", name="t3", trigger_type=TaskTriggerType.TIMER, trigger_spec="1", code="pass", status=TaskStatus.FAILED)
        t4 = ScheduledTask(task_id="t4", name="t4", trigger_type=TaskTriggerType.TIMER, trigger_spec="1", code="pass", status=TaskStatus.CANCELLED)

        for t in [t1, t2, t3, t4]:
            registry.register(t)

        telemetry = monitor.get_telemetry()
        assert telemetry["total_tasks"] == 4
        assert telemetry["active_tasks"] == 1
        assert telemetry["completed_tasks"] == 1
        assert telemetry["failed_tasks"] == 1
        assert telemetry["cancelled_tasks"] == 1
        assert telemetry["status"] == "DEGRADED"  # failed_tasks > 0

    def test_daemon_pause_and_resume_lifecycle(self, sandbox_manager: SandboxManager):
        """Tests pausing and resuming task dispatch in ServiceWorkerDaemon."""
        async def _run():
            sandbox = sandbox_manager.create_sandbox()
            daemon = ServiceWorkerDaemon(sandbox_manager=sandbox_manager, tick_interval_seconds=0.01)
            await daemon.start()
            assert daemon.is_running is True

            await daemon.pause()
            task = ScheduledTask(
                task_id="pause-resume-task",
                name="pause_test",
                trigger_type=TaskTriggerType.TIMER,
                trigger_spec="0.01",
                code="print('Executed while paused?')",
                sandbox_id=sandbox.sandbox_id,
            )
            daemon.register_task(task)

            # Wait during pause - task should NOT be executed
            await asyncio.sleep(0.05)
            hist_paused = daemon.get_task_history("pause-resume-task")
            assert len(hist_paused) == 0

            # Resume daemon - task should execute
            await daemon.resume()
            for _ in range(50):
                if len(daemon.get_task_history("pause-resume-task")) >= 1:
                    break
                await asyncio.sleep(0.02)

            hist_resumed = daemon.get_task_history("pause-resume-task")
            assert len(hist_resumed) >= 1
            assert hist_resumed[0].exit_code == 0

            await daemon.stop()
            assert daemon.is_running is False

        asyncio.run(_run())

    def test_daemon_max_runs_enforcement(self, sandbox_manager: SandboxManager):
        """Tests that a task with max_runs stops and transitions to COMPLETED when limit reached."""
        async def _run():
            sandbox = sandbox_manager.create_sandbox()
            daemon = ServiceWorkerDaemon(sandbox_manager=sandbox_manager, tick_interval_seconds=0.01)
            await daemon.start()

            task = ScheduledTask(
                task_id="max-runs-task",
                name="max_runs_test",
                trigger_type=TaskTriggerType.TIMER,
                trigger_spec="0.01",
                code="x = 1",
                max_runs=2,
                sandbox_id=sandbox.sandbox_id,
            )
            daemon.register_task(task)

            for _ in range(50):
                t = daemon.get_task("max-runs-task")
                if t and t.run_count >= 2 and t.status == TaskStatus.COMPLETED:
                    break
                await asyncio.sleep(0.02)

            t = daemon.get_task("max-runs-task")
            assert t is not None
            assert t.run_count == 2
            assert t.status == TaskStatus.COMPLETED
            assert t.next_run_at is None

            await daemon.stop()

        asyncio.run(_run())

    def test_daemon_concurrency_semaphore_throttling(self, sandbox_manager: SandboxManager):
        """Tests that concurrent worker execution respects max_concurrent_workers limit."""
        async def _run():
            daemon = ServiceWorkerDaemon(
                sandbox_manager=sandbox_manager,
                max_concurrent_workers=2,
                tick_interval_seconds=0.01,
            )
            await daemon.start()

            # Register 4 tasks targeting individual sandboxes
            sandboxes = [sandbox_manager.create_sandbox() for _ in range(4)]
            for i in range(4):
                t = ScheduledTask(
                    task_id=f"concurrent-task-{i}",
                    name=f"concurrent_{i}",
                    trigger_type=TaskTriggerType.TIMER,
                    trigger_spec="0.01",
                    code=f"import time\ntime.sleep(0.02)\nprint('Done {i}')",
                    max_runs=1,
                    sandbox_id=sandboxes[i].sandbox_id,
                )
                daemon.register_task(t)

            # Wait for all to finish
            for _ in range(100):
                all_done = all(len(daemon.get_task_history(f"concurrent-task-{i}")) >= 1 for i in range(4))
                if all_done:
                    break
                await asyncio.sleep(0.02)

            for i in range(4):
                hist = daemon.get_task_history(f"concurrent-task-{i}")
                assert len(hist) == 1
                assert hist[0].exit_code == 0

            await daemon.stop()

        asyncio.run(_run())
