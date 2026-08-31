"""Tier 4: Real-World Application Workloads — Multi-Turn Agent with Local Model & Persistence (Requirement R5).

Tests end-to-end integration combining:
1. LocalModelRunner (Nemotron / lightweight mathematical transformer engine)
2. LocalSandbox (secure multi-turn REPL with ML security whitelisting)
3. Disk-backed PersistenceManager (SQLite WAL & filesystem blob store)
4. Multi-branch snapshot tree exploration and state inspection
"""

import tempfile
import time
from pathlib import Path
import pytest

from antigravity.models import (
    ChatMessage,
    GenerationConfig,
    LocalModelRunner,
    ModelBackend,
    ModelConfig,
)
from antigravity.sandbox import LocalSandbox, SandboxManager
from antigravity.scheduler.daemon import ServiceWorkerDaemon
from antigravity.scheduler.models import ScheduledTask, TaskTriggerType
from antigravity.storage.models import StorageConfig
from antigravity.storage.persistence_manager import PersistenceManager


@pytest.fixture
def temp_storage_dir():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
        yield Path(tmpdir)


class TestMultiTurnAgentWithLocalModel:
    """End-to-end workload test suite for multi-turn agent execution with local models and persistence."""

    def test_multi_turn_agent_reasoning_and_sandbox_execution(self, temp_storage_dir):
        """Simulates an autonomous AI agent reasoning with local model, running sandboxed code, persisting state, and resuming."""
        storage_cfg = StorageConfig(base_dir=str(temp_storage_dir))
        pm = PersistenceManager(storage_cfg)
        model_runner = LocalModelRunner.load("nvidia/Nemotron-Mini-4B-Instruct")
        sandbox_id = "sb-agent-workload-01"

        sb = LocalSandbox(sandbox_id=sandbox_id)
        try:
            # Turn 1: Agent receives problem, queries model, and executes data ingestion in sandbox
            gen_prompt = "Generate Python code to create a matrix of random weights and compute row means."
            gen_res = model_runner.generate(gen_prompt, config=GenerationConfig(max_new_tokens=20))
            assert gen_res.tokens_generated > 0
            assert gen_res.duration_ms >= 0

            turn1_code = """
import math
matrix = [
    [1.0, 2.0, 3.0],
    [4.0, 5.0, 6.0],
    [7.0, 8.0, 9.0]
]
row_means = [sum(row) / len(row) for row in matrix]
overall_mean = sum(row_means) / len(row_means)
print(f"TURN1_DONE: overall_mean={overall_mean}")
"""
            res1 = sb.execute(turn1_code, repl=True)
            assert res1.exit_code == 0
            assert "TURN1_DONE: overall_mean=5.0" in res1.stdout

            # Turn 2: Agent computes normalization transformation on state retained in REPL
            turn2_code = """
normalized_matrix = [[(val - overall_mean) for val in row] for row in matrix]
var_calc = sum(sum((val ** 2) for val in row) for row in normalized_matrix) / 9.0
std_dev = math.sqrt(var_calc)
print(f"TURN2_DONE: std_dev={round(std_dev, 4)}")
"""
            res2 = sb.execute(turn2_code, repl=True)
            assert res2.exit_code == 0
            assert "TURN2_DONE: std_dev=2.582" in res2.stdout

            # Turn 3: Agent saves session state to disk
            saved_record = pm.save_sandbox(sb)
            assert saved_record.sandbox_id == sandbox_id
            assert saved_record.variable_count >= 5

            # Simulate agent session termination / crash
            sb.destroy()

            # Turn 4: Fresh process hydration from disk
            restored_sb = pm.restore_sandbox(sandbox_id)
            try:
                # Turn 5: Continue computation on restored state in the fresh sandbox process
                turn3_code = """
z_scores = [[round(val / std_dev, 3) for val in row] for row in normalized_matrix]
print(f"TURN3_DONE: z_score_0_0={z_scores[0][0]}, z_score_2_2={z_scores[2][2]}")
"""
                res3 = restored_sb.execute(turn3_code, repl=True)
                assert res3.exit_code == 0
                assert "TURN3_DONE: z_score_0_0=-1.549, z_score_2_2=1.549" in res3.stdout

                # Final model synthesis
                chat_res = model_runner.chat(
                    [
                        ChatMessage(role="system", content="You are a data analysis agent."),
                        ChatMessage(role="user", content="The z-scores are -1.549 and 1.549. Summarize."),
                    ],
                    config=GenerationConfig(max_new_tokens=15),
                )
                assert chat_res.tokens_generated > 0
                assert chat_res.finish_reason in ("stop", "length")
            finally:
                restored_sb.destroy()
        finally:
            pm.close()

    def test_multi_turn_chat_with_context_accumulation_and_state_inspection(self):
        """Validates multi-turn chat dialog tracking with context window expansion and state inspection."""
        runner = LocalModelRunner.load("nvidia/Nemotron-Mini-4B-Instruct")
        messages = [
            ChatMessage(role="system", content="You are an expert computational assistant.")
        ]

        # Turn 1
        messages.append(ChatMessage(role="user", content="What is an eigenvalue?"))
        res1 = runner.chat(messages, config=GenerationConfig(max_new_tokens=10, temperature=0.3))
        assert res1.tokens_generated > 0
        prompt_tokens_1 = res1.prompt_tokens
        messages.append(ChatMessage(role="assistant", content=res1.text))

        # Turn 2
        messages.append(ChatMessage(role="user", content="How do you compute them in Python?"))
        res2 = runner.chat(messages, config=GenerationConfig(max_new_tokens=10, temperature=0.3))
        assert res2.tokens_generated > 0
        prompt_tokens_2 = res2.prompt_tokens
        # Context accumulated -> prompt tokens should increase
        assert prompt_tokens_2 > prompt_tokens_1
        messages.append(ChatMessage(role="assistant", content=res2.text))

        # Turn 3
        messages.append(ChatMessage(role="user", content="Provide a 2x2 matrix example."))
        res3 = runner.chat(messages, config=GenerationConfig(max_new_tokens=15, temperature=0.3))
        assert res3.tokens_generated > 0
        assert res3.prompt_tokens > prompt_tokens_2
        assert len(messages) == 6

    def test_model_driven_snapshot_branching_and_state_recovery(self, temp_storage_dir):
        """Validates model-guided parameter optimization across branching snapshot trees."""
        config = StorageConfig(base_dir=str(temp_storage_dir))
        pm = PersistenceManager(config)
        sandbox_id = "sb-branching-workload"
        sb = LocalSandbox(sandbox_id=sandbox_id)

        try:
            # Baseline execution on main branch
            sb.execute("model_type = 'linear'; lr = 0.01; accuracy = 0.65", repl=True)
            snap_base = pm.save_snapshot(
                sandbox_id=sandbox_id,
                snapshot_id="snap_baseline",
                name="Baseline Model",
                variables=sb.export_state(),
                branch_name="main",
            )
            assert snap_base.snapshot_id == "snap_baseline"

            # Branch A: Transformer Optimization
            sb.execute("model_type = 'transformer'; lr = 0.0001; accuracy = 0.92; heads = 8", repl=True)
            snap_tf = pm.save_snapshot(
                sandbox_id=sandbox_id,
                snapshot_id="snap_transformer",
                name="Transformer Branch",
                variables=sb.export_state(),
                parent_snapshot_id="snap_baseline",
                branch_name="feature-transformer",
            )
            assert snap_tf.branch_name == "feature-transformer"

            # Reset back to baseline for Branch B: CNN Optimization
            sb.reset_session()
            pm.restore_snapshot(sb, "snap_baseline")
            check_base = sb.execute("print(model_type, accuracy)", repl=True)
            assert "linear 0.65" in check_base.stdout

            sb.execute("model_type = 'cnn'; lr = 0.005; accuracy = 0.88; kernels = 16", repl=True)
            snap_cnn = pm.save_snapshot(
                sandbox_id=sandbox_id,
                snapshot_id="snap_cnn",
                name="CNN Branch",
                variables=sb.export_state(),
                parent_snapshot_id="snap_baseline",
                branch_name="feature-cnn",
            )
            assert snap_cnn.branch_name == "feature-cnn"

            # Verify DAG structure in storage
            tree = pm.get_snapshot_tree(sandbox_id)
            assert tree["total_snapshots"] == 3
            assert len(tree["roots"]) == 1
            assert "feature-transformer" in tree["branches"]
            assert "feature-cnn" in tree["branches"]

            # Switch between branches and verify variables
            sb.reset_session()
            pm.restore_snapshot(sb, "snap_transformer")
            check_tf = sb.execute("print(model_type, accuracy, heads)", repl=True)
            assert "transformer 0.92 8" in check_tf.stdout

            sb.reset_session()
            pm.restore_snapshot(sb, "snap_cnn")
            check_cnn = sb.execute("print(model_type, accuracy, kernels)", repl=True)
            assert "cnn 0.88 16" in check_cnn.stdout
        finally:
            sb.destroy()
            pm.close()

    def test_local_model_execution_within_sandboxed_service_worker(self, temp_storage_dir):
        """Validates executing local model inference code safely inside background scheduled service workers."""
        storage_cfg = StorageConfig(base_dir=str(temp_storage_dir))
        pm = PersistenceManager(storage_cfg)
        mgr = SandboxManager()
        daemon = ServiceWorkerDaemon(sandbox_manager=mgr)

        sb = mgr.create_sandbox(sandbox_id="sb-worker-model-runner")
        try:
            worker_code = """
from antigravity.models import LocalModelRunner, GenerationConfig

runner = LocalModelRunner.load("nvidia/Nemotron-Mini-4B-Instruct")
result = runner.generate("Worker task execution test", config=GenerationConfig(max_new_tokens=5))
print(f"WORKER_MODEL_OUTPUT: tokens={result.tokens_generated}")
"""
            pm.save_sandbox(sb)
            task = ScheduledTask(
                task_id="model-worker-task-01",
                name="model_inference_worker",
                trigger_type=TaskTriggerType.TIMER,
                trigger_spec="1.0",
                code=worker_code,
                sandbox_id=sb.sandbox_id,
            )
            daemon.register_task(task)
            pm.save_task(task)

            # Execute worker task inside sandbox
            exec_res = sb.execute(task.code)
            assert exec_res.exit_code == 0
            assert "WORKER_MODEL_OUTPUT: tokens=" in exec_res.stdout

            # Record execution history
            pm.record_task_execution(
                task.task_id,
                {
                    "exit_code": exec_res.exit_code,
                    "stdout": exec_res.stdout,
                    "stderr": exec_res.stderr,
                    "duration_ms": exec_res.duration_ms,
                },
            )

            # Verify history retrieved from persistence
            history = pm.get_task_history(task.task_id)
            assert len(history) >= 1
            assert history[0].exit_code == 0
            assert "WORKER_MODEL_OUTPUT:" in history[0].stdout
        finally:
            mgr.destroy_sandbox(sb.sandbox_id)
            pm.close()

    def test_cross_turn_variable_types_and_memory_cleanup(self, temp_storage_dir):
        """Validates heterogeneous variable type serialization, restoration, and runner memory release."""
        storage_cfg = StorageConfig(base_dir=str(temp_storage_dir))
        pm = PersistenceManager(storage_cfg)
        runner = LocalModelRunner.load("test-mem-runner", backend=ModelBackend.LIGHTWEIGHT)

        sb = LocalSandbox(sandbox_id="sb-mem-cleanup")
        try:
            code = """
import math
int_val = 100
float_val = 3.14159265
list_val = [1, 2, "three", {"nested": True}]
dict_val = {"alpha": 1, "beta": [10, 20, 30], "gamma": {"inner": 99}}
bytes_val = b"hello_antigravity_storage"
tuple_val = (10, 20, 30)
"""
            res = sb.execute(code, repl=True)
            assert res.exit_code == 0

            # Persist state
            record = pm.save_sandbox(sb)
            assert record.variable_count >= 5

            # Load and inspect manifest
            loaded_rec, loaded_vars = pm.load_sandbox(sb.sandbox_id)
            assert loaded_vars["int_val"] == 100
            assert abs(loaded_vars["float_val"] - 3.14159265) < 1e-6
            assert loaded_vars["list_val"][2] == "three"
            assert loaded_vars["dict_val"]["gamma"]["inner"] == 99
            assert loaded_vars["bytes_val"] == b"hello_antigravity_storage"
            assert tuple(loaded_vars["tuple_val"]) == (10, 20, 30)

            # Memory cleanup
            models_before = runner.list_loaded_models()
            assert any(m["model_id"] == "test-mem-runner" for m in models_before)

            unloaded = runner.unload_model("test-mem-runner")
            assert unloaded is True
            models_after = runner.list_loaded_models()
            assert not any(m["model_id"] == "test-mem-runner" for m in models_after)
        finally:
            sb.destroy()
            pm.close()
