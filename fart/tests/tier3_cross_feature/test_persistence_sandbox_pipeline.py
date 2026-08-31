"""Cross-feature integration tests: LocalSandbox state persistence across process boundaries."""

import tempfile
from pathlib import Path
import pytest

from antigravity.sandbox.local_sandbox import LocalSandbox
from antigravity.storage.models import StorageConfig
from antigravity.storage.persistence_manager import PersistenceManager


@pytest.fixture
def temp_storage_dir():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
        yield Path(tmpdir)


class TestPersistenceSandboxPipeline:
    def test_sandbox_state_roundtrip_across_process_boundary(self, temp_storage_dir):
        config = StorageConfig(base_dir=str(temp_storage_dir))
        pm = PersistenceManager(config)

        # 1. Run initial sandbox session
        sandbox_id = "sb-persist-test-1"
        sb = LocalSandbox(sandbox_id=sandbox_id)
        try:
            exec_res = sb.execute("x = 42; y = [10, 20, 30]; msg = 'hello persistent world'")
            assert exec_res.exit_code == 0

            # Verify variables in session
            vars_summary = sb.get_variables()
            assert "x" in vars_summary
            assert "msg" in vars_summary

            # Persist sandbox session
            record = pm.save_sandbox(sb)
            assert record.sandbox_id == sandbox_id
            assert record.variable_count >= 3
        finally:
            sb.terminate()
            pm.close()

        # 2. Simulate Clean Subprocess / Restart in new PersistenceManager
        pm_clean = PersistenceManager(StorageConfig(base_dir=str(temp_storage_dir)))
        sb_restored = pm_clean.restore_sandbox(sandbox_id, auto_start=True)

        try:
            # Execute code referencing previously computed variables
            res = sb_restored.execute("res = f'{msg}: {x + sum(y)}'; print(res)")
            assert res.exit_code == 0
            assert "hello persistent world: 102" in res.stdout.strip()

            # Mutate state in restored session
            res2 = sb_restored.execute("x = x * 2; y.append(40); print(x, sum(y))")
            assert res2.exit_code == 0
            assert "84 100" in res2.stdout.strip()
        finally:
            sb_restored.terminate()
            pm_clean.close()

    def test_sandbox_snapshot_restore_pipeline(self, temp_storage_dir):
        config = StorageConfig(base_dir=str(temp_storage_dir))
        pm = PersistenceManager(config)

        sandbox_id = "sb-snap-pipeline"
        sb = LocalSandbox(sandbox_id=sandbox_id)
        try:
            # State 1
            sb.execute("stage = 1; value = 100")
            snap1 = pm.save_snapshot(
                sandbox_id=sandbox_id,
                name="stage_1",
                variables=sb.export_state(),
                branch_name="main",
            )

            # State 2
            sb.execute("stage = 2; value = 200; extra = 'added in stage 2'")
            snap2 = pm.save_snapshot(
                sandbox_id=sandbox_id,
                name="stage_2",
                variables=sb.export_state(),
                parent_snapshot_id=snap1.snapshot_id,
                branch_name="main",
            )

            # Revert to State 1
            pm.restore_snapshot(sb, snap1.snapshot_id)
            res = sb.execute("has_extra = 'extra' in dir(); print(f'stage={stage}, value={value}, has_extra={has_extra}')")
            assert res.exit_code == 0
            assert "stage=1, value=100" in res.stdout.strip()

            # Advance to State 2
            pm.restore_snapshot(sb, snap2.snapshot_id)
            res2 = sb.execute("print(f'stage={stage}, value={value}, extra={extra}')")
            assert res2.exit_code == 0
            assert "stage=2, value=200, extra=added in stage 2" in res2.stdout.strip()
        finally:
            sb.terminate()
            pm.close()
