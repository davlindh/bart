"""Omnipod UI Controller — Manages view state, debouncing, and batch refreshes for the 9 Perspective Windows.

Migrated and adapted from 3.7fmossmorph/meta-framework/layered_runner/ui_controller.ts.
Provides:
  - Perspective Window component registration
  - Visibility tracking per window
  - Batched update pipeline with debounce and throttle controls
  - Integration with LocalStateManager for reactive UI synchronization
"""

import asyncio
import time
from typing import Any, Callable, Dict, List, Optional, Set
from pydantic import BaseModel, Field

from src.core.types import PerspectiveWindow
from src.graph.window_particles import WINDOW_DECOMPOSITIONS, WindowDecomposition
from src.platform.state_manager import LocalStateManager


class UIControllerConfig(BaseModel):
    """Configuration for UI update batching and rate limiting."""
    debounce_ms: int = Field(default=50, description="Debounce interval in milliseconds")
    throttle_ms: int = Field(default=100, description="Throttle interval in milliseconds")
    batch_updates: bool = Field(default=True)
    max_batch_size: int = Field(default=15)


class WindowViewUpdate(BaseModel):
    """Encapsulates a payload targeted at a specific Perspective Window component."""
    window: PerspectiveWindow
    component_id: str
    entity_id: Optional[str] = None
    data: Dict[str, Any] = Field(default_factory=dict)
    timestamp: float = Field(default_factory=time.time)


class OmnipodUIController:
    """Manages reactive UI updates, visibility states, and event routing for all 9 Omnipod windows."""

    def __init__(
        self,
        state_manager: Optional[LocalStateManager] = None,
        config: Optional[UIControllerConfig] = None,
    ):
        self.state_manager = state_manager or LocalStateManager()
        self.config = config or UIControllerConfig()
        # window -> component_id -> callback
        self._window_callbacks: Dict[PerspectiveWindow, Dict[str, Callable[[WindowViewUpdate], Any]]] = {
            w: {} for w in PerspectiveWindow
        }
        self._active_visible_windows: Set[PerspectiveWindow] = set(PerspectiveWindow)
        self._pending_updates: List[WindowViewUpdate] = []
        self._processed_history: List[WindowViewUpdate] = []
        self._error_log: List[Dict[str, Any]] = []

    # ── Window Registration ─────────────────────────────────────────────

    def register_window_component(
        self,
        window: PerspectiveWindow,
        component_id: str,
        callback: Callable[[WindowViewUpdate], Any],
    ) -> None:
        """Register a presentation callback for a specific window component."""
        if window not in self._window_callbacks:
            self._window_callbacks[window] = {}
        self._window_callbacks[window][component_id] = callback

    def unregister_window_component(
        self,
        window: PerspectiveWindow,
        component_id: str,
    ) -> None:
        """Unregister a presentation callback."""
        if window in self._window_callbacks and component_id in self._window_callbacks[window]:
            del self._window_callbacks[window][component_id]

    def set_window_visibility(self, window: PerspectiveWindow, is_visible: bool) -> None:
        """Toggle whether a window is currently visible/active in the user interface."""
        if is_visible:
            self._active_visible_windows.add(window)
        else:
            self._active_visible_windows.discard(window)

    def is_window_visible(self, window: PerspectiveWindow) -> bool:
        return window in self._active_visible_windows

    # ── Update Pipeline ─────────────────────────────────────────────────

    def queue_update(self, update: WindowViewUpdate) -> None:
        """Queue a window update. If batching is disabled, dispatches immediately."""
        if not self.config.batch_updates:
            self._dispatch_immediate(update)
            return

        self._pending_updates.append(update)
        if len(self._pending_updates) >= self.config.max_batch_size:
            self.flush_updates()

    def flush_updates(self) -> int:
        """Process all queued updates synchronously."""
        if not self._pending_updates:
            return 0

        batch = list(self._pending_updates)
        self._pending_updates.clear()

        processed_count = 0
        for update in batch:
            # Only dispatch if the window is currently visible
            if update.window in self._active_visible_windows:
                self._dispatch_immediate(update)
                processed_count += 1
            self._processed_history.append(update)

        return processed_count

    def _dispatch_immediate(self, update: WindowViewUpdate) -> None:
        """Deliver an update directly to registered component callbacks."""
        window_handlers = self._window_callbacks.get(update.window, {})
        # If component_id is specified and registered, trigger that handler
        if update.component_id in window_handlers:
            try:
                window_handlers[update.component_id](update)
            except Exception as e:
                self._error_log.append({
                    "window": update.window.value,
                    "component": update.component_id,
                    "error": str(e),
                    "timestamp": time.time(),
                })
        else:
            # Broadcast to all components in the window
            for comp_id, handler in window_handlers.items():
                try:
                    handler(update)
                except Exception as e:
                    self._error_log.append({
                        "window": update.window.value,
                        "component": comp_id,
                        "error": str(e),
                        "timestamp": time.time(),
                    })

    # ── Telemetry & Diagnostics ─────────────────────────────────────────

    @property
    def pending_count(self) -> int:
        return len(self._pending_updates)

    @property
    def history_count(self) -> int:
        return len(self._processed_history)

    @property
    def error_count(self) -> int:
        return len(self._error_log)

    def get_registered_component_count(self, window: Optional[PerspectiveWindow] = None) -> int:
        if window:
            return len(self._window_callbacks.get(window, {}))
        return sum(len(handlers) for handlers in self._window_callbacks.values())
