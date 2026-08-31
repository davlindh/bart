"""Base abstract interface for Antigravity Sandboxes."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from .models import ExecutionResult, SandboxMode, SandboxState


class BaseSandbox(ABC):
    """Abstract Base Class defining the unified interface for all sandbox implementations."""

    @abstractmethod
    def start(self) -> None:
        """Initialize and start the sandbox environment."""
        pass

    @abstractmethod
    def execute(
        self,
        code: str,
        language: str = "python",
        timeout: float = 30.0,
        repl: bool = True,
    ) -> ExecutionResult:
        """
        Execute code within the sandbox environment.

        Args:
            code: The Python source code string to execute.
            language: Programming language (defaults to 'python').
            timeout: Maximum execution duration in seconds.
            repl: If True, execute statefully in REPL mode maintaining namespace.
                  If False, execute as an isolated script.

        Returns:
            ExecutionResult containing stdout, stderr, artifacts, exit code, duration, etc.
        """
        pass

    @abstractmethod
    def pause(self) -> None:
        """Pause the sandbox execution state."""
        pass

    @abstractmethod
    def resume(self) -> None:
        """Resume execution state for a paused sandbox."""
        pass

    @abstractmethod
    def create_snapshot(self, name: str) -> str:
        """
        Create a checkpoint/snapshot of current sandbox state.

        Args:
            name: Descriptive name for the snapshot.

        Returns:
            Unique snapshot ID string.
        """
        pass

    @abstractmethod
    def restore_snapshot(self, snapshot_id: str) -> None:
        """
        Restore sandbox namespace and memory state from a snapshot ID.

        Args:
            snapshot_id: Unique snapshot ID created earlier.
        """
        pass

    @abstractmethod
    def list_snapshots(self) -> List[Dict[str, Any]]:
        """
        List all snapshots captured in the sandbox.

        Returns:
            List of snapshot metadata dictionaries with snapshot_id, name, and timestamp.
        """
        pass

    @abstractmethod
    def delete_snapshot(self, snapshot_id: str) -> bool:
        """
        Delete a snapshot from the sandbox.

        Args:
            snapshot_id: Unique snapshot ID to delete.

        Returns:
            True if snapshot was found and deleted, False otherwise.
        """
        pass

    @abstractmethod
    def terminate(self) -> None:
        """Terminate sandbox process/microVM and free all allocated resources."""
        pass

    def destroy(self) -> None:
        """Alias for terminate()."""
        self.terminate()

    @abstractmethod
    def reset_session(self) -> None:
        """Reset the REPL session state back to initial clean environment."""
        pass

    @abstractmethod
    def get_variables(self) -> Dict[str, Any]:
        """Inspect and return current variables defined in the REPL session."""
        pass

    @property
    @abstractmethod
    def sandbox_id(self) -> str:
        """Return the unique identifier of the sandbox."""
        pass

    @property
    @abstractmethod
    def status(self) -> SandboxState:
        """Return the current lifecycle state of the sandbox."""
        pass

    @property
    @abstractmethod
    def mode(self) -> SandboxMode:
        """Return the sandbox backend mode (LOCAL or E2B)."""
        pass

    def __enter__(self) -> "BaseSandbox":
        self.start()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.terminate()
