"""Tests for optimized LocalSandbox capabilities and lifecycle features."""

import os
import tempfile
import pytest
from antigravity.sandbox.local_sandbox import LocalSandbox
from antigravity.sandbox.models import SandboxState, SandboxMode
from antigravity.mcp.tools import MCPToolRegistry
from antigravity.mcp.schemas import ManageSnapshotInput, CreateSandboxInput, ExecuteCodeInput


class TestLocalSandboxOptimal:
    """Test suite for hardened and optimized LocalSandbox."""

    def test_local_sandbox_snapshots_lifecycle(self):
        """Verify create, list, restore, and delete snapshot operations on LocalSandbox."""
        sb = LocalSandbox(auto_start=True)
        try:
            # Turn 1: initialize state
            res1 = sb.execute("x = 100\nitems = ['alpha', 'beta']")
            assert res1.is_success

            # Create snapshot 1
            snap1_id = sb.create_snapshot("checkpoint_1")
            assert snap1_id.startswith("snap_")

            # Turn 2: mutate state
            res2 = sb.execute("x = 999\nitems.append('gamma')\ny = 'extra'")
            assert res2.is_success
            vars_mutated = sb.get_variables()
            assert "y" in vars_mutated

            # Create snapshot 2
            snap2_id = sb.create_snapshot("checkpoint_2")

            # List snapshots
            snapshots = sb.list_snapshots()
            assert len(snapshots) >= 2
            snap_ids = [s["snapshot_id"] for s in snapshots]
            assert snap1_id in snap_ids
            assert snap2_id in snap_ids

            # Restore snapshot 1
            sb.restore_snapshot(snap1_id)
            res3 = sb.execute("x + len(items)")
            assert res3.is_success
            assert res3.result == "102"  # 100 + 2

            # Delete snapshot 2
            deleted = sb.delete_snapshot(snap2_id)
            assert deleted is True
            remaining = sb.list_snapshots()
            remaining_ids = [s["snapshot_id"] for s in remaining]
            assert snap2_id not in remaining_ids
            assert snap1_id in remaining_ids
        finally:
            sb.terminate()

    def test_local_sandbox_utf8_and_unicode_handling(self):
        """Verify LocalSandbox handles UTF-8, Swedish text, emojis, and math characters."""
        sb = LocalSandbox(auto_start=True)
        try:
            code = """
swedish_text = "Öppen Källkod För Virtuella Maskiner: År 2026"
emoji_str = "🚀 Multi-Agent Sandbox 🛡️"
math_str = "π ≈ 3.14159, ∑(1..n)"
print(f"Processed: {swedish_text} | {emoji_str}")
result = f"{swedish_text} -> {emoji_str}"
result
"""
            res = sb.execute(code)
            assert res.is_success
            assert "Öppen Källkod För Virtuella Maskiner" in res.stdout
            assert "🚀" in res.stdout
            assert "Öppen Källkod För Virtuella Maskiner" in str(res.result)
        finally:
            sb.terminate()

    def test_local_sandbox_scientific_and_standard_modules(self):
        """Verify expanded allowed standard and data science modules."""
        sb = LocalSandbox(auto_start=True)
        try:
            code = """
import math
import statistics
import json
import csv
import io
import datetime
import sqlite3

mean_val = statistics.mean([10, 20, 30, 40])
pi_val = math.pi
now_iso = datetime.datetime(2026, 8, 29).isoformat()

# In-memory SQLite check
conn = sqlite3.connect(":memory:")
cur = conn.cursor()
cur.execute("CREATE TABLE metrics (id INT, val REAL)")
cur.execute("INSERT INTO metrics VALUES (1, 99.5)")
conn.commit()
row = cur.execute("SELECT val FROM metrics").fetchone()
conn.close()

{"mean": mean_val, "pi": pi_val, "db_val": row[0]}
"""
            res = sb.execute(code)
            assert res.is_success
            assert "mean" in str(res.result)
            assert "99.5" in str(res.result)
        finally:
            sb.terminate()

    def test_local_sandbox_custom_artifact_helper(self):
        """Verify save_artifact helper function inside sandbox."""
        sb = LocalSandbox(auto_start=True)
        try:
            code = """
data_report = {"status": "optimized", "score": 100}
save_artifact("report.json", data_report, "application/json")
save_artifact("notes.txt", "LocalSandbox is optimally supported.", "text/plain")
"Done"
"""
            res = sb.execute(code)
            assert res.is_success
            assert len(res.artifacts) == 2
            art_names = [a["name"] for a in res.artifacts]
            assert "report.json" in art_names
            assert "notes.txt" in art_names
        finally:
            sb.terminate()

    def test_local_sandbox_working_directory_isolation(self):
        """Verify work_dir parameter customizes execution directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            sb = LocalSandbox(work_dir=temp_dir, auto_start=True)
            try:
                assert sb.work_dir == temp_dir
                res = sb.execute("a = 42\na * 2")
                assert res.is_success
                assert res.result == "84"
            finally:
                sb.terminate()

    def test_local_sandbox_auto_recovery_after_process_kill(self):
        """Verify LocalSandbox re-spawns worker if process was forcefully terminated."""
        sb = LocalSandbox(auto_start=True)
        try:
            res1 = sb.execute("val = 12345")
            assert res1.is_success

            # Simulate worker process crash
            sb._kill_worker()
            assert sb._process is None

            # Next command should auto-re-spawn worker
            res2 = sb.execute("fresh_val = 54321\nfresh_val * 2")
            assert res2.is_success
            assert res2.result == "108642"
        finally:
            sb.terminate()

    def test_mcp_manage_snapshot_list_and_delete_on_local(self):
        """Verify MCP manage_snapshot tool works seamlessly with list and delete on LocalSandbox."""
        import asyncio
        async def _run():
            registry = MCPToolRegistry()
            
            # 1. Create sandbox
            create_res = await registry.call_tool("create_sandbox", {"mode": "local"})
            assert create_res["isError"] is False
            import json
            sb_info = json.loads(create_res["content"][0]["text"])
            sb_id = sb_info["sandbox_id"]

            try:
                # 2. Execute code
                await registry.call_tool("execute_code", {
                    "sandbox_id": sb_id,
                    "code": "a = 10\nb = 20",
                })

                # 3. Create snapshot
                snap_res = await registry.call_tool("manage_snapshot", {
                    "sandbox_id": sb_id,
                    "action": "create",
                    "name": "mcp_checkpoint",
                })
                assert snap_res["isError"] is False
                snap_data = json.loads(snap_res["content"][0]["text"])
                snap_id = snap_data["snapshot_id"]

                # 4. List snapshots
                list_res = await registry.call_tool("manage_snapshot", {
                    "sandbox_id": sb_id,
                    "action": "list",
                })
                assert list_res["isError"] is False
                list_data = json.loads(list_res["content"][0]["text"])
                assert len(list_data["snapshots"]) >= 1

                # 5. Delete snapshot
                del_res = await registry.call_tool("manage_snapshot", {
                    "sandbox_id": sb_id,
                    "action": "delete",
                    "snapshot_id": snap_id,
                })
                assert del_res["isError"] is False
                del_data = json.loads(del_res["content"][0]["text"])
                assert del_data["deleted"] is True
            finally:
                registry.sandbox_manager.destroy_sandbox(sb_id)

        asyncio.run(_run())
