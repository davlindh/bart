"""
Thread-safe in-memory task registry, indexer, and ring-buffer execution history store.
"""

from __future__ import annotations

import collections
import logging
import threading
import time
from typing import Any, Deque, Dict, List, Optional, Union

from .models import ScheduledTask, TaskExecutionRecord, TaskStatus, TaskTriggerType
from .triggers import CronTrigger, TimerTrigger

logger = logging.getLogger("antigravity.scheduler.registry")


class TaskRegistry:
    """
    Thread-safe registry for task storage, indexing, lookup, status updates,
    and ring-buffer execution history logging with optional SQLite persistence write-through.
    """

    def __init__(
        self,
        max_history_per_task: int = 50,
        persistence_manager: Optional[Any] = None,
        auto_hydrate: bool = True,
    ) -> None:
        self._tasks: Dict[str, ScheduledTask] = {}
        self._history: Dict[str, Deque[TaskExecutionRecord]] = {}
        self._lock = threading.RLock()
        self._max_history = max(1, max_history_per_task)
        self._persistence_manager = persistence_manager

        if self._persistence_manager is not None and auto_hydrate:
            self.hydrate_from_persistence()

    def hydrate_from_persistence(self) -> None:
        """Hydrate tasks and execution histories from attached PersistenceManager."""
        if self._persistence_manager is None:
            return

        with self._lock:
            try:
                tasks = self._persistence_manager.list_tasks()
                now = time.time()
                for task in tasks:
                    # Handle orphaned running tasks from prior process crash
                    if task.status == TaskStatus.RUNNING:
                        if task.max_runs is not None and task.run_count >= task.max_runs:
                            task.status = TaskStatus.FAILED
                        else:
                            task.status = TaskStatus.SCHEDULED

                        # Record crash notice in history
                        orphan_rec = TaskExecutionRecord(
                            task_id=task.task_id,
                            started_at=now,
                            finished_at=now,
                            exit_code=1,
                            error="Daemon process restarted while task was running",
                            sandbox_backend="local",
                        )
                        try:
                            self._persistence_manager.record_task_execution(task.task_id, orphan_rec)
                        except Exception as e:
                            logger.warning("Failed recording crash record for task %s: %s", task.task_id, e)

                    # Recompute next_run_at if scheduled
                    if task.status in (TaskStatus.SCHEDULED, TaskStatus.PENDING):
                        task.next_run_at = self.calculate_next_run(task, from_time=now)

                    try:
                        self._persistence_manager.save_task(task)
                    except Exception as e:
                        logger.warning("Failed saving refreshed task %s to DB: %s", task.task_id, e)

                    self._tasks[task.task_id] = task

                    # Load recent execution history
                    try:
                        hist = self._persistence_manager.get_task_history(
                            task.task_id, limit=self._max_history
                        )
                        self._history[task.task_id] = collections.deque(hist, maxlen=self._max_history)
                    except Exception as e:
                        logger.warning("Failed loading history for task %s: %s", task.task_id, e)
                        self._history[task.task_id] = collections.deque(maxlen=self._max_history)

            except Exception as e:
                logger.error("Failed hydrating task registry from persistence: %s", e)

    def register(self, task: ScheduledTask) -> str:
        """
        Store a scheduled task and initialize its history buffer and next_run_at.
        """
        with self._lock:
            # Calculate next_run_at if not explicitly set
            if task.next_run_at is None:
                task.next_run_at = self.calculate_next_run(task, from_time=time.time())

            self._tasks[task.task_id] = task
            if task.task_id not in self._history:
                self._history[task.task_id] = collections.deque(maxlen=self._max_history)

            if self._persistence_manager is not None:
                try:
                    self._persistence_manager.save_task(task)
                except Exception as e:
                    logger.error("Failed persisting registered task %s: %s", task.task_id, e)

            return task.task_id

    def get(self, task_id: str) -> Optional[ScheduledTask]:
        """Retrieve a task by ID."""
        with self._lock:
            return self._tasks.get(task_id)

    def list_tasks(self, status: Optional[Union[TaskStatus, str]] = None) -> List[ScheduledTask]:
        """List all tasks, optionally filtered by status."""
        with self._lock:
            if status is None:
                return list(self._tasks.values())
            if isinstance(status, str):
                try:
                    status = TaskStatus(status.lower())
                except ValueError:
                    pass
            return [t for t in self._tasks.values() if t.status == status]

    def cancel(self, task_id: str) -> bool:
        """Cancel a registered task. Returns True if task existed, False otherwise."""
        with self._lock:
            task = self._tasks.get(task_id)
            if task is not None:
                task.status = TaskStatus.CANCELLED
                if self._persistence_manager is not None:
                    try:
                        self._persistence_manager.save_task(task)
                    except Exception as e:
                        logger.error("Failed persisting cancelled task %s: %s", task_id, e)
                return True
            return False

    def update_status(self, task_id: str, status: TaskStatus) -> bool:
        """Update the status of a registered task."""
        with self._lock:
            task = self._tasks.get(task_id)
            if task is not None:
                task.status = status
                if self._persistence_manager is not None:
                    try:
                        self._persistence_manager.save_task(task)
                    except Exception as e:
                        logger.error("Failed persisting updated task status for %s: %s", task_id, e)
                return True
            return False

    def record_execution(
        self,
        task_id: str,
        record: Union[TaskExecutionRecord, Dict[str, Any], Any],
    ) -> None:
        """Append an execution record to the task's history ring buffer."""
        with self._lock:
            if not isinstance(record, TaskExecutionRecord):
                if isinstance(record, dict):
                    rec = TaskExecutionRecord(
                        task_id=task_id,
                        stdout=record.get("stdout", ""),
                        stderr=record.get("stderr", ""),
                        exit_code=record.get("exit_code", 0),
                        duration_ms=record.get("duration_ms", 0.0),
                        error=record.get("error"),
                        artifacts=record.get("artifacts", []),
                        state=record.get("state", {}),
                        sandbox_backend=record.get("backend_used", "local"),
                        backend_used=record.get("backend_used", "local"),
                        started_at=record.get("started_at", time.time()),
                        finished_at=record.get("finished_at"),
                    )
                else:
                    # Object like ExecutionResult
                    rec = TaskExecutionRecord(
                        task_id=task_id,
                        stdout=getattr(record, "stdout", ""),
                        stderr=getattr(record, "stderr", ""),
                        exit_code=getattr(record, "exit_code", 0),
                        duration_ms=getattr(record, "duration_ms", 0.0),
                        error=getattr(record, "error", None),
                        artifacts=getattr(record, "artifacts", []),
                        state=getattr(record, "state", {}),
                        sandbox_backend=getattr(record, "backend_used", "local"),
                        backend_used=getattr(record, "backend_used", "local"),
                    )
            else:
                rec = record

            if task_id not in self._history:
                self._history[task_id] = collections.deque(maxlen=self._max_history)
            self._history[task_id].append(rec)

            # Update task stats
            task = self._tasks.get(task_id)
            if task is not None:
                task.last_run_at = rec.started_at
                task.run_count += 1

            if self._persistence_manager is not None:
                try:
                    self._persistence_manager.record_task_execution(task_id, rec)
                except Exception as e:
                    logger.error("Failed persisting execution record for task %s: %s", task_id, e)

    def get_history(self, task_id: str, limit: Optional[int] = None) -> List[TaskExecutionRecord]:
        """Retrieve execution history for a task, up to optional limit."""
        with self._lock:
            history = list(self._history.get(task_id, []))
            if limit is not None and limit > 0:
                return history[-limit:]
            return history

    def get_due_tasks(self, now: Optional[float] = None) -> List[ScheduledTask]:
        """Retrieve all active tasks that are due for execution."""
        ref_time = time.time() if now is None else now
        with self._lock:
            due: List[ScheduledTask] = []
            for task in self._tasks.values():
                if task.status in (TaskStatus.SCHEDULED, TaskStatus.PENDING):
                    if task.next_run_at is not None and task.next_run_at <= ref_time:
                        due.append(task)
            return due

    def calculate_next_run(
        self,
        task: ScheduledTask,
        from_time: Optional[float] = None,
    ) -> Optional[float]:
        """Calculate the next trigger timestamp for a task based on its trigger spec."""
        ref_time = time.time() if from_time is None else from_time
        try:
            if task.trigger_type in (TaskTriggerType.CRON, "cron"):
                trigger = CronTrigger(task.trigger_spec)
                return trigger.next_fire_time(from_time=ref_time)
            elif task.trigger_type in (TaskTriggerType.TIMER, "timer"):
                trigger = TimerTrigger(interval_seconds=float(task.trigger_spec))
                return trigger.next_fire_time(from_time=ref_time)
        except Exception as e:
            logger.error("Failed calculating next run time for task %s: %s", task.task_id, e)
            return None
        return None

    def clear(self) -> None:
        """Clear all tasks and execution histories."""
        with self._lock:
            self._tasks.clear()
            self._history.clear()

    def count(self) -> int:
        """Total number of registered tasks."""
        with self._lock:
            return len(self._tasks)
