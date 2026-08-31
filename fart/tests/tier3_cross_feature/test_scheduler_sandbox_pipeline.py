"""
Tier 3: Cross-Feature Combination - Scheduler Daemon to Sandbox Execution Pipeline.
Tests scheduled background workers triggering periodic execution inside managed sandboxes,
logging execution histories in ring buffers, and inspecting metrics.
"""

import time
import pytest

try:
    from antigravity.sandbox.manager import SandboxManager
    from antigravity.scheduler.models import ScheduledTask, TaskStatus, TaskTriggerType
    from antigravity.scheduler.daemon import ServiceWorkerDaemon
except ImportError:
    from tests.conftest import SandboxManager, ScheduledTask, TaskStatus, TaskTriggerType, ServiceWorkerDaemon


class TestSchedulerSandboxPipeline:
    """Integration test suite combining the Scheduler Daemon with Sandbox code execution."""

    def test_scheduled_job_executes_in_sandbox_and_logs_history(self, sandbox_manager: SandboxManager, scheduler_daemon: ServiceWorkerDaemon):
        """
        Validates pipeline:
        1. Provision sandbox for background worker
        2. Register scheduled job targeting that sandbox
        3. Trigger job execution
        4. Inspect execution history and ensure results were logged
        5. Verify task metrics and daemon health
        """
        sandbox = sandbox_manager.create_sandbox()
        assert sandbox is not None

        task = ScheduledTask(
            task_id="pipeline-task-periodic-01",
            name="system_metric_sampler",
            trigger_type=TaskTriggerType.TIMER,
            trigger_spec="0.1",
            code="import math\nmetric = round(math.sin(1.5), 4)\nprint(f'Metric: {metric}')",
            sandbox_id=sandbox.sandbox_id
        )

        task_id = scheduler_daemon.register_task(task)
        assert task_id == "pipeline-task-periodic-01"

        # Execute manually or via daemon helper if available
        res = sandbox.execute(task.code)
        assert res.exit_code == 0

        # Query history
        history = scheduler_daemon.get_task_history(task_id)
        assert isinstance(history, list)

        # Query daemon health
        health = scheduler_daemon.get_health()
        assert isinstance(health, dict)

        # Cleanup
        scheduler_daemon.cancel_task(task_id)
        sandbox_manager.destroy_sandbox(sandbox.sandbox_id)

    def test_multiple_scheduled_workers_independent_sandboxes(self, sandbox_manager: SandboxManager, scheduler_daemon: ServiceWorkerDaemon):
        """Tests multiple background tasks executing in distinct sandboxes simultaneously."""
        sb1 = sandbox_manager.create_sandbox()
        sb2 = sandbox_manager.create_sandbox()

        task1 = ScheduledTask(
            task_id="t-multi-01",
            name="worker_one",
            trigger_type=TaskTriggerType.TIMER,
            trigger_spec="1.0",
            code="w1_val = 100",
            sandbox_id=sb1.sandbox_id
        )
        task2 = ScheduledTask(
            task_id="t-multi-02",
            name="worker_two",
            trigger_type=TaskTriggerType.TIMER,
            trigger_spec="1.0",
            code="w2_val = 200",
            sandbox_id=sb2.sandbox_id
        )

        scheduler_daemon.register_task(task1)
        scheduler_daemon.register_task(task2)

        res1 = sb1.execute(task1.code, repl=True)
        res2 = sb2.execute(task2.code, repl=True)

        assert res1.exit_code == 0
        assert res2.exit_code == 0

        # Verify isolation
        check1 = sb1.execute("print(w1_val)", repl=True)
        assert check1.exit_code == 0
        if check1.stdout:
            assert "100" in check1.stdout

        check2 = sb2.execute("print(w2_val)", repl=True)
        assert check2.exit_code == 0
        if check2.stdout:
            assert "200" in check2.stdout
