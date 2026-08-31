"""Tier 3: Cross-Feature Integration Tests for Auto-Fallback and Multi-Sandbox Isolation."""

import pytest

from antigravity.sandbox import SandboxManager, SandboxMode, SandboxState


def test_auto_mode_fallback_to_local(sandbox_manager: SandboxManager):
    """Verify that mode=AUTO falls back gracefully to LocalSandbox when E2B is unconfigured."""
    box = sandbox_manager.create_sandbox(mode=SandboxMode.AUTO)
    assert box is not None
    assert box.mode == SandboxMode.LOCAL
    assert box.status == SandboxState.RUNNING

    res = box.execute("data = [1, 2, 3, 4, 5]\nsum(data)")
    assert res.is_success is True
    assert res.result == "15"


def test_multi_sandbox_isolation(sandbox_manager: SandboxManager):
    """Verify that multiple concurrent sandboxes maintain independent namespaces."""
    sb1 = sandbox_manager.create_sandbox(mode=SandboxMode.LOCAL)
    sb2 = sandbox_manager.create_sandbox(mode=SandboxMode.LOCAL)

    assert sb1.sandbox_id != sb2.sandbox_id

    sb1.execute("shared_name = 'INSTANCE_ONE'")
    sb2.execute("shared_name = 'INSTANCE_TWO'")

    res1 = sb1.execute("shared_name")
    res2 = sb2.execute("shared_name")

    assert res1.result == "'INSTANCE_ONE'"
    assert res2.result == "'INSTANCE_TWO'"
