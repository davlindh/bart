"""Real-time Stream Bridge — Async event streaming for WebSocket/SSE UI clients.

Bridges agent lifecycle events, context resolution updates, and dual-path action
dispatches into a real-time event stream suitable for SSE / WebSocket client consumption.
"""

import asyncio
import json
import time
import uuid
from enum import Enum
from typing import Any, AsyncGenerator, Dict, List, Optional, Set
from pydantic import BaseModel, Field


class EventType(str, Enum):
    """Event types broadcasted across the real-time stream."""
    CYCLE_STARTED = "cycle_started"
    AGENT_PROGRESS = "agent_progress"
    CONTEXT_RESOLVED = "context_resolved"
    ACTION_DISPATCHED = "action_dispatched"
    STATE_MUTATED = "state_mutated"
    PROPOSAL_STATUS_CHANGED = "proposal_status_changed"
    CYCLE_COMPLETED = "cycle_completed"
    ERROR_ALERT = "error_alert"


class StreamFrame(BaseModel):
    """Standardized SSE / WebSocket wire frame."""
    frame_id: str = Field(default_factory=lambda: f"frame_{uuid.uuid4().hex[:8]}")
    event_type: EventType
    timestamp: float = Field(default_factory=time.time)
    payload: Dict[str, Any] = Field(default_factory=dict)

    def to_sse_message(self) -> str:
        """Formats the frame as an SSE event stream data chunk."""
        return f"event: {self.event_type.value}\ndata: {json.dumps(self.payload)}\nid: {self.frame_id}\n\n"

    def to_ws_message(self) -> str:
        """Formats the frame as a JSON-RPC / WebSocket payload string."""
        return self.model_dump_json()


class StreamBridge:
    """Pub/sub event bus with async generators for client streaming connections."""

    def __init__(self, max_buffer_size: int = 200):
        self.max_buffer_size = max_buffer_size
        self._subscribers: Set[asyncio.Queue] = set()
        self._history: List[StreamFrame] = []

    # ── Producer API ────────────────────────────────────────────────────

    async def broadcast(self, event_type: EventType, payload: Dict[str, Any]) -> StreamFrame:
        """Broadcast an event frame to all connected streaming clients."""
        frame = StreamFrame(event_type=event_type, payload=payload)

        # Buffer history
        self._history.append(frame)
        if len(self._history) > self.max_buffer_size:
            self._history.pop(0)

        # Dispatch to all active client queues
        for queue in list(self._subscribers):
            try:
                queue.put_nowait(frame)
            except asyncio.QueueFull:
                pass  # Avoid blocking fast publisher if client is slow

        return frame

    # ── Consumer API (SSE / WebSocket Generators) ───────────────────────

    async def client_stream(self, replay_history: bool = True) -> AsyncGenerator[StreamFrame, None]:
        """Async generator providing a live stream of frames for a connected client."""
        queue: asyncio.Queue = asyncio.Queue(maxsize=100)
        self._subscribers.add(queue)

        try:
            # Replay historical frames if requested
            if replay_history:
                for frame in self._history:
                    yield frame

            while True:
                frame = await queue.get()
                yield frame
        finally:
            self._subscribers.discard(queue)

    @property
    def active_connections(self) -> int:
        return len(self._subscribers)

    @property
    def history_length(self) -> int:
        return len(self._history)
