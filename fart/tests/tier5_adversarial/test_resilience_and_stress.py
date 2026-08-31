"""Tier 5: Resilience, Concurrency, Crash Recovery, and Snapshot Stress Harness."""

from __future__ import annotations

import concurrent.futures
import time
import pytest

from antigravity.sandbox import (
    LocalSandbox,
    SandboxManager,
    SandboxMode,
    SandboxState,
    SnapshotError,
)


def test_infinite_loop_timeout_and_recovery():
    """Verify that infinite loops are halted by timeout and the sandbox recovers on next execution."""
    sandbox = LocalSandbox(timeout=60.0)
    try:
        # 1. Execute infinite loop with 0.5s timeout
        t0 = time.perf_counter()
        res_timeout = sandbox.execute("while True: pass", timeout=0.5)
        elapsed = time.perf_counter() - t0

        assert res_timeout.is_success is False
        assert res_timeout.exit_code == 1
        assert "SandboxTimeoutError" in str(res_timeout.error) or "timed out" in res_timeout.stderr
        assert elapsed >= 0.45  # Should have waited at least ~0.5s

        # 2. Immediately verify subsequent command works and sandbox automatically recovers
        res_rec = sandbox.execute("x = 42\nx * 2", timeout=5.0)
        assert res_rec.is_success is True
        assert res_rec.exit_code == 0
        assert res_rec.result == "84"
        assert sandbox.status == SandboxState.RUNNING
    finally:
        sandbox.terminate()


def test_nested_infinite_loop_with_allocations():
    """Verify infinite loop with memory allocations is terminated cleanly."""
    sandbox = LocalSandbox(timeout=60.0)
    try:
        res = sandbox.execute("acc = []\nwhile True:\n    acc.append('memory_chunk')", timeout=0.5)
        assert res.is_success is False
        assert res.exit_code == 1
        assert "SandboxTimeoutError" in str(res.error) or "timed out" in res.stderr

        # Recover and check clean namespace
        res_clean = sandbox.execute("10 + 20")
        assert res_clean.is_success is True
        assert res_clean.result == "30"
    finally:
        sandbox.terminate()


def test_deep_recursion_handling():
    """Verify deep recursion stack overflow is safely caught without crashing the worker."""
    sandbox = LocalSandbox()
    try:
        code = """
def recurse(n):
    return recurse(n + 1)
recurse(0)
"""
        res = sandbox.execute(code)
        assert res.is_success is False
        assert res.exit_code == 1
        assert "RecursionError" in str(res.error) or "RecursionError" in res.stderr

        # Worker should remain alive and functional
        res_after = sandbox.execute("y = 100\ny + 50")
        assert res_after.is_success is True
        assert res_after.result == "150"
    finally:
        sandbox.terminate()


def test_worker_process_kill_and_recovery():
    """Simulate abrupt worker subprocess crash (SIGKILL) and verify transparent recovery."""
    sandbox = LocalSandbox()
    try:
        # Establish initial state
        res1 = sandbox.execute("val = 999")
        assert res1.is_success is True

        # Forcibly terminate the underlying subprocess
        assert sandbox._process is not None
        sandbox._process.kill()
        sandbox._process.wait(timeout=2.0)
        assert sandbox._process.poll() is not None

        # Next execution should automatically respawn worker and execute cleanly
        res2 = sandbox.execute("a = 123; a * 2")
        assert res2.is_success is True
        assert res2.exit_code == 0
        assert res2.result == "246"
        assert sandbox.status == SandboxState.RUNNING
    finally:
        sandbox.terminate()


