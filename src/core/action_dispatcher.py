"""Dual-Path Action Dispatcher — Priority-based routing for agent actions.

Migrated from 3.7fmossmorph/meta-framework/layered_runner/dual_path_processor.ts.
Routes agent actions through either an immediate execution path or a sequential
background queue based on priority, trust-impact, and visibility criteria.
"""

import asyncio
import time
import uuid
from enum import IntEnum
from typing import Any, Callable, Coroutine, Dict, List, Optional

from pydantic import BaseModel, Field


class ActionPriority(IntEnum):
    """Priority levels for dispatched actions."""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


class DispatchableAction(BaseModel):
    """A unit of work to be dispatched through the dual-path system."""
    action_id: str = Field(default_factory=lambda: f"act_{uuid.uuid4().hex[:12]}")
    source_agent: str = Field(..., description="Name of the originating agent")
    action_type: str = Field(..., description="Semantic action type tag (e.g. ROLE_REDESIGN, WEBHOOK_SETUP)")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Action-specific data")
    priority: ActionPriority = Field(default=ActionPriority.NORMAL)
    affects_visibility: bool = Field(default=False, description="Does this change what the user sees?")
    user_initiated: bool = Field(default=False)
    affects_trust: bool = Field(default=False, description="Does this modify trust-critical state?")
    timestamp: float = Field(default_factory=time.time)


class QueuedAction(BaseModel):
    """Action sitting in the background processing queue."""
    action: DispatchableAction
    retry_count: int = 0
    max_retries: int = 3
    queued_at: float = Field(default_factory=time.time)


class DispatchResult(BaseModel):
    """Outcome of dispatching an action."""
    action_id: str
    path: str = Field(description="'immediate' or 'sequential'")
    success: bool = True
    error: Optional[str] = None
    queued_for_sync: bool = False


class ActionDispatcher:
    """Dual-path action dispatcher with priority routing and background queue.

    Path 1 — Immediate: High-priority, user-initiated, visibility-affecting,
    or trust-impacting actions are executed synchronously and then queued for
    background persistence/sync.

    Path 2 — Sequential: Lower-priority actions are queued and batch-processed
    at a configurable interval.
    """

    def __init__(
        self,
        on_execute: Optional[Callable[[DispatchableAction], Coroutine[Any, Any, bool]]] = None,
        on_persist: Optional[Callable[[DispatchableAction], Coroutine[Any, Any, bool]]] = None,
        queue_interval_seconds: float = 1.0,
    ):
        self._queue: Dict[str, QueuedAction] = {}
        self._executed_log: List[DispatchResult] = []
        self._on_execute = on_execute
        self._on_persist = on_persist
        self._queue_interval = queue_interval_seconds
        self._processing = False
        self._task: Optional[asyncio.Task] = None

    # ── Public API ──────────────────────────────────────────────────────

    async def dispatch(self, action: DispatchableAction) -> DispatchResult:
        """Route an action through the appropriate path."""
        if self._requires_immediate(action):
            return await self._execute_immediate(action)
        else:
            return self._enqueue_sequential(action)

    def start_background_processing(self, loop: Optional[asyncio.AbstractEventLoop] = None):
        """Start the periodic background queue processor."""
        if self._task is None:
            _loop = loop or asyncio.get_event_loop()
            self._task = _loop.create_task(self._process_loop())

    def stop_background_processing(self):
        """Cancel the background queue processor."""
        if self._task:
            self._task.cancel()
            self._task = None

    @property
    def queue_size(self) -> int:
        return len(self._queue)

    @property
    def execution_log(self) -> List[DispatchResult]:
        return list(self._executed_log)

    # ── Path Decision ───────────────────────────────────────────────────

    def _requires_immediate(self, action: DispatchableAction) -> bool:
        """Determine if an action should take the immediate execution path."""
        if action.priority >= ActionPriority.HIGH:
            return True
        if action.user_initiated:
            return True
        if action.affects_visibility:
            return True
        if action.affects_trust:
            return True
        return False

    # ── Path 1: Immediate ───────────────────────────────────────────────

    async def _execute_immediate(self, action: DispatchableAction) -> DispatchResult:
        """Execute action synchronously, then queue for background persistence."""
        result = DispatchResult(action_id=action.action_id, path="immediate")
        try:
            if self._on_execute:
                success = await self._on_execute(action)
                result.success = success
            # Queue background persistence sync
            self._queue[action.action_id] = QueuedAction(action=action)
            result.queued_for_sync = True
        except Exception as e:
            result.success = False
            result.error = str(e)
        self._executed_log.append(result)
        return result

    # ── Path 2: Sequential ──────────────────────────────────────────────

    def _enqueue_sequential(self, action: DispatchableAction) -> DispatchResult:
        """Queue an action for later batch processing."""
        self._queue[action.action_id] = QueuedAction(action=action)
        result = DispatchResult(
            action_id=action.action_id,
            path="sequential",
            queued_for_sync=True,
        )
        self._executed_log.append(result)
        return result

    # ── Background Queue Processor ──────────────────────────────────────

    async def _process_loop(self):
        """Periodically process the background queue."""
        while True:
            await asyncio.sleep(self._queue_interval)
            await self.process_queue()

    async def process_queue(self):
        """Process the highest-priority queued action."""
        if self._processing or not self._queue:
            return
        self._processing = True
        try:
            # Sort by priority (descending), then by queue time (oldest first)
            sorted_items = sorted(
                self._queue.values(),
                key=lambda q: (-q.action.priority, q.queued_at),
            )
            item = sorted_items[0]
            del self._queue[item.action.action_id]

            try:
                if self._on_persist:
                    await self._on_persist(item.action)
            except Exception:
                # Re-queue with backoff if under retry limit
                if item.retry_count < item.max_retries:
                    item.retry_count += 1
                    item.queued_at = time.time()
                    self._queue[item.action.action_id] = item
        finally:
            self._processing = False

    async def force_flush(self):
        """Process all queued actions immediately."""
        while self._queue:
            await self.process_queue()
