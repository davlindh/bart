"""SandboxManager: Lifecycle Orchestration, Routing, and Auto-Fallback Engine."""

from __future__ import annotations

import logging
import os
import threading
import time
from typing import Any, Dict, List, Optional

from .base import BaseSandbox
from .e2b_sandbox import E2BSandbox
from .local_sandbox import LocalSandbox
from .models import SandboxError, SandboxExecutionError, SandboxMode, SandboxState

logger = logging.getLogger("antigravity.sandbox.manager")


class SandboxManager:
    """
    Factory and Lifecycle Manager for Sandboxes.

    Handles creation, routing (including automatic graceful fallback between E2B
    and LocalSandbox), tracking, inspection, and teardown of active sandboxes.
    """

    def __init__(self) -> None:
        self._sandboxes: Dict[str, BaseSandbox] = {}
        self._metadata: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()

    def create_sandbox(
        self,
        mode: SandboxMode = SandboxMode.AUTO,
        timeout: float = 300.0,
        env: Optional[Dict[str, str]] = None,
        authorized_imports: Optional[List[str]] = None,
        api_key: Optional[str] = None,
        template: Optional[str] = None,
        **kwargs: Any,
    ) -> BaseSandbox:
        """
        Provision a new sandbox according to requested mode with automatic fallback.

        Args:
            mode: SandboxMode.AUTO, SandboxMode.LOCAL, or SandboxMode.E2B.
            timeout: Maximum default execution/lifetime timeout in seconds.
            env: Environment variables to expose within the sandbox.
            authorized_imports: Additional module names permitted for import.
            api_key: Optional explicit E2B API key.
            template: Optional E2B template name.

        Returns:
            An active, initialized BaseSandbox instance.
        """
        with self._lock:
            sandbox: BaseSandbox
            chosen_backend = mode

            if mode == SandboxMode.E2B:
                # Explicit E2B requested - must succeed or raise error
                sandbox = E2BSandbox(
                    api_key=api_key,
                    template=template,
                    timeout=timeout,
                    env=env,
                    auto_start=True,
                    **kwargs,
                )
            elif mode == SandboxMode.LOCAL:
                # Explicit Local requested
                sandbox = LocalSandbox(
                    timeout=timeout,
                    env=env,
                    authorized_imports=authorized_imports,
                    auto_start=True,
                    **kwargs,
                )
            else:
                # SandboxMode.AUTO: Attempt E2B first if configured, else fallback to Local
                e2b_key = api_key or os.environ.get("E2B_API_KEY")
                e2b_available = False
                if e2b_key:
                    try:
                        import e2b_code_interpreter  # noqa: F401
                        e2b_available = True
                    except ImportError:
                        e2b_available = False

                if e2b_available:
                    try:
                        sandbox = E2BSandbox(
                            api_key=e2b_key,
                            template=template,
                            timeout=timeout,
                            env=env,
                            auto_start=True,
                            **kwargs,
                        )
                    except Exception as e:
                        logger.warning(
                            "E2B initialization failed (%s); falling back to LocalSandbox.",
                            e,
                        )
                        sandbox = LocalSandbox(
                            timeout=timeout,
                            env=env,
                            authorized_imports=authorized_imports,
                            auto_start=True,
                            **kwargs,
                        )
                else:
                    # Seamlessly provision local sandbox
                    sandbox = LocalSandbox(
                        timeout=timeout,
                        env=env,
                        authorized_imports=authorized_imports,
                        auto_start=True,
                        **kwargs,
                    )

            sb_id = sandbox.sandbox_id
            self._sandboxes[sb_id] = sandbox
            self._metadata[sb_id] = {
                "sandbox_id": sb_id,
                "mode": sandbox.mode.value,
                "requested_mode": mode.value,
                "created_at": time.time(),
                "timeout": timeout,
            }

            return sandbox

    def get_sandbox(self, sandbox_id: str) -> Optional[BaseSandbox]:
        """Retrieve an active sandbox by ID."""
        with self._lock:
            return self._sandboxes.get(sandbox_id)

    def list_sandboxes(self) -> List[Dict[str, Any]]:
        """List summary metadata for all managed sandboxes."""
        with self._lock:
            result = []
            for sb_id, sb in self._sandboxes.items():
                meta = self._metadata.get(sb_id, {})
                result.append({
                    "sandbox_id": sb_id,
                    "mode": sb.mode.value,
                    "status": sb.status.value,
                    "created_at": meta.get("created_at", 0.0),
                    "timeout": meta.get("timeout", 300.0),
                })
            return result

    def destroy_sandbox(self, sandbox_id: str) -> bool:
        """Terminate and remove a sandbox by ID."""
        with self._lock:
            sb = self._sandboxes.pop(sandbox_id, None)
            self._metadata.pop(sandbox_id, None)
            if sb is not None:
                try:
                    sb.terminate()
                except Exception as e:
                    logger.error("Error terminating sandbox %s: %s", sandbox_id, e)
                return True
            return False

    def destroy_all(self) -> None:
        """Terminate and clean up all active sandboxes."""
        with self._lock:
            for sb_id in list(self._sandboxes.keys()):
                self.destroy_sandbox(sb_id)

    def __enter__(self) -> "SandboxManager":
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.destroy_all()
