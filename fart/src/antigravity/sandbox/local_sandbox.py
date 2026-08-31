"""Local Python Subprocess Sandbox with AST security validation and stateful REPL."""

from __future__ import annotations

import base64
import concurrent.futures
import json
import logging
import os
import pickle
import subprocess
import sys
import threading
import time
import uuid
from typing import Any, Dict, List, Optional

from .ast_security import ASTSecurityValidator
from .base import BaseSandbox
from .models import (
    ExecutionResult,
    SandboxConfig,
    SandboxExecutionError,
    SandboxMode,
    SandboxState,
    SandboxTimeoutError,
    SecurityViolationError,
    SnapshotError,
)


class LocalSandbox(BaseSandbox):
    """
    Secure Local Sandbox implementation.

    Executes Python code inside an isolated subprocess via stdio JSON-RPC,
    enforces AST security validation, runtime builtins sanitization,
    cross-platform timeouts, persistent REPL session state, and state snapshotting.
    """

    def __init__(
        self,
        sandbox_id: Optional[str] = None,
        timeout: float = 300.0,
        env: Optional[Dict[str, str]] = None,
        authorized_imports: Optional[List[str]] = None,
        work_dir: Optional[str] = None,
        max_output_bytes: int = 2 * 1024 * 1024,
        auto_start: bool = True,
    ) -> None:
        self._sandbox_id = sandbox_id or f"sb_loc_{uuid.uuid4().hex[:12]}"
        self._timeout = timeout
        self._env = env or {}
        self._authorized_imports = authorized_imports or []
        self._work_dir = work_dir
        self._max_output_bytes = max_output_bytes
        self._status = SandboxState.INITIALIZING
        self._process: Optional[subprocess.Popen] = None
        self._snapshots: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()
        self._created_at = time.time()
        self._validator = ASTSecurityValidator(
            additional_allowed_modules=self._authorized_imports
        )

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
        return SandboxMode.LOCAL

    @property
    def work_dir(self) -> Optional[str]:
        return self._work_dir

    def _get_worker_script_path(self) -> str:
        """Locate the standalone worker script."""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(current_dir, "local_repl_worker.py")

    def _spawn_worker(self) -> None:
        """Spawn the background REPL worker subprocess."""
        worker_path = self._get_worker_script_path()
        worker_env = os.environ.copy()
        worker_env.update(self._env)
        worker_env["MAX_OUTPUT_BYTES"] = str(self._max_output_bytes)
        worker_env["PYTHONIOENCODING"] = "utf-8"
        worker_env["PYTHONUTF8"] = "1"
        # Ensure pythonpath includes src
        root_src = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..")
        )
        if "PYTHONPATH" in worker_env:
            worker_env["PYTHONPATH"] = f"{root_src}{os.pathsep}{worker_env['PYTHONPATH']}"
        else:
            worker_env["PYTHONPATH"] = root_src

        try:
            self._process = subprocess.Popen(
                [sys.executable, "-u", worker_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
                cwd=self._work_dir,
                env=worker_env,
            )
            self._status = SandboxState.RUNNING
        except Exception as e:
            self._status = SandboxState.ERROR
            raise SandboxExecutionError(f"Failed to spawn local worker subprocess: {e}") from e

    def _kill_worker(self) -> None:
        """Forcefully kill the worker process if running."""
        if self._process is not None:
            try:
                self._process.terminate()
                self._process.wait(timeout=0.5)
            except Exception:
                try:
                    self._process.kill()
                    self._process.wait(timeout=0.5)
                except Exception:
                    pass
            finally:
                self._process = None

    def _send_command(
        self, cmd: Dict[str, Any], timeout: float = 30.0
    ) -> Dict[str, Any]:
        """Send JSON-RPC command to worker subprocess and wait for response with timeout."""
        with self._lock:
            if self._process is None or self._process.poll() is not None:
                self._spawn_worker()

            req_id = cmd.get("id", uuid.uuid4().hex[:8])
            cmd["id"] = req_id
            payload = json.dumps(cmd) + "\n"

            try:
                assert self._process.stdin is not None
                self._process.stdin.write(payload)
                self._process.stdin.flush()
            except (BrokenPipeError, OSError) as e:
                self._kill_worker()
                self._status = SandboxState.ERROR
                raise SandboxExecutionError(
                    f"Communication pipe broken with worker: {e}"
                ) from e

            # Read response using ThreadPoolExecutor with timeout
            def _readline() -> str:
                assert self._process is not None and self._process.stdout is not None
                return self._process.stdout.readline()

            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(_readline)
                try:
                    line = future.result(timeout=timeout)
                except concurrent.futures.TimeoutError:
                    self._kill_worker()
                    self._status = SandboxState.ERROR
                    raise SandboxTimeoutError(
                        f"Execution timed out after {timeout} seconds"
                    )

            if not line:
                exit_code = self._process.poll() if self._process else "unknown"
                self._kill_worker()
                self._status = SandboxState.ERROR
                raise SandboxExecutionError(
                    f"Worker process terminated unexpectedly (exit code: {exit_code})"
                )

            try:
                return json.loads(line)
            except json.JSONDecodeError as e:
                raise SandboxExecutionError(
                    f"Malformed JSON received from worker: {line}"
                ) from e

    def start(self) -> None:
        """Start the sandbox environment."""
        with self._lock:
            if self._status == SandboxState.RUNNING and self._process is not None:
                return
            self._spawn_worker()
            self._status = SandboxState.RUNNING

    def execute(
        self,
        code: str,
        language: str = "python",
        timeout: float = 30.0,
        repl: bool = True,
    ) -> ExecutionResult:
        """
        Execute code within the sandbox after AST security validation.
        """
        if self._status == SandboxState.PAUSED:
            raise SandboxExecutionError("Cannot execute code in a paused sandbox. Call resume() first.")
        if self._status == SandboxState.TERMINATED:
            raise SandboxExecutionError("Cannot execute code in a terminated sandbox.")

        if language.lower() != "python":
            return ExecutionResult(
                exit_code=1,
                stderr=f"Unsupported language '{language}'. Local sandbox supports 'python'.",
                error=f"UnsupportedLanguageError: {language}",
                backend_used="local",
            )

        # 1. AST Security Validation
        try:
            self._validator.validate(code)
        except SecurityViolationError as e:
            return ExecutionResult(
                exit_code=1,
                stderr=str(e),
                error=f"SecurityViolationError: {e}",
                duration_ms=0.0,
                backend_used="local",
            )
        except SyntaxError as e:
            return ExecutionResult(
                exit_code=1,
                stderr=f"SyntaxError: {e}",
                error=f"SyntaxError: {e}",
                duration_ms=0.0,
                backend_used="local",
            )

        # 2. Dispatch to Subprocess
        try:
            resp = self._send_command(
                {"action": "execute", "code": code, "repl": repl},
                timeout=timeout,
            )
            res_val = resp.get("result")
            results_list = [res_val] if res_val is not None else []
            out_str = resp.get("stdout", "")
            err_str = resp.get("stderr", "")
            if len(out_str.encode("utf-8")) > self._max_output_bytes:
                out_str = out_str[: self._max_output_bytes // 2] + "\n... [stdout truncated due to size limit]\n"
            if len(err_str.encode("utf-8")) > self._max_output_bytes:
                err_str = err_str[: self._max_output_bytes // 2] + "\n... [stderr truncated due to size limit]\n"

            return ExecutionResult(
                stdout=out_str,
                stderr=err_str,
                exit_code=resp.get("exit_code", 0),
                artifacts=resp.get("artifacts", []),
                duration_ms=resp.get("duration_ms", 0.0),
                error=resp.get("error"),
                state=resp.get("state", {}),
                backend_used="local",
                result=res_val,
                results=results_list,
            )
        except SandboxTimeoutError as e:
            return ExecutionResult(
                exit_code=1,
                stderr=str(e),
                error=f"SandboxTimeoutError: {e}",
                duration_ms=timeout * 1000.0,
                backend_used="local",
            )
        except SandboxExecutionError as e:
            return ExecutionResult(
                exit_code=1,
                stderr=str(e),
                error=f"SandboxExecutionError: {e}",
                duration_ms=0.0,
                backend_used="local",
            )

    def pause(self) -> None:
        """Pause execution in sandbox."""
        with self._lock:
            if self._status == SandboxState.TERMINATED:
                raise SandboxExecutionError("Cannot pause a terminated sandbox.")
            self._status = SandboxState.PAUSED

    def resume(self) -> None:
        """Resume execution in sandbox."""
        with self._lock:
            if self._status == SandboxState.TERMINATED:
                raise SandboxExecutionError("Cannot resume a terminated sandbox.")
            self._status = SandboxState.RUNNING

    def create_snapshot(self, name: str) -> str:
        """Take a snapshot of current session variables."""
        with self._lock:
            if self._status == SandboxState.TERMINATED:
                raise SnapshotError("Cannot create snapshot of a terminated sandbox.")
            try:
                resp = self._send_command({"action": "snapshot", "name": name}, timeout=10.0)
                if resp.get("status") == "ok":
                    snap_id = resp["snapshot_id"]
                    self._snapshots[snap_id] = {
                        "snapshot_id": snap_id,
                        "name": name,
                        "timestamp": time.time(),
                    }
                    return snap_id
                raise SnapshotError(resp.get("error", "Snapshot creation failed"))
            except Exception as e:
                raise SnapshotError(f"Snapshot creation error: {e}") from e

    def restore_snapshot(self, snapshot_id: str) -> None:
        """Restore sandbox state from snapshot ID."""
        with self._lock:
            if self._status == SandboxState.TERMINATED:
                raise SnapshotError("Cannot restore snapshot in a terminated sandbox.")
            try:
                resp = self._send_command(
                    {"action": "restore", "snapshot_id": snapshot_id}, timeout=10.0
                )
                if resp.get("status") != "ok":
                    raise SnapshotError(resp.get("error", f"Snapshot '{snapshot_id}' restore failed"))
            except Exception as e:
                raise SnapshotError(f"Snapshot restore error: {e}") from e

    def list_snapshots(self) -> List[Dict[str, Any]]:
        """List all snapshots captured in the sandbox."""
        with self._lock:
            if self._status == SandboxState.TERMINATED:
                return []
            try:
                resp = self._send_command({"action": "list_snapshots"}, timeout=5.0)
                if resp.get("status") == "ok" and "snapshots" in resp:
                    # Update local tracking cache
                    for s in resp["snapshots"]:
                        self._snapshots[s["snapshot_id"]] = s
                    return resp["snapshots"]
            except Exception:
                pass
            return list(self._snapshots.values())

    def delete_snapshot(self, snapshot_id: str) -> bool:
        """Delete a snapshot by ID."""
        with self._lock:
            if self._status == SandboxState.TERMINATED:
                return False
            self._snapshots.pop(snapshot_id, None)
            try:
                resp = self._send_command(
                    {"action": "delete_snapshot", "snapshot_id": snapshot_id}, timeout=5.0
                )
                return bool(resp.get("status") == "ok" and resp.get("deleted", True))
            except Exception:
                return True

    def reset_session(self) -> None:
        """Clear user variables in the REPL session."""
        with self._lock:
            if self._status == SandboxState.TERMINATED:
                raise SandboxExecutionError("Cannot reset session of a terminated sandbox.")
            try:
                self._send_command({"action": "reset"}, timeout=10.0)
            except Exception as e:
                raise SandboxExecutionError(f"Session reset error: {e}") from e

    def get_variables(self) -> Dict[str, Any]:
        """Return variable summary from REPL session."""
        with self._lock:
            if self._status == SandboxState.TERMINATED:
                return {}
            try:
                resp = self._send_command({"action": "get_variables"}, timeout=10.0)
                return resp.get("variables", {})
            except Exception:
                return {}

    def export_state(self, timeout: float = 10.0) -> Dict[str, Any]:
        """Export user-defined session variables from REPL subprocess."""
        with self._lock:
            if self._status == SandboxState.TERMINATED:
                return {}
            try:
                resp = self._send_command({"action": "export_state"}, timeout=timeout)
                if resp.get("status") == "ok" and "state_b64" in resp:
                    raw_bytes = base64.b64decode(resp["state_b64"].encode("ascii"))
                    return pickle.loads(raw_bytes)
                elif resp.get("status") == "ok" and "variables" in resp:
                    return resp["variables"]
                return {}
            except Exception as e:
                return {}

    def hydrate_state(self, state: Dict[str, Any], timeout: float = 10.0) -> bool:
        """Inject user variables into the REPL subprocess session globals."""
        with self._lock:
            if self._status == SandboxState.TERMINATED:
                raise SandboxExecutionError("Cannot hydrate a terminated sandbox.")
            try:
                try:
                    pkl_bytes = pickle.dumps(state, protocol=pickle.HIGHEST_PROTOCOL)
                    b64_str = base64.b64encode(pkl_bytes).decode("ascii")
                    cmd = {"action": "hydrate_state", "state_b64": b64_str}
                except Exception:
                    cmd = {"action": "hydrate_state", "variables": state}

                resp = self._send_command(cmd, timeout=timeout)
                if resp.get("status") != "ok":
                    raise SandboxExecutionError(resp.get("error", "Hydration failed"))
                return True
            except Exception as e:
                raise SandboxExecutionError(f"Failed to hydrate sandbox state: {e}") from e

    def persist_to_disk(self, storage_path: Optional[str] = None, name: Optional[str] = None) -> str:
        """Persist sandbox state, variables, and snapshots to SQLite disk store."""
        from antigravity.storage.disk_store import PersistenceManager
        store = PersistenceManager.get_instance(db_path=storage_path).store
        
        state_dict = self.export_state()
        metadata = {
            "name": name or self._sandbox_id,
            "work_dir": self._work_dir,
            "authorized_imports": self._authorized_imports,
            "timeout": self._timeout,
        }
        store.save_sandbox(
            sandbox_id=self._sandbox_id,
            mode=self.mode.value,
            status=self._status.value,
            state_dict=state_dict,
            metadata=metadata,
            created_at=self._created_at,
        )
        
        # Save snapshots to disk
        snapshots = self.list_snapshots()
        for snap in snapshots:
            snap_id = snap.get("snapshot_id")
            if snap_id:
                try:
                    snap_data = self._send_command({"action": "export_snapshot", "snapshot_id": snap_id}, timeout=5.0)
                    if snap_data.get("status") == "ok":
                        store.save_snapshot(
                            snapshot_id=snap_id,
                            sandbox_id=self._sandbox_id,
                            name=snap.get("name", "checkpoint"),
                            state_dict=snap_data.get("state", {}),
                            timestamp=snap.get("timestamp"),
                        )
                except Exception:
                    pass

        return self._sandbox_id

    def restore_from_disk(self, sandbox_id: Optional[str] = None, storage_path: Optional[str] = None) -> bool:
        """Restore sandbox state and snapshots from SQLite disk store."""
        from antigravity.storage.disk_store import PersistenceManager
        target_id = sandbox_id or self._sandbox_id
        store = PersistenceManager.get_instance(db_path=storage_path).store
        
        record = store.load_sandbox(target_id)
        if not record:
            return False
        
        state_dict = record.get("state", {})
        if state_dict:
            self.hydrate_state(state_dict)
            
        snapshots = store.list_snapshots(sandbox_id=target_id)
        for snap in snapshots:
            full_snap = store.load_snapshot(snap["snapshot_id"])
            if full_snap:
                try:
                    self._send_command({
                        "action": "import_snapshot",
                        "snapshot_id": full_snap["snapshot_id"],
                        "name": full_snap["name"],
                        "timestamp": full_snap["timestamp"],
                        "state": full_snap["state"],
                    }, timeout=5.0)
                except Exception:
                    pass

        return True

    def terminate(self) -> None:
        """Terminate worker process and mark sandbox as terminated."""
        with self._lock:
            if self._status == SandboxState.TERMINATED:
                return
            try:
                if self._process is not None and self._process.poll() is None:
                    try:
                        self._send_command({"action": "exit"}, timeout=2.0)
                    except Exception:
                        pass
            finally:
                self._kill_worker()
                self._status = SandboxState.TERMINATED
