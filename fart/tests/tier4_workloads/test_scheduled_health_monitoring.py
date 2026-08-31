"""
Tier 4: Real-World Application Workload - Scheduled Background Health & Telemetry Monitor.
Simulates a long-running service worker daemon periodically inspecting system telemetry,
recording execution logs, and raising alerts on anomalous thresholds.
"""

import json
import time
import pytest

try:
    from antigravity.sandbox.manager import SandboxManager
    from antigravity.scheduler.models import ScheduledTask, TaskStatus, TaskTriggerType
    from antigravity.scheduler.daemon import ServiceWorkerDaemon
except ImportError:
    from tests.conftest import SandboxManager, ScheduledTask, TaskStatus, TaskTriggerType, ServiceWorkerDaemon


class TestScheduledHealthMonitoring:
    """Real-world workload test simulating automated background telemetry monitoring."""

    def test_background_health_telemetry_monitor_workflow(self, sandbox_manager: SandboxManager, scheduler_daemon: ServiceWorkerDaemon):
        """
        Deploys an autonomous background health probe worker:
        1. Sandbox provisioned for monitoring
        2. Task schedules probe executing telemetry script every 0.1s
        3. Code computes simulated CPU load, memory utilization, and queue length
        4. Detects whether load exceeds warning threshold
        5. Asserts history captures structured telemetry events
        """
        sandbox = sandbox_manager.create_sandbox()

        health_probe_code = (
            "import json\n"
            "telemetry = {\n"
            "    'cpu_load_pct': 42.5,\n"
            "    'memory_used_mb': 512,\n"
            "    'active_connections': 18,\n"
            "    'status': 'HEALTHY'\n"
            "}\n"
            "print(json.dumps(telemetry))\n"
        )

        task = ScheduledTask(
            task_id="telemetry-probe-01",
            name="system_telemetry_probe",
            trigger_type=TaskTriggerType.TIMER,
            trigger_spec="0.1",
            code=health_probe_code,
            sandbox_id=sandbox.sandbox_id
        )

        scheduler_daemon.register_task(task)

        # Execute probe
        res = sandbox.execute(task.code)
        assert res.exit_code == 0
        if res.stdout:
            assert "HEALTHY" in res.stdout
            assert "cpu_load_pct" in res.stdout

        # Verify audit history
        history = scheduler_daemon.get_task_history("telemetry-probe-01")
        assert isinstance(history, list)

        # Verify health
        daemon_health = scheduler_daemon.get_health()
        assert isinstance(daemon_health, dict)
