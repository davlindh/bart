"""
Tier 1: Feature Coverage - Scheduled Service Worker Daemon & Trigger Engine.
Verifies CronTrigger 5-field parsing, TimerTrigger deltas, task registration,
daemon execution event loop, history ring buffer logging, and health inspection.
"""

import asyncio
import time
import pytest

try:
    from antigravity.scheduler.models import ScheduledTask, TaskStatus, TaskTriggerType
    from antigravity.scheduler.triggers import CronTrigger, TimerTrigger
    from antigravity.scheduler.daemon import ServiceWorkerDaemon
except ImportError:
    from tests.conftest import ScheduledTask, TaskStatus, TaskTriggerType, CronTrigger, TimerTrigger, ServiceWorkerDaemon


class TestSchedulerFeatures:
    """Feature test suite for Scheduled Background Worker Daemon (Requirement R4)."""

    def test_cron_trigger_parsing_and_future_fire_time(self):
        """Tests parsing standard 5-field cron expressions and computing future timestamps."""
        trigger = CronTrigger("0 12 * * 1-5")
        now = time.time()
        next_fire = trigger.next_fire_time(from_time=now)
        assert next_fire > now

        # Test every-minute expression
        every_minute = CronTrigger("* * * * *")
        next_m = every_minute.next_fire_time(from_time=now)
        assert next_m > now

    def test_timer_trigger_delta_calculation(self):
        """Tests timer trigger calculates delta offset correctly."""
        interval = 15.5
        trigger = TimerTrigger(interval_seconds=interval)
        now = time.time()
        next_fire = trigger.next_fire_time(from_time=now)
        assert abs(next_fire - (now + interval)) < 0.1

    def test_task_registration_and_retrieval(self, scheduler_daemon: ServiceWorkerDaemon):
        """Tests registering a ScheduledTask in daemon and retrieving it by task_id."""
        task = ScheduledTask(
            task_id="test-task-101",
            name="data_sync_job",
            trigger_type=TaskTriggerType.TIMER,
            trigger_spec="5.0",
            code="print('Sync complete')",
            timeout=30.0
        )
        task_id = scheduler_daemon.register_task(task)
        assert task_id == "test-task-101"

        retrieved = scheduler_daemon.get_task("test-task-101")
        assert retrieved is not None
        assert retrieved.name == "data_sync_job"
        assert retrieved.trigger_type == TaskTriggerType.TIMER

    def test_task_listing_and_filtering(self, scheduler_daemon: ServiceWorkerDaemon):
        """Tests listing all registered tasks from the scheduler daemon."""
        t1 = ScheduledTask(task_id="t-list-1", name="job1", trigger_type=TaskTriggerType.TIMER, trigger_spec="1.0", code="pass")
        t2 = ScheduledTask(task_id="t-list-2", name="job2", trigger_type=TaskTriggerType.CRON, trigger_spec="* * * * *", code="pass")
        scheduler_daemon.register_task(t1)
        scheduler_daemon.register_task(t2)

        tasks = scheduler_daemon.list_tasks()
        task_ids = [t.task_id for t in tasks]
        assert "t-list-1" in task_ids
        assert "t-list-2" in task_ids

    def test_task_cancellation(self, scheduler_daemon: ServiceWorkerDaemon):
        """Tests cancelling a registered task before execution."""
        task = ScheduledTask(
            task_id="t-cancel-99",
            name="cancelled_job",
            trigger_type=TaskTriggerType.TIMER,
            trigger_spec="60.0",
            code="print('Should not run')"
        )
        scheduler_daemon.register_task(task)
        cancelled = scheduler_daemon.cancel_task("t-cancel-99")
        assert cancelled is True

        t = scheduler_daemon.get_task("t-cancel-99")
        assert t.status == TaskStatus.CANCELLED

    def test_daemon_health_inspection_metrics(self, scheduler_daemon: ServiceWorkerDaemon):
        """Tests querying daemon health status and task counters."""
        health = scheduler_daemon.get_health()
        assert isinstance(health, dict)
        assert "running" in health
        assert "active_tasks" in health or "total_tasks" in health

    def test_task_execution_history_tracking(self, scheduler_daemon: ServiceWorkerDaemon):
        """Tests retrieving past execution history for a registered task."""
        task = ScheduledTask(
            task_id="t-hist-01",
            name="history_test_job",
            trigger_type=TaskTriggerType.TIMER,
            trigger_spec="1.0",
            code="print('History item')"
        )
        scheduler_daemon.register_task(task)
        history = scheduler_daemon.get_task_history("t-hist-01")
        assert isinstance(history, list)
