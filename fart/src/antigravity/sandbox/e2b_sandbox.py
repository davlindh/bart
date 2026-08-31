"""E2B Firecracker MicroVM Sandbox Implementation."""

from __future__ import annotations

import os
import time
import uuid
from typing import Any, Dict, List, Optional

from .base import BaseSandbox
from .models import (
    ExecutionResult,
    SandboxExecutionError,
    SandboxMode,
    SandboxState,
    SandboxTimeoutError,
    SnapshotError,
)


class E2BSandbox(BaseSandbox):
    """
    E2B Cloud Firecracker MicroVM Sandbox Driver.

    Interfaces with e2b-code-interpreter SDK to provision hardware-isolated
    microVMs in the cloud. Gracefully handles missing API keys or offline environments.
    """

    def __init__(
        self,
        sandbox_id: Optional[str] = None,
        api_key: Optional[str] = None,
        template: Optional[str] = None,
        timeout: float = 300.0,
        env: Optional[Dict[str, str]] = None,
        auto_start: bool = True,
        _driver_client: Optional[Any] = None,  # Hook for mock driver injection in tests
    ) -> None:
        self._sandbox_id = sandbox_id or f"sb_e2b_{uuid.uuid4().hex[:12]}"
        self._api_key = api_key or os.environ.get("E2B_API_KEY")
        self._template = template or "python-sandbox"
        self._timeout = timeout
        self._env = env or {}
        self._status = SandboxState.INITIALIZING
        self._created_at = time.time()
        self._client: Optional[Any] = _driver_client
        self._snapshots: Dict[str, Any] = {}

        if auto_start:
            self.start()

    @property
    def sandbox_id(self) -> str:
        return self._sandbox_id

    @property
    def status(self) -> SandboxState:
        return self._status

    @property
    def mode(self) -> SandboxMode:
        return SandboxMode.E2B

    def start(self) -> None:
        """Initialize E2B microVM instance."""
        if self._client is not None:
            # Custom / mocked client provided
            self._status = SandboxState.RUNNING
            return

        if not self._api_key:
            self._status = SandboxState.ERROR
            raise SandboxExecutionError(
                "E2B API key not found. Please set E2B_API_KEY environment variable "
                "or specify api_key in sandbox configuration."
            )

        try:
            # Attempt to import e2b SDK dynamically
            from e2b_code_interpreter import CodeInterpreter

            self._client = CodeInterpreter(
                api_key=self._api_key,
                template=self._template,
                timeout=int(self._timeout),
                envs=self._env,
            )
            self._status = SandboxState.RUNNING
        except ImportError:
            self._status = SandboxState.ERROR
            raise SandboxExecutionError(
                "Package 'e2b-code-interpreter' is not installed. "
                "Install with 'pip install e2b-code-interpreter' to use E2BSandbox."
            )
        except Exception as e:
            self._status = SandboxState.ERROR
            raise SandboxExecutionError(f"Failed to initialize E2B microVM: {e}") from e

    def execute(
        self,
        code: str,
        language: str = "python",
        timeout: float = 30.0,
        repl: bool = True,
    ) -> ExecutionResult:
        """Execute code inside the remote microVM."""
        if self._status == SandboxState.PAUSED:
            raise SandboxExecutionError("Cannot execute code in a paused microVM. Call resume() first.")
        if self._status == SandboxState.TERMINATED:
            raise SandboxExecutionError("Cannot execute code in a terminated microVM.")
        if self._client is None:
            raise SandboxExecutionError("E2B microVM is not running.")

        start_time = time.perf_counter()
        try:
            # Check if client is a mock or real CodeInterpreter
            if hasattr(self._client, "notebook") and hasattr(self._client.notebook, "exec_cell"):
                res = self._client.notebook.exec_cell(code)
            elif hasattr(self._client, "run_code"):
                res = self._client.run_code(code)
            elif hasattr(self._client, "execute"):
                res = self._client.execute(code)
            else:
                raise SandboxExecutionError("Unsupported E2B client interface.")

            duration_ms = (time.perf_counter() - start_time) * 1000.0

            # Extract outputs and artifacts
            stdout_parts: List[str] = []
            stderr_parts: List[str] = []
            artifacts: List[Dict[str, Any]] = []
            error_str: Optional[str] = None
            exit_code = 0

            # Parse stdout/stderr/results
            if hasattr(res, "logs"):
                if hasattr(res.logs, "stdout"):
                    stdout_parts.extend(res.logs.stdout)
                if hasattr(res.logs, "stderr"):
                    stderr_parts.extend(res.logs.stderr)

            if hasattr(res, "stdout") and isinstance(res.stdout, (str, list)):
                if isinstance(res.stdout, list):
                    stdout_parts.extend(res.stdout)
                else:
                    stdout_parts.append(res.stdout)

            if hasattr(res, "stderr") and isinstance(res.stderr, (str, list)):
                if isinstance(res.stderr, list):
                    stderr_parts.extend(res.stderr)
                else:
                    stderr_parts.append(res.stderr)

            if hasattr(res, "error") and res.error:
                exit_code = 1
                error_str = str(res.error)
                stderr_parts.append(error_str)

            # MIME results / artifacts
            if hasattr(res, "results") and res.results:
                for item in res.results:
                    if hasattr(item, "png") and item.png:
                        artifacts.append({
                            "type": "image/png",
                            "data": item.png,
                            "name": "chart.png"
                        })
                    elif hasattr(item, "svg") and item.svg:
                        artifacts.append({
                            "type": "image/svg+xml",
                            "data": item.svg,
                            "name": "chart.svg"
                        })
                    elif hasattr(item, "text") and item.text:
                        stdout_parts.append(str(item.text))

            stdout_text = "".join(stdout_parts)
            stderr_text = "".join(stderr_parts)

            return ExecutionResult(
                stdout=stdout_text,
                stderr=stderr_text,
                exit_code=exit_code,
                artifacts=artifacts,
                duration_ms=duration_ms,
                error=error_str,
                state={},
                backend_used="e2b",
            )

        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            return ExecutionResult(
                stdout="",
                stderr=str(e),
                exit_code=1,
                error=f"E2BExecutionError: {e}",
                duration_ms=duration_ms,
                backend_used="e2b",
            )

    def pause(self) -> None:
        """Pause microVM execution."""
        if self._status == SandboxState.TERMINATED:
            raise SandboxExecutionError("Cannot pause a terminated microVM.")
        if hasattr(self._client, "pause"):
            try:
                self._client.pause()
            except Exception as e:
                raise SandboxExecutionError(f"Failed to pause E2B microVM: {e}") from e
        self._status = SandboxState.PAUSED

    def resume(self) -> None:
        """Resume paused microVM execution."""
        if self._status == SandboxState.TERMINATED:
            raise SandboxExecutionError("Cannot resume a terminated microVM.")
        if hasattr(self._client, "resume"):
            try:
                self._client.resume()
            except Exception as e:
                raise SandboxExecutionError(f"Failed to resume E2B microVM: {e}") from e
        self._status = SandboxState.RUNNING

    def create_snapshot(self, name: str) -> str:
        """Create a snapshot of the microVM."""
        if self._status == SandboxState.TERMINATED:
            raise SnapshotError("Cannot snapshot a terminated microVM.")
        snapshot_id = f"snap_e2b_{uuid.uuid4().hex[:12]}"
        if hasattr(self._client, "create_snapshot"):
            try:
                remote_id = self._client.create_snapshot(name)
                snapshot_id = remote_id or snapshot_id
            except Exception as e:
                raise SnapshotError(f"E2B snapshot failed: {e}") from e
        self._snapshots[snapshot_id] = {"name": name, "timestamp": time.time()}
        return snapshot_id

    def restore_snapshot(self, snapshot_id: str) -> None:
        """Restore microVM to a previous snapshot."""
        if self._status == SandboxState.TERMINATED:
            raise SnapshotError("Cannot restore a terminated microVM.")
        if snapshot_id not in self._snapshots and not (
            hasattr(self._client, "restore_snapshot")
        ):
            raise SnapshotError(f"Snapshot '{snapshot_id}' not found.")
        if hasattr(self._client, "restore_snapshot"):
            try:
                self._client.restore_snapshot(snapshot_id)
            except Exception as e:
                raise SnapshotError(f"E2B snapshot restore failed: {e}") from e

    def list_snapshots(self) -> List[Dict[str, Any]]:
        """List all snapshots captured in the microVM."""
        result = []
        for sid, meta in self._snapshots.items():
            result.append({
                "snapshot_id": sid,
                "name": meta.get("name", ""),
                "timestamp": meta.get("timestamp", 0.0),
            })
        return result

    def delete_snapshot(self, snapshot_id: str) -> bool:
        """Delete a snapshot by ID."""
        if snapshot_id in self._snapshots:
            del self._snapshots[snapshot_id]
            return True
        return False

    def reset_session(self) -> None:
        """Reset microVM REPL state."""
        if hasattr(self._client, "reset"):
            self._client.reset()
        elif hasattr(self._client, "notebook") and hasattr(self._client.notebook, "restart"):
            self._client.notebook.restart()

    def get_variables(self) -> Dict[str, Any]:
        """Inspect variables in the microVM session."""
        if hasattr(self._client, "get_variables"):
            return self._client.get_variables()
        return {}

    def terminate(self) -> None:
        """Terminate the microVM instance."""
        if self._status == SandboxState.TERMINATED:
            return
        if self._client is not None:
            try:
                if hasattr(self._client, "kill"):
                    self._client.kill()
                elif hasattr(self._client, "close"):
                    self._client.close()
            except Exception:
                pass
            finally:
                self._client = None
        self._status = SandboxState.TERMINATED
