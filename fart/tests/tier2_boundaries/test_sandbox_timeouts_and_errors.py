"""Tier 2: Boundary Tests for Sandbox Timeouts, Exceptions, and Crash Recovery."""

import pytest

from antigravity.sandbox import LocalSandbox, SandboxTimeoutError


def test_execution_timeout_enforcement(local_sandbox: LocalSandbox):
    """Verify that infinite loops are forcefully terminated when timeout expires."""
    res = local_sandbox.execute("while True:\n    pass", timeout=1.0)
    assert res.is_success is False
    assert res.exit_code == 1
    assert "SandboxTimeoutError" in str(res.error) or "timed out" in res.stderr

    # Verify self-healing / subsequent execution works
    res_after = local_sandbox.execute("x = 42\nx")
    assert res_after.is_success is True
    assert res_after.result == "42"


def test_syntax_error_handling(local_sandbox: LocalSandbox):
    """Verify that syntax errors in user code are captured without crashing sandbox."""
    res = local_sandbox.execute("def broken_syntax(")
    assert res.is_success is False
    assert res.exit_code == 1
    assert "SyntaxError" in res.stderr or "SyntaxError" in str(res.error)


def test_runtime_exception_handling(local_sandbox: LocalSandbox):
    """Verify that standard runtime exceptions are caught and reported cleanly."""
    res_div_zero = local_sandbox.execute("x = 10 / 0")
    assert res_div_zero.is_success is False
    assert res_div_zero.exit_code == 1
    assert "ZeroDivisionError" in res_div_zero.stderr or "ZeroDivisionError" in str(res_div_zero.error)

    res_key_err = local_sandbox.execute("d = {}\nval = d['missing_key']")
    assert res_key_err.is_success is False
    assert res_key_err.exit_code == 1
    assert "KeyError" in res_key_err.stderr or "KeyError" in str(res_key_err.error)


def test_output_capping_limit():
    """Verify that enormous stdout output is truncated to prevent memory exhaustion."""
    box = LocalSandbox(timeout=5.0, max_output_bytes=10 * 1024)  # 10KB limit
    try:
        res = box.execute("for _ in range(2000):\n    print('A' * 50)")
        assert res.is_success is True
        assert len(res.stdout) < 20000
        assert "truncated" in res.stdout
    finally:
        box.terminate()
