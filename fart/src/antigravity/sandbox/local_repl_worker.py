"""Standalone JSON-RPC stdio REPL worker for LocalSandbox subprocess isolation."""

from __future__ import annotations

import ast
import base64
import copy
import io
import json
import pickle
import sys
import time
import traceback
import uuid
from typing import Any, Dict, List, Optional

# Ensure package root is in sys.path when invoked directly as a script
try:
    from antigravity.sandbox.builtins_sanitizer import get_sanitized_builtins
    from antigravity.sandbox.models import SecurityViolationError
except ImportError:
    # If invoked directly by path, locate and add root
    import os
    parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    from antigravity.sandbox.builtins_sanitizer import get_sanitized_builtins
    from antigravity.sandbox.models import SecurityViolationError


# Ensure UTF-8 standard streams on all platforms
if hasattr(sys.stdin, "reconfigure"):
    try:
        sys.stdin.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


class LocalREPLWorker:
    """
    Subprocess execution worker maintaining a persistent namespace across execution turns.
    Communicates with parent process via JSON lines over standard streams.
    """

    def __init__(self, max_output_bytes: int = 2 * 1024 * 1024) -> None:
        self.max_output_bytes = max_output_bytes
        self.snapshots: Dict[str, Dict[str, Any]] = {}
        self.session_globals: Dict[str, Any] = {}
        self._init_session()

    def _init_session(self) -> None:
        """Initialize or reset session globals to sanitized defaults."""
        def _save_artifact(name: str, data: Any, mime_type: str = "text/plain") -> None:
            """Helper function exposed inside sandbox for user scripts to emit artifacts."""
            if not isinstance(self.session_globals.get("__artifacts__"), list):
                self.session_globals["__artifacts__"] = []
            
            if isinstance(data, bytes):
                b64_data = base64.b64encode(data).decode("ascii")
            elif isinstance(data, str):
                b64_data = base64.b64encode(data.encode("utf-8")).decode("ascii")
            else:
                b64_data = base64.b64encode(json.dumps(data).encode("utf-8")).decode("ascii")
                mime_type = "application/json"

            self.session_globals["__artifacts__"].append({
                "name": name,
                "data": b64_data,
                "type": mime_type,
            })

        self.session_globals = {
            "__builtins__": get_sanitized_builtins(),
            "__name__": "__main__",
            "__doc__": None,
            "__artifacts__": [],
            "save_artifact": _save_artifact,
        }

    def _extract_state_summary(self) -> Dict[str, Any]:
        """Extract a clean, serializable summary of user-defined variables."""
        summary: Dict[str, Any] = {}
        excluded = {"__builtins__", "__name__", "__doc__", "__artifacts__", "__TASK_CONTEXT__"}
        for k, v in self.session_globals.items():
            if k in excluded or k.startswith("_LocalREPLWorker"):
                continue
            try:
                type_name = type(v).__name__
                val_repr = repr(v)
                if len(val_repr) > 500:
                    val_repr = val_repr[:500] + "... [truncated]"
                summary[k] = {"type": type_name, "repr": val_repr}
            except Exception:
                summary[k] = {"type": type(v).__name__, "repr": "<unprintable>"}
        return summary

    def execute_code(
        self,
        code: str,
        repl: bool = True,
    ) -> Dict[str, Any]:
        """
        Execute code within persistent session globals, capturing output and return value.
        """
        start_time = time.perf_counter()
        stdout_buf = io.StringIO()
        stderr_buf = io.StringIO()

        orig_stdout = sys.stdout
        orig_stderr = sys.stderr

        artifacts: List[Dict[str, Any]] = []
        result_repr: Optional[str] = None
        error_msg: Optional[str] = None
        exit_code = 0

        # Ensure __artifacts__ list exists in session
        if "__artifacts__" not in self.session_globals or not isinstance(
            self.session_globals["__artifacts__"], list
        ):
            self.session_globals["__artifacts__"] = []

        try:
            sys.stdout = stdout_buf
            sys.stderr = stderr_buf

            tree = ast.parse(code)
            if not tree.body:
                # Empty code block
                pass
            elif repl and isinstance(tree.body[-1], ast.Expr):
                # Separate statements from the trailing expression
                last_expr = tree.body.pop()
                if tree.body:
                    exec_mod = ast.Module(body=tree.body, type_ignores=[])
                    exec_code = compile(exec_mod, "<sandbox>", "exec")
                    exec(exec_code, self.session_globals)

                eval_mod = ast.Expression(body=last_expr.value)
                eval_code = compile(eval_mod, "<sandbox>", "eval")
                eval_result = eval(eval_code, self.session_globals)

                if eval_result is not None:
                    result_repr = repr(eval_result)
                    # Automatically capture matplotlib figures if present
                    if hasattr(eval_result, "savefig") or "Figure" in type(eval_result).__name__:
                        try:
                            img_buf = io.BytesIO()
                            eval_result.savefig(img_buf, format="png")
                            img_b64 = base64.b64encode(img_buf.getvalue()).decode("ascii")
                            artifacts.append({
                                "type": "image/png",
                                "data": img_b64,
                                "name": "figure.png"
                            })
                        except Exception:
                            pass
            else:
                exec_code = compile(tree, "<sandbox>", "exec")
                exec(exec_code, self.session_globals)

            # Collect any artifacts explicitly appended to __artifacts__
            user_artifacts = self.session_globals.get("__artifacts__", [])
            if isinstance(user_artifacts, list):
                for item in user_artifacts:
                    if isinstance(item, dict):
                        artifacts.append(item)

        except SyntaxError as e:
            exit_code = 1
            error_msg = f"SyntaxError: {e}"
            stderr_buf.write(f"SyntaxError: {e}\n")
        except SecurityViolationError as e:
            exit_code = 1
            error_msg = f"SecurityViolationError: {e}"
            stderr_buf.write(f"SecurityViolationError: {e}\n")
        except Exception as e:
            exit_code = 1
            tb_lines = traceback.format_exception(type(e), e, e.__traceback__)
            # Strip out worker internal frames
            clean_tb = "".join(tb_lines)
            error_msg = f"{type(e).__name__}: {e}"
            stderr_buf.write(clean_tb)
        finally:
            sys.stdout = orig_stdout
            sys.stderr = orig_stderr

        duration_ms = (time.perf_counter() - start_time) * 1000.0
        stdout_str = stdout_buf.getvalue()
        stderr_str = stderr_buf.getvalue()

        # Truncate output if exceeding limits
        if len(stdout_str.encode("utf-8")) > self.max_output_bytes:
            stdout_str = (
                stdout_str[: self.max_output_bytes // 2]
                + "\n... [stdout truncated due to size limit]\n"
            )
        if len(stderr_str.encode("utf-8")) > self.max_output_bytes:
            stderr_str = (
                stderr_str[: self.max_output_bytes // 2]
                + "\n... [stderr truncated due to size limit]\n"
            )

        state_summary = self._extract_state_summary()

        return {
            "exit_code": exit_code,
            "stdout": stdout_str,
            "stderr": stderr_str,
            "result": result_repr,
            "error": error_msg,
            "artifacts": artifacts,
            "state": state_summary,
            "duration_ms": duration_ms,
        }

    def reset_session(self) -> Dict[str, Any]:
        """Reset session namespace."""
        self._init_session()
        return {"status": "ok", "message": "Session reset successfully"}

    def create_snapshot(self, name: str) -> Dict[str, Any]:
        """Create an in-memory snapshot of current session variables."""
        snapshot_id = f"snap_{uuid.uuid4().hex[:12]}"
        saved_state: Dict[str, Any] = {}
        excluded = {"__builtins__"}
        for k, v in self.session_globals.items():
            if k in excluded:
                continue
            try:
                saved_state[k] = copy.deepcopy(v)
            except Exception:
                # If uncopyable, fallback to shallow reference
                saved_state[k] = v

        self.snapshots[snapshot_id] = {
            "name": name,
            "timestamp": time.time(),
            "state": saved_state,
        }
        return {"status": "ok", "snapshot_id": snapshot_id, "name": name}

    def restore_snapshot(self, snapshot_id: str) -> Dict[str, Any]:
        """Restore session variables from snapshot ID."""
        if snapshot_id not in self.snapshots:
            return {"status": "error", "error": f"Snapshot '{snapshot_id}' not found"}

        snap_data = self.snapshots[snapshot_id]["state"]
        self._init_session()
        for k, v in snap_data.items():
            try:
                self.session_globals[k] = copy.deepcopy(v)
            except Exception:
                self.session_globals[k] = v

        return {"status": "ok", "snapshot_id": snapshot_id}

    def list_snapshots(self) -> Dict[str, Any]:
        """List all stored snapshots."""
        snap_list = []
        for sid, sdata in self.snapshots.items():
            snap_list.append({
                "snapshot_id": sid,
                "name": sdata.get("name", ""),
                "timestamp": sdata.get("timestamp", 0.0),
                "variable_count": len(sdata.get("state", {})),
            })
        return {"status": "ok", "snapshots": snap_list}

    def delete_snapshot(self, snapshot_id: str) -> Dict[str, Any]:
        """Delete a snapshot by ID."""
        if snapshot_id in self.snapshots:
            del self.snapshots[snapshot_id]
            return {"status": "ok", "snapshot_id": snapshot_id, "deleted": True}
        return {"status": "error", "error": f"Snapshot '{snapshot_id}' not found", "deleted": False}

    def get_variables(self) -> Dict[str, Any]:
        """Get summary of user variables."""
        return {"status": "ok", "variables": self._extract_state_summary()}

    def export_state(self) -> Dict[str, Any]:
        """Export user-defined session globals as a base64-encoded pickle payload."""
        excluded = {
            "__builtins__", "__name__", "__doc__", "__package__",
            "__loader__", "__spec__", "__artifacts__", "save_artifact",
            "__TASK_CONTEXT__",
        }
        export_dict: Dict[str, Any] = {}
        for k, v in self.session_globals.items():
            if k in excluded or k.startswith("_LocalREPLWorker"):
                continue
            try:
                # Test picklability
                pickle.dumps(v, protocol=pickle.HIGHEST_PROTOCOL)
                export_dict[k] = v
            except Exception:
                pass

        try:
            pkl_data = pickle.dumps(export_dict, protocol=pickle.HIGHEST_PROTOCOL)
            b64_str = base64.b64encode(pkl_data).decode("ascii")
            return {"status": "ok", "state_b64": b64_str, "count": len(export_dict)}
        except Exception as e:
            return {"status": "error", "error": f"Failed exporting state: {e}"}

    def hydrate_state(
        self, state_b64: Optional[str] = None, variables: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Inject variables into session globals."""
        injected_count = 0
        if state_b64:
            try:
                raw_bytes = base64.b64decode(state_b64.encode("ascii"))
                restored_dict = pickle.loads(raw_bytes)
                if isinstance(restored_dict, dict):
                    for k, v in restored_dict.items():
                        self.session_globals[k] = v
                        injected_count += 1
            except Exception as e:
                return {"status": "error", "error": f"Failed hydrating state from b64: {e}"}
        if variables and isinstance(variables, dict):
            for k, v in variables.items():
                self.session_globals[k] = v
                injected_count += 1
        return {"status": "ok", "hydrated_count": injected_count}

    def run_loop(self) -> None:
        """Main stdio JSON line processing loop."""
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                req = json.loads(line)
                req_id = req.get("id", "")
                action = req.get("action", "")

                if action == "ping":
                    res = {"id": req_id, "status": "ok", "pong": True}
                elif action == "execute":
                    code = req.get("code", "")
                    repl = req.get("repl", True)
                    exec_res = self.execute_code(code, repl=repl)
                    res = {"id": req_id, "status": "ok", **exec_res}
                elif action == "reset":
                    reset_res = self.reset_session()
                    res = {"id": req_id, **reset_res}
                elif action == "snapshot":
                    name = req.get("name", "checkpoint")
                    snap_res = self.create_snapshot(name)
                    res = {"id": req_id, **snap_res}
                elif action == "restore":
                    snapshot_id = req.get("snapshot_id", "")
                    restore_res = self.restore_snapshot(snapshot_id)
                    res = {"id": req_id, **restore_res}
                elif action == "list_snapshots":
                    list_res = self.list_snapshots()
                    res = {"id": req_id, **list_res}
                elif action == "delete_snapshot":
                    snapshot_id = req.get("snapshot_id", "")
                    del_res = self.delete_snapshot(snapshot_id)
                    res = {"id": req_id, **del_res}
                elif action == "get_variables":
                    vars_res = self.get_variables()
                    res = {"id": req_id, **vars_res}
                elif action == "export_state":
                    export_res = self.export_state()
                    res = {"id": req_id, **export_res}
                elif action == "hydrate_state":
                    state_b64 = req.get("state_b64")
                    vars_dict = req.get("variables")
                    hydrate_res = self.hydrate_state(state_b64=state_b64, variables=vars_dict)
                    res = {"id": req_id, **hydrate_res}
                elif action == "export_snapshot":
                    snap_id = req.get("snapshot_id", "")
                    if snap_id in self.snapshots:
                        sdata = self.snapshots[snap_id]
                        res = {
                            "id": req_id,
                            "status": "ok",
                            "snapshot_id": snap_id,
                            "name": sdata.get("name", ""),
                            "timestamp": sdata.get("timestamp", 0.0),
                            "state": sdata.get("state", {}),
                        }
                    else:
                        res = {"id": req_id, "status": "error", "error": f"Snapshot '{snap_id}' not found"}
                elif action == "import_snapshot":
                    snap_id = req.get("snapshot_id", "")
                    sname = req.get("name", "imported")
                    sts = req.get("timestamp", time.time())
                    sstate = req.get("state", {})
                    self.snapshots[snap_id] = {
                        "name": sname,
                        "timestamp": sts,
                        "state": sstate,
                    }
                    res = {"id": req_id, "status": "ok", "snapshot_id": snap_id}
                elif action == "exit":
                    res = {"id": req_id, "status": "exiting"}
                    sys.stdout.write(json.dumps(res, ensure_ascii=False) + "\n")
                    sys.stdout.flush()
                    break
                else:
                    res = {
                        "id": req_id,
                        "status": "error",
                        "error": f"Unknown action '{action}'",
                    }

                sys.stdout.write(json.dumps(res, ensure_ascii=False) + "\n")
                sys.stdout.flush()

            except Exception as e:
                err_res = {
                    "id": req.get("id", "") if "req" in locals() else "",
                    "status": "error",
                    "error": f"Worker loop error: {e}",
                    "traceback": traceback.format_exc(),
                }
                sys.stdout.write(json.dumps(err_res, ensure_ascii=False) + "\n")
                sys.stdout.flush()


if __name__ == "__main__":
    import os
    max_bytes_env = os.environ.get("MAX_OUTPUT_BYTES")
    max_bytes = int(max_bytes_env) if max_bytes_env else 2 * 1024 * 1024
    worker = LocalREPLWorker(max_output_bytes=max_bytes)
    worker.run_loop()
