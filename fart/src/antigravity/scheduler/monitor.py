"""
Health and Telemetry Monitoring System for the Service Worker Daemon.
"""

from __future__ import annotations

import time
from typing import Any, Dict, Optional

from .models import TaskStatus
from .registry import TaskRegistry


class HealthMonitor:
    """
    Health and telemetry inspection engine for the Service Worker Daemon.
    Provides system status, task counters, failure telemetry, and uptime metrics.
    """

    def __init__(self, registry: TaskRegistry, start_time: Optional[float] = None) -> None:
        self.registry = registry
        self.start_time = time.time() if start_time is None else start_time
        self.is_running = False

    def set_running(self, running: bool) -> None:
        """Update the running state flag."""
        self.is_running = running

    def get_telemetry(self) -> Dict[str, Any]:
        """
        Compile system health telemetry, active counts, failure metrics, and uptime.
        """
        tasks = self.registry.list_tasks()
        total_tasks = len(tasks)
        active_tasks = len([t for t in tasks if t.status in (TaskStatus.SCHEDULED, TaskStatus.PENDING)])
        running_tasks = len([t for t in tasks if t.status == TaskStatus.RUNNING])
        completed_tasks = len([t for t in tasks if t.status == TaskStatus.COMPLETED])
        failed_tasks = len([t for t in tasks if t.status == TaskStatus.FAILED])
        cancelled_tasks = len([t for t in tasks if t.status == TaskStatus.CANCELLED])

        # Execution stats across all task histories
        total_executions = 0
        failed_executions = 0
        for t in tasks:
            hist = self.registry.get_history(t.task_id)
            total_executions += len(hist)
            failed_executions += len([r for r in hist if not r.is_success])

        # Next upcoming scheduled run
        upcoming_runs = [
            t.next_run_at for t in tasks
            if t.status in (TaskStatus.SCHEDULED, TaskStatus.PENDING) and t.next_run_at is not None
        ]
        next_run = min(upcoming_runs) if upcoming_runs else None

        now = time.time()
        uptime = now - self.start_time

        return {
            "running": self.is_running,
            "status": "HEALTHY" if failed_tasks == 0 else "DEGRADED",
            "uptime_seconds": round(uptime, 3),
            "total_tasks": total_tasks,
            "active_tasks": active_tasks,
            "running_tasks": running_tasks,
            "completed_tasks": completed_tasks,
            "failed_tasks": failed_tasks,
            "cancelled_tasks": cancelled_tasks,
            "total_executions": total_executions,
            "failed_executions": failed_executions,
            "next_scheduled_run": next_run,
            "timestamp": now,
        }