def test_snapshot_multibranch_restoration_tree():
    """Verify multi-branch snapshot tree creation, state preservation, and branching isolation."""
    sandbox = LocalSandbox()
    try:
        # 1. Base root state
        sandbox.execute("root_var = 'ROOT'\ncounter = 0\ndata_list = [1, 2]")
        snap_root = sandbox.create_snapshot("root_checkpoint")
        assert snap_root.startswith("snap_")

        # 2. Branch A
        sandbox.execute("branch = 'A'\ncounter = 100\ndata_list.append(3)")
        snap_a = sandbox.create_snapshot("branch_a_checkpoint")

        # Mutate Branch A further
        sandbox.execute("counter = 101")
        assert sandbox.execute("counter").result == "101"

        # 3. Restore Root
        sandbox.restore_snapshot(snap_root)
        assert sandbox.execute("counter").result == "0"
        assert sandbox.execute("data_list").result == "[1, 2]"
        res_branch_undef = sandbox.execute("branch")
        assert res_branch_undef.is_success is False
        assert "NameError" in str(res_branch_undef.error) or "NameError" in res_branch_undef.stderr

        # 4. Branch B
        sandbox.execute("branch = 'B'\ncounter = 200\ndict_data = {'k': 'v'}")
        snap_b = sandbox.create_snapshot("branch_b_checkpoint")

        # Mutate dict_data in Branch B
        sandbox.execute("dict_data['k'] = 'modified_v'")

        # 5. Restore Branch A
        sandbox.restore_snapshot(snap_a)
        assert sandbox.execute("branch").result == "'A'"
        assert sandbox.execute("counter").result == "100"
        assert sandbox.execute("data_list").result == "[1, 2, 3]"
        assert sandbox.execute("dict_data").is_success is False

        # 6. Restore Branch B
        sandbox.restore_snapshot(snap_b)
        assert sandbox.execute("branch").result == "'B'"
        assert sandbox.execute("counter").result == "200"
        # Deep copy verification: original snapshot had 'v'
        assert sandbox.execute("dict_data['k']").result == "'v'"

        # 7. Non-existent snapshot error
        with pytest.raises(SnapshotError, match="not found"):
            sandbox.restore_snapshot("snap_non_existent_12345")
    finally:
        sandbox.terminate()


def test_concurrent_sandbox_creation_and_destruction():
    """Stress test rapid concurrent creation, execution, and destruction using SandboxManager."""
    manager = SandboxManager()
    num_concurrent_workers = 20
    executions_per_worker = 3

    def worker_lifecycle_task(worker_id: int) -> dict:
        sb = manager.create_sandbox(mode=SandboxMode.LOCAL, timeout=30.0)
        sb_id = sb.sandbox_id
        results = []
        try:
            for i in range(executions_per_worker):
                multiplier = (worker_id + 1) * 10
                code = f"val_{i} = {i} * {multiplier}\nval_{i}"
                res = sb.execute(code)
                assert res.is_success is True
                assert res.result == str(i * multiplier)
                results.append(res.result)

            # Test snapshot in concurrent environment
            snap_id = sb.create_snapshot(f"snap_w_{worker_id}")
            sb.execute(f"val_0 = 99999")
            sb.restore_snapshot(snap_id)
            res_restored = sb.execute("val_0")
            assert res_restored.result == "0"

            return {"worker_id": worker_id, "sandbox_id": sb_id, "success": True}
        finally:
            manager.destroy_sandbox(sb_id)

    with concurrent.futures.ThreadPoolExecutor(max_workers=num_concurrent_workers) as executor:
        futures = [executor.submit(worker_lifecycle_task, i) for i in range(num_concurrent_workers)]
        for f in concurrent.futures.as_completed(futures):
            res = f.result()
            assert res["success"] is True

    # Ensure all sandboxes were cleaned up
    assert len(manager.list_sandboxes()) == 0
    manager.destroy_all()


def test_massive_output_truncation_stress():
    """Verify that generating millions of bytes of stdout is safely truncated and doesn't deadlock."""
    sandbox = LocalSandbox(max_output_bytes=100 * 1024)  # 100 KB limit
    try:
        # Output 5 MB
        res = sandbox.execute("print('X' * (5 * 1024 * 1024))")
        assert res.is_success is True
        assert len(res.stdout.encode("utf-8")) <= 150 * 1024
        assert "truncated due to size limit" in res.stdout

        # Verify next turn is completely unaffected
        res2 = sandbox.execute("'unaffected'")
        assert res2.result == "'unaffected'"
    finally:
        sandbox.terminate()


def test_special_characters_and_unicode_handling():
    """Verify handling of complex unicode, emojis, and escaped strings."""
    sandbox = LocalSandbox()
    try:
        code = r"""
s = "🚀 Antigravity Sandbox: こんにちは, 世界! \t \u2764"
emoji_len = len("🚀")
s
"""
        res = sandbox.execute(code)
        assert res.is_success is True
        assert "🚀 Antigravity Sandbox" in res.result
        assert res.state["s"]["type"] == "str"
        assert res.state["emoji_len"]["repr"] == "1"
    finally:
        sandbox.terminate()


def test_rapid_sequential_execution_stress():
    """Verify rapid fire execution of 50 turns without latency degradation or memory leaks."""
    sandbox = LocalSandbox()
    try:
        for i in range(50):
            res = sandbox.execute(f"num_{i} = {i}\nnum_{i} ** 2")
            assert res.is_success is True
            assert res.result == str(i ** 2)

        vars_dict = sandbox.get_variables()
        assert len(vars_dict) >= 50
        assert vars_dict["num_49"]["repr"] == "49"
    finally:
        sandbox.terminate()
