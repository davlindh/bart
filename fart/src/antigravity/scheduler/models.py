"""
Data models, enums, and execution record definitions for the Scheduled Background Service Worker.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union


class TaskTriggerType(str, Enum):
    """Trigger mechanism types for scheduled background tasks."""
    CRON = "cron"
    TIMER = "timer"


class TaskStatus(str, Enum):
    """Lifecycle states of a scheduled task."""
    SCHEDULED = "scheduled"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"
    PENDING = "pending"


@dataclass
class TaskExecutionRecord:
    """Audit record capturing the outcome of a single task execution run."""
    task_id: str
    execution_id: str = field(default_factory=lambda: f"exec-{uuid.uuid4().hex[:10]}")
    started_at: float = field(default_factory=time.time)
    finished_at: Optional[float] = None
    duration_ms: float = 0.0
    exit_code: int = 0
    stdout: str = ""
    stderr: str = ""
    result: Optional[Any] = None
    results: List[Any] = field(default_factory=list)
    error: Optional[str] = None
    artifacts: List[Dict[str, Any]] = field(default_factory=list)
    state: Dict[str, Any] = field(default_factory=dict)
    sandbox_backend: str = "local"
    backend_used: str = "local"

    @property
    def is_success(self) -> bool:
        """Returns True if execution completed successfully without error and exit code 0."""
        return self.exit_code == 0 and self.error is None

    @property
    def success(self) -> bool:
        """Alias for is_success."""
        return self.is_success

    @property
    def duration_seconds(self) -> float:
        """Duration in seconds."""
        return self.duration_ms / 1000.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert execution record to dictionary."""
        return {
            "execution_id": self.execution_id,
            "task_id": self.task_id,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "duration_ms": self.duration_ms,
            "duration_seconds": self.duration_seconds,
            "exit_code": self.exit_code,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "result": self.result,
            "results": self.results,
            "error": self.error,
            "artifacts": self.artifacts,
            "state": self.state,
            "sandbox_backend": self.sandbox_backend,
            "backend_used": self.backend_used,
            "is_success": self.is_success,
        }


@dataclass
class ScheduledTask:
    """Definition and lifecycle state of a scheduled background task."""
    task_id: str
    name: str
    trigger_type: Union[TaskTriggerType, str]
    trigger_spec: str
    code: str
    sandbox_id: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    next_run_at: Optional[float] = None
    last_run_at: Optional[float] = None
    run_count: int = 0
    status: TaskStatus = TaskStatus.SCHEDULED
    max_runs: Optional[int] = None
    timeout: float = 60.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if isinstance(self.trigger_type, str):
            try:
                self.trigger_type = TaskTriggerType(self.trigger_type.lower())
            except ValueError:
                pass
        if isinstance(self.status, str):
            try:
                self.status = TaskStatus(self.status.lower())
            except ValueError:
                pass
        if not self.created_at:
            self.created_at = time.time()

    @property
    def code_payload(self) -> str:
        """Alias for code attribute."""
        return self.code

    @code_payload.setter
    def code_payload(self, val: str) -> None:
        self.code = val

    @property
    def timeout_seconds(self) -> float:
        """Alias for timeout attribute."""
        return self.timeout

    @timeout_seconds.setter
    def timeout_seconds(self, val: float) -> None:
        self.timeout = val

    def to_dict(self) -> Dict[str, Any]:
        """Convert scheduled task to dictionary."""
        return {
            "task_id": self.task_id,
            "name": self.name,
            "trigger_type": self.trigger_type.value if isinstance(self.trigger_type, TaskTriggerType) else str(self.trigger_type),
            "trigger_spec": self.trigger_spec,
            "code": self.code,
            "sandbox_id": self.sandbox_id,
            "created_at": self.created_at,
            "next_run_at": self.next_run_at,
            "last_run_at": self.last_run_at,
            "run_count": self.run_count,
            "status": self.status.value if isinstance(self.status, TaskStatus) else str(self.status),
            "max_runs": self.max_runs,
            "timeout": self.timeout,
            "metadata": self.metadata,
        }
