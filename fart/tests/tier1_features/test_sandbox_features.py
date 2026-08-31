"""Tier 1: Feature Tests for Sandbox Subsystem."""

import pytest

from antigravity.sandbox import (
    BaseSandbox,
    E2BSandbox,
    ExecutionResult,
    LocalSandbox,
    SandboxExecutionError,
    SandboxManager,
    SandboxMode,
    SandboxState,
    SnapshotError,
)


def test_basesandbox_interface_subclass():
    """Verify that LocalSandbox and E2BSandbox inherit and implement BaseSandbox."""
    assert issubclass(LocalSandbox, BaseSandbox)
    assert issubclass(E2BSandbox, BaseSandbox)


def test_execution_result_model():
    """Verify ExecutionResult properties and serialization."""
    res = ExecutionResult(
        stdout="output\n",
        stderr="",
        exit_code=0,
        artifacts=[{"type": "text/plain", "data": "abc"}],
        duration_ms=12.5,
        state={"a": {"type": "int", "repr": "1"}},
        backend_used="local",
    )
    assert res.is_success is True
    assert res.success is True
    assert res.duration_seconds == 0.0125
    d = res.to_dict()
    assert d["stdout"] == "output\n"
    assert d["exit_code"] == 0
    assert d["backend_used"] == "local"
    assert d["success"] is True

    err_res = ExecutionResult(exit_code=1, error="SomeError: boom")
    assert err_res.is_success is False
    assert err_res.success is False


def test_local_sandbox_lifecycle(local_sandbox: LocalSandbox):
    """Test LocalSandbox basic execution, pause, resume, and termination."""
    assert local_sandbox.status == SandboxState.RUNNING
    assert local_sandbox.mode == SandboxMode.LOCAL
    assert local_sandbox.sandbox_id.startswith("sb_loc_")

    # Execution
    res = local_sandbox.execute("val = 10 + 20\nprint(f'Computed: {val}')")
    assert res.is_success is True
    assert "Computed: 30" in res.stdout
    assert res.state.get("val", {}).get("repr") == "30"

    # Pause
    local_sandbox.pause()
    assert local_sandbox.status == SandboxState.PAUSED
    with pytest.raises(SandboxExecutionError, match="paused"):
        local_sandbox.execute("print('fail')")

    # Resume
    local_sandbox.resume()
    assert local_sandbox.status == SandboxState.RUNNING
    res2 = local_sandbox.execute("val * 2")
    assert res2.is_success is True
    assert res2.result == "60"

    # Terminate
    local_sandbox.terminate()
    assert local_sandbox.status == SandboxState.TERMINATED
    with pytest.raises(SandboxExecutionError, match="terminated"):
        local_sandbox.execute("print('fail')")


def test_local_sandbox_snapshot_and_restore(local_sandbox: LocalSandbox):
    """Test state snapshotting and restoration."""
    local_sandbox.execute("counter = 1")
    snap1 = local_sandbox.create_snapshot("checkpoint1")
    assert snap1.startswith("snap_")

    local_sandbox.execute("counter = 99")
    res_modified = local_sandbox.execute("counter")
    assert res_modified.result == "99"

    # Restore checkpoint 1
    local_sandbox.restore_snapshot(snap1)
    res_restored = local_sandbox.execute("counter")
    assert res_restored.result == "1"


def test_sandbox_manager_lifecycle(sandbox_manager: SandboxManager):
    """Test SandboxManager factory creation, listing, retrieval, and destruction."""
    sb1 = sandbox_manager.create_sandbox(mode=SandboxMode.LOCAL)
    assert sb1.sandbox_id in [s["sandbox_id"] for s in sandbox_manager.list_sandboxes()]

    retrieved = sandbox_manager.get_sandbox(sb1.sandbox_id)
    assert retrieved is sb1

    res = sb1.execute("message = 'antigravity rocks'")
    assert res.is_success is True

    # Destroy specific sandbox
    destroyed = sandbox_manager.destroy_sandbox(sb1.sandbox_id)
    assert destroyed is True
    assert sandbox_manager.get_sandbox(sb1.sandbox_id) is None
    assert sb1.status == SandboxState.TERMINATED


def test_mock_e2b_sandbox(mock_e2b_sandbox: E2BSandbox):
    """Test E2BSandbox execution and lifecycle with injected mock driver."""
    assert mock_e2b_sandbox.status == SandboxState.RUNNING
    assert mock_e2b_sandbox.mode == SandboxMode.E2B

    res = mock_e2b_sandbox.execute("print('Hello from microVM')")
    assert res.is_success is True
    assert "Hello from microVM" in res.stdout
    assert res.backend_used == "e2b"

    snap_id = mock_e2b_sandbox.create_snapshot("snap_e2b")
    assert snap_id is not None

    mock_e2b_sandbox.restore_snapshot(snap_id)
    mock_e2b_sandbox.pause()
    assert mock_e2b_sandbox.status == SandboxState.PAUSED
    mock_e2b_sandbox.resume()
    assert mock_e2b_sandbox.status == SandboxState.RUNNING
    mock_e2b_sandbox.terminate()
    assert mock_e2b_sandbox.status == SandboxState.TERMINATED


def test_e2b_sandbox_missing_api_key_raises():
    """Test that explicit E2BSandbox without API key raises SandboxExecutionError."""
    with pytest.raises(SandboxExecutionError, match="API key not found"):
        E2BSandbox(api_key="", auto_start=True)
