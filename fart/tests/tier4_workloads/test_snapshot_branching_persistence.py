"""Workload test: Multi-branch snapshot DAG persistence and tree traversal."""

import tempfile
from pathlib import Path
import pytest

from antigravity.storage.models import StorageConfig
from antigravity.storage.persistence_manager import PersistenceManager


@pytest.fixture
def temp_storage_dir():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
        yield Path(tmpdir)


class TestSnapshotBranchingPersistence:
    def test_multi_branch_snapshot_dag_workflow(self, temp_storage_dir):
        config = StorageConfig(base_dir=str(temp_storage_dir))
        pm = PersistenceManager(config)
        try:
            sandbox_id = "sb-dag-demo"

            # 1. Root Snapshot
            vars_root = {"model_name": "base-model", "epochs": 0, "accuracy": 0.50}
            snap_root = pm.save_snapshot(
                sandbox_id=sandbox_id,
                snapshot_id="snap_root",
                name="Root Initial",
                variables=vars_root,
                branch_name="main",
                description="Initial state before experiments",
            )

            # 2. Main Branch Child 1
            vars_main_1 = {**vars_root, "epochs": 5, "accuracy": 0.72}
            snap_main_1 = pm.save_snapshot(
                sandbox_id=sandbox_id,
                snapshot_id="snap_main_1",
                name="Main Epoch 5",
                variables=vars_main_1,
                parent_snapshot_id="snap_root",
                branch_name="main",
            )

            # 3. Main Branch Child 2
            vars_main_2 = {**vars_main_1, "epochs": 10, "accuracy": 0.85}
            snap_main_2 = pm.save_snapshot(
                sandbox_id=sandbox_id,
                snapshot_id="snap_main_2",
                name="Main Epoch 10",
                variables=vars_main_2,
                parent_snapshot_id="snap_main_1",
                branch_name="main",
            )

            # 4. Fork Branch "experiment-A" (from snap_main_1 with high learning rate)
            vars_exp_a = {**vars_main_1, "lr": 0.05, "accuracy": 0.79, "branch_note": "high_lr"}
            snap_exp_a = pm.save_snapshot(
                sandbox_id=sandbox_id,
                snapshot_id="snap_exp_a",
                name="Exp A Fork",
                variables=vars_exp_a,
                parent_snapshot_id="snap_main_1",
                branch_name="experiment-A",
            )

            # 5. Fork Branch "experiment-B" (from snap_root with different architecture)
            vars_exp_b = {**vars_root, "architecture": "transformer_lite", "accuracy": 0.65}
            snap_exp_b = pm.save_snapshot(
                sandbox_id=sandbox_id,
                snapshot_id="snap_exp_b",
                name="Exp B Architecture Change",
                variables=vars_exp_b,
                parent_snapshot_id="snap_root",
                branch_name="experiment-B",
            )

            # 6. Verify DAG Tree Structure
            tree = pm.get_snapshot_tree(sandbox_id)
            assert tree["total_snapshots"] == 5
            assert "snap_root" in tree["roots"]
            assert len(tree["roots"]) == 1

            # Check branches
            assert "main" in tree["branches"]
            assert "experiment-A" in tree["branches"]
            assert "experiment-B" in tree["branches"]
            assert len(tree["branches"]["main"]) == 3
            assert len(tree["branches"]["experiment-A"]) == 1
            assert len(tree["branches"]["experiment-B"]) == 1

            # Check parent-child relations
            root_children = tree["nodes"]["snap_root"]["children"]
            assert "snap_main_1" in root_children
            assert "snap_exp_b" in root_children

            main1_children = tree["nodes"]["snap_main_1"]["children"]
            assert "snap_main_2" in main1_children
            assert "snap_exp_a" in main1_children

            # 7. Verify isolated state retrieval per snapshot
            _, state_exp_a = pm.load_snapshot(sandbox_id, "snap_exp_a")
            assert state_exp_a["lr"] == 0.05
            assert state_exp_a["accuracy"] == 0.79
            assert "architecture" not in state_exp_a

            _, state_exp_b = pm.load_snapshot(sandbox_id, "snap_exp_b")
            assert state_exp_b["architecture"] == "transformer_lite"
            assert state_exp_b["accuracy"] == 0.65
            assert "lr" not in state_exp_b
        finally:
            pm.close()
