"""Data models, enums, and exception classes for Antigravity Sandbox Engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class SandboxState(str, Enum):
    """Lifecycle states of a sandbox."""
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    TERMINATED = "terminated"
    ERROR = "error"


class SandboxMode(str, Enum):
    """Sandbox runtime backend mode."""
    E2B = "e2b"
    LOCAL = "local"
    AUTO = "auto"


@dataclass
class ExecutionResult:
    """Encapsulates the output and status of code execution inside a sandbox."""
    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0
    artifacts: List[Dict[str, Any]] = field(default_factory=list)
    duration_ms: float = 0.0
    error: Optional[str] = None
    state: Dict[str, Any] = field(default_factory=dict)
    backend_used: str = "local"
    result: Optional[Any] = None
    results: List[Any] = field(default_factory=list)

    @property
    def is_success(self) -> bool:
        """Returns True if execution completed without error and exit code 0."""
        return self.exit_code == 0 and self.error is None

    @property
    def success(self) -> bool:
        """Alias for is_success."""
        return self.is_success

    @property
    def duration_seconds(self) -> float:
        """Execution duration in seconds."""
        return self.duration_ms / 1000.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert execution result to a dictionary."""
        return {
            "stdout": self.stdout,
            "stderr": self.stderr,
            "exit_code": self.exit_code,
            "artifacts": self.artifacts,
            "duration_ms": self.duration_ms,
            "error": self.error,
            "state": self.state,
            "backend_used": self.backend_used,
            "result": self.result,
            "results": self.results,
            "success": self.is_success,
        }


@dataclass
class SandboxConfig:
    """Configuration parameters for sandbox initialization."""
    mode: SandboxMode = SandboxMode.AUTO
    timeout: float = 300.0
    env: Optional[Dict[str, str]] = None
    authorized_imports: Optional[List[str]] = None
    max_output_bytes: int = 2 * 1024 * 1024  # 2MB default stream limit
    e2b_api_key: Optional[str] = None
    e2b_template: Optional[str] = None


class SandboxError(Exception):
    """Base exception for all sandbox subsystem errors."""
    pass


class SecurityViolationError(SandboxError):
    """Raised when code violates AST or runtime security policies."""
    pass


class SandboxTimeoutError(SandboxError):
    """Raised when execution or lifecycle operation times out."""
    pass


class SandboxExecutionError(SandboxError):
    """Raised when an execution fails or sandbox process crashes."""
    pass


class SnapshotError(SandboxError):
    """Raised when snapshot creation or restoration fails."""
    pass
