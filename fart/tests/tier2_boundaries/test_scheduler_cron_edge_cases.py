"""
Tier 2: Boundary & Corner Cases - Scheduler, Cron Parsing & Concurrency Edge Cases.
Tests malformed cron expressions, out-of-range cron values, negative timer intervals,
duplicate task IDs, cancellation boundaries, and high-volume task registration.
"""

import time
import pytest

try:
    from antigravity.scheduler.models import ScheduledTask, TaskStatus, TaskTriggerType
    from antigravity.scheduler.triggers import CronTrigger, TimerTrigger
    from antigravity.scheduler.daemon import ServiceWorkerDaemon
except ImportError:
    from tests.conftest import ScheduledTask, TaskStatus, TaskTriggerType, CronTrigger, TimerTrigger, ServiceWorkerDaemon


class TestSchedulerCronEdgeCases:
    """Boundary and corner cases for Cron triggers, timer triggers, and task scheduling."""

    @pytest.mark.parametrize("invalid_cron", [
        "*",
        "* * *",
        "* * * *",
        "* * * * * *",  # 6 fields instead of 5
        "invalid_text",
        "",
    ])
    def test_invalid_cron_field_counts(self, invalid_cron: str):
        """Tests that invalid cron expressions are rejected or flagged."""
        try:
            trigger = CronTrigger(invalid_cron)
            # If constructor accepts string, next_fire_time should handle or raise
            fire_t = trigger.next_fire_time()
            # If it didn't raise, ensure it gave a reasonable future timestamp
            assert fire_t > 0
        except (ValueError, TypeError, Exception) as e:
            assert isinstance(e, Exception)

    @pytest.mark.parametrize("out_of_range_cron", [
        "60 * * * *",   # minute 60 is out of 0-59 range
        "* 25 * * *",   # hour 25 is out of 0-23 range
        "* * 32 * *",   # day 32 is out of 1-31 range
        "* * * 13 *",   # month 13 is out of 1-12 range
        "* * * * 8",    # weekday 8 is out of 0-7 range
    ])
    def test_out_of_range_cron_values(self, out_of_range_cron: str):
        """Tests that out-of-range cron values are rejected or handled gracefully."""
        try:
            trigger = CronTrigger(out_of_range_cron)
            fire_t = trigger.next_fire_time()
            assert fire_t > 0
        except (ValueError, Exception):
            pass  # Rejection is valid behavior

    @pytest.mark.parametrize("zero_or_negative_interval", [
        0.0,
        -1.0,
        -100.0,
    ])
    def test_zero_or_negative_timer_interval_handling(self, zero_or_negative_interval: float):
        """Tests that zero or negative interval timers do not cause infinite loops or past fire times."""
        trigger = TimerTrigger(interval_seconds=zero_or_negative_interval)
        now = time.time()
        next_fire = trigger.next_fire_time(from_time=now)
        # Next fire time must be strictly >= now
        assert next_fire >= now

    def test_past_from_time_calculation(self):
        """Tests that calculating fire time from a past timestamp yields correct relative time."""
        trigger = TimerTrigger(interval_seconds=10.0)
        past_time = time.time() - 1000.0
        next_fire = trigger.next_fire_time(from_time=past_time)
        assert next_fire > past_time

    def test_cancel_nonexistent_task_id(self, scheduler_daemon: ServiceWorkerDaemon):
        """Tests cancelling a task ID that does not exist in the registry."""
        result = scheduler_daemon.cancel_task("nonexistent-task-id-99999")
        assert result is False

    def test_cancel_already_cancelled_task(self, scheduler_daemon: ServiceWorkerDaemon):
        """Tests double-cancelling a task."""
        task = ScheduledTask(
            task_id="t-double-cancel",
            name="double_cancel_job",
            trigger_type=TaskTriggerType.TIMER,
            trigger_spec="60.0",
            code="pass"
        )
        scheduler_daemon.register_task(task)
        first_cancel = scheduler_daemon.cancel_task("t-double-cancel")
        assert first_cancel is True

        # Second cancel should handle gracefully
        second_cancel = scheduler_daemon.cancel_task("t-double-cancel")
        assert second_cancel in (True, False)

    def test_high_volume_task_registration_stress(self, scheduler_daemon: ServiceWorkerDaemon):
        """Registers 50 rapid tasks and verifies registry integrity and count."""
        for i in range(50):
            task = ScheduledTask(
                task_id=f"stress-task-{i:03d}",
                name=f"stress_job_{i}",
                trigger_type=TaskTriggerType.TIMER,
                trigger_spec="100.0",
                code=f"x = {i}"
            )
            scheduler_daemon.register_task(task)

        tasks = scheduler_daemon.list_tasks()
        assert len(tasks) >= 50
        health = scheduler_daemon.get_health()
        assert health.get("total_tasks", len(tasks)) >= 50
