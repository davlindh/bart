"""
Asynchronous Service Worker Daemon executing scheduled tasks inside isolated sandboxes.
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional, Set, Union

from antigravity.sandbox.base import BaseSandbox
from antigravity.sandbox.manager import SandboxManager
from antigravity.sandbox.models import ExecutionResult, SandboxMode

from .models import ScheduledTask, TaskExecutionRecord, TaskStatus, TaskTriggerType
from .monitor import HealthMonitor
from .registry import TaskRegistry

logger = logging.getLogger("antigravity.scheduler.daemon")


class ServiceWorkerDaemon:
    """
    Asynchronous Background Service Worker Daemon.

    Manages scheduled cron and timer background tasks, provisions or binds
    to sandboxes via SandboxManager, executes task payloads, logs history records,
    advances schedules, and exposes telemetry/health metrics.
    """

    def __init__(
        self,
        sandbox_manager: Optional[SandboxManager] = None,
        max_concurrent_workers: int = 5,
        tick_interval_seconds: float = 0.05,
    ) -> None:
        self.sandbox_manager = sandbox_manager or SandboxManager()
        self.registry = TaskRegistry()
        self.monitor = HealthMonitor(self.registry)
        self.max_concurrent_workers = max(1, max_concurrent_workers)
        self.tick_interval_seconds = tick_interval_seconds

        self._running = False
        self._paused = False
        self._daemon_task: Optional[asyncio.Task] = None
        self._semaphore: Optional[asyncio.Semaphore] = None
        self._active_worker_tasks: Set[asyncio.Task] = set()

    @property
    def is_running(self) -> bool:
        """Returns True if the background daemon loop is running."""
        return self._running

    async def start(self) -> None:
        """Start the background scheduler event loop."""
        if self._running:
            return

        self._running = True
        self._paused = False
        self.monitor.set_running(True)
        self._semaphore = asyncio.Semaphore(self.max_concurrent_workers)
        self._daemon_task = asyncio.create_task(
            self._scheduler_loop(),
            name="scheduler-daemon-loop",
        )
        logger.info("ServiceWorkerDaemon started.")

    async def stop(self, timeout: float = 5.0) -> None:
        """Gracefully stop the daemon and wait for running workers to complete."""
        if not self._running:
            return

        logger.info("Stopping ServiceWorkerDaemon...")
        self._running = False
        self.monitor.set_running(False)

        if self._daemon_task and not self._daemon_task.done():
            self._daemon_task.cancel()
            try:
                await asyncio.wait_for(self._daemon_task, timeout=1.0)
            except (asyncio.CancelledError, asyncio.TimeoutError):
                pass

        if self._active_worker_tasks:
            pending = [t for t in self._active_worker_tasks if not t.done()]
            if pending:
                try:
                    await asyncio.wait_for(
                        asyncio.gather(*pending, return_exceptions=True),
                        timeout=timeout,
                    )
                except asyncio.TimeoutError:
                    for t in pending:
                        t.cancel()

        self._active_worker_tasks.clear()
        logger.info("ServiceWorkerDaemon stopped cleanly.")

    async def pause(self) -> None:
        """Pause task dispatching without shutting down the daemon."""
        self._paused = True

    async def resume(self) -> None:
        """Resume task dispatching."""
        self._paused = False

    def register_task(self, task: ScheduledTask) -> str:
        """Register a new scheduled task."""
        return self.registry.register(task)

    def cancel_task(self, task_id: str) -> bool:
        """Cancel a registered task."""
        return self.registry.cancel(task_id)

    def get_task(self, task_id: str) -> Optional[ScheduledTask]:
        """Retrieve task details by ID."""
        return self.registry.get(task_id)

    def list_tasks(self, status: Optional[Union[TaskStatus, str]] = None) -> List[ScheduledTask]:
        """List all tasks, optionally filtered by status."""
        return self.registry.list_tasks(status)

    def get_task_history(
        self,
        task_id: str,
        limit: Optional[int] = None,
    ) -> List[TaskExecutionRecord]:
        """Retrieve execution history for a task."""
        return self.registry.get_history(task_id, limit=limit)

    def record_task_result(
        self,
        task_id: str,
        result: Union[ExecutionResult, TaskExecutionRecord, Dict[str, Any]],
    ) -> None:
        """Manually record an execution result for a task."""
        self.registry.record_execution(task_id, result)

    def get_health(self) -> Dict[str, Any]:
        """Retrieve daemon health and telemetry metrics."""
        telemetry = self.monitor.get_telemetry()
        telemetry["running"] = self._running
        return telemetry

    def get_metrics(self) -> Dict[str, Any]:
        """Alias for get_health()."""
        return self.get_health()

    async def execute_task_now(self, task_id: str) -> Optional[TaskExecutionRecord]:
        """Manually trigger and execute a task immediately."""
        task = self.registry.get(task_id)
        if task is None:
            return None
        return await self.execute_task_pipeline(task)

    def execute_task_sync(self, task_id: str) -> Optional[TaskExecutionRecord]:
        """Synchronously execute a task in the current thread."""
        task = self.registry.get(task_id)
        if task is None:
            return None
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Run via thread/sync helper
                return self._execute_task_direct(task)
            else:
                return loop.run_until_complete(self.execute_task_pipeline(task))
        except RuntimeError:
            return self._execute_task_direct(task)

    def _execute_task_direct(self, task: ScheduledTask) -> TaskExecutionRecord:
        """Direct synchronous execution helper."""
        start_t = time.time()
        ephemeral_sandbox = False
        sandbox: Optional[BaseSandbox] = None

        try:
            if task.sandbox_id:
                sandbox = self.sandbox_manager.get_sandbox(task.sandbox_id)

            if sandbox is None:
                sandbox = self.sandbox_manager.create_sandbox(
                    mode=SandboxMode.AUTO,
                    timeout=task.timeout + 10.0,
                )
                ephemeral_sandbox = True

            timeout = task.timeout if task.timeout > 0 else 60.0
            exec_res = sandbox.execute(task.code, "python", timeout, True)

            end_t = time.time()
            duration_ms = (end_t - start_t) * 1000.0

            record = TaskExecutionRecord(
                task_id=task.task_id,
                started_at=start_t,
                finished_at=end_t,
                duration_ms=duration_ms,
                exit_code=exec_res.exit_code,
                stdout=exec_res.stdout,
                stderr=exec_res.stderr,
                result=getattr(exec_res, "result", None),
                results=getattr(exec_res, "results", []),
                error=exec_res.error,
                artifacts=exec_res.artifacts,
                state=exec_res.state,
                sandbox_backend=getattr(sandbox, "mode", SandboxMode.LOCAL).value,
                backend_used=getattr(sandbox, "mode", SandboxMode.LOCAL).value,
            )
        except Exception as e:
            end_t = time.time()
            duration_ms = (end_t - start_t) * 1000.0
            logger.error("Error executing task %s directly: %s", task.task_id, e)
            record = TaskExecutionRecord(
                task_id=task.task_id,
                started_at=start_t,
                finished_at=end_t,
                duration_ms=duration_ms,
                exit_code=1,
                error=str(e),
                stderr=f"Task execution failed: {e}",
            )
        finally:
            if ephemeral_sandbox and sandbox is not None:
                try:
                    self.sandbox_manager.destroy_sandbox(sandbox.sandbox_id)
                except Exception:
                    pass

        self.registry.record_execution(task.task_id, record)
        return record

    async def _scheduler_loop(self) -> None:
        """Main background event loop inspecting due tasks and dispatching executions."""
        while self._running:
            try:
                if not self._paused:
                    now = time.time()
                    due_tasks = self.registry.get_due_tasks(now=now)
                    for task in due_tasks:
                        # Mark running immediately to prevent duplicate dispatch in subsequent tick
                        self.registry.update_status(task.task_id, TaskStatus.RUNNING)
                        worker_task = asyncio.create_task(
                            self._dispatch_task_with_semaphore(task)
                        )
                        self._active_worker_tasks.add(worker_task)
                        worker_task.add_done_callback(self._active_worker_tasks.discard)

                await asyncio.sleep(self.tick_interval_seconds)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Unexpected error in scheduler loop: %s", e)
                await asyncio.sleep(self.tick_interval_seconds)

    async def _dispatch_task_with_semaphore(self, task: ScheduledTask) -> TaskExecutionRecord:
        """Acquire concurrency semaphore and execute task pipeline."""
        if self._semaphore is None:
            self._semaphore = asyncio.Semaphore(self.max_concurrent_workers)

        async with self._semaphore:
            return await self.execute_task_pipeline(task)

    async def execute_task_pipeline(self, task: ScheduledTask) -> TaskExecutionRecord:
        """
        Execute a scheduled task:
        1. Provision or attach to sandbox
        2. Execute task code asynchronously with timeout
        3. Capture structured results into TaskExecutionRecord
        4. Advance schedule or mark completed
        """
        start_t = time.time()
        ephemeral_sandbox = False
        sandbox: Optional[BaseSandbox] = None
        record: TaskExecutionRecord

        try:
            # 1. Resolve or provision sandbox
            if task.sandbox_id:
                sandbox = self.sandbox_manager.get_sandbox(task.sandbox_id)

            if sandbox is None:
                sandbox = self.sandbox_manager.create_sandbox(
                    mode=SandboxMode.AUTO,
                    timeout=task.timeout + 10.0,
                )
                ephemeral_sandbox = True

            # 2. Execute code in sandbox in separate worker thread
            timeout = task.timeout if task.timeout > 0 else 60.0
            exec_res = await asyncio.to_thread(
                sandbox.execute,
                task.code,
                "python",
                timeout,
                True,
            )

            end_t = time.time()
            duration_ms = (end_t - start_t) * 1000.0

            record = TaskExecutionRecord(
                task_id=task.task_id,
                started_at=start_t,
                finished_at=end_t,
                duration_ms=duration_ms,
                exit_code=exec_res.exit_code,
                stdout=exec_res.stdout,
                stderr=exec_res.stderr,
                result=getattr(exec_res, "result", None),
                results=getattr(exec_res, "results", []),
                error=exec_res.error,
                artifacts=exec_res.artifacts,
                state=exec_res.state,
                sandbox_backend=getattr(sandbox, "mode", SandboxMode.LOCAL).value,
                backend_used=getattr(sandbox, "mode", SandboxMode.LOCAL).value,
            )
        except Exception as e:
            end_t = time.time()
            duration_ms = (end_t - start_t) * 1000.0
            logger.error("Error executing task %s: %s", task.task_id, e)
            record = TaskExecutionRecord(
                task_id=task.task_id,
                started_at=start_t,
                finished_at=end_t,
                duration_ms=duration_ms,
                exit_code=1,
                error=str(e),
                stderr=f"Task execution failed: {e}",
            )
        finally:
            if ephemeral_sandbox and sandbox is not None:
                try:
                    self.sandbox_manager.destroy_sandbox(sandbox.sandbox_id)
                except Exception:
                    pass

        # 3. Record history in registry
        self.registry.record_execution(task.task_id, record)

        # 4. Advance schedule / update status
        if task.status != TaskStatus.CANCELLED:
            if task.max_runs is not None and task.run_count >= task.max_runs:
                task.status = TaskStatus.COMPLETED
                task.next_run_at = None
            else:
                next_t = self.registry.calculate_next_run(task, from_time=time.time())
                if next_t is not None:
                    task.next_run_at = next_t
                    task.status = TaskStatus.SCHEDULED
                else:
                    task.status = TaskStatus.COMPLETED
                    task.next_run_at = None

        return record
