"""
Tests for Disk-Backed Local Persistence and Real Local Model Inference (NVIDIA Nemotron / NeMo).
"""

import os
import tempfile
import pytest

from antigravity.storage.disk_store import DiskStateStore, PersistenceManager
from antigravity.models.runner import LocalModelRunner, NemotronEngine, ModelConfig
from antigravity.sandbox.local_sandbox import LocalSandbox
from antigravity.mcp.tools import MCPToolRegistry


class TestLocalPersistenceAndModels:
    """Test suite for Disk Persistence and Local Model Execution."""

    def test_disk_state_store_lifecycle(self):
        """Verify SQLite database storage of sandboxes, snapshots, and tasks."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_file = os.path.join(temp_dir, "test_store.db")
            store = DiskStateStore(db_path=db_file)

            # 1. Save and load sandbox
            store.save_sandbox(
                sandbox_id="sb-test-101",
                mode="local",
                status="running",
                state_dict={"counter": 42, "msg": "Hello Antigravity"},
                metadata={"name": "test_sandbox"},
            )

            sb_data = store.load_sandbox("sb-test-101")
            assert sb_data is not None
            assert sb_data["sandbox_id"] == "sb-test-101"
            assert sb_data["state"]["counter"] == 42
            assert sb_data["metadata"]["name"] == "test_sandbox"

            # 2. Save and list snapshots
            store.save_snapshot(
                snapshot_id="snap-101",
                sandbox_id="sb-test-101",
                name="checkpoint_alpha",
                state_dict={"counter": 42},
            )

            snaps = store.list_snapshots(sandbox_id="sb-test-101")
            assert len(snaps) == 1
            assert snaps[0]["snapshot_id"] == "snap-101"

            snap_data = store.load_snapshot("snap-101")
            assert snap_data is not None
            assert snap_data["state"]["counter"] == 42

            # 3. Delete sandbox
            deleted = store.delete_sandbox("sb-test-101")
            assert deleted is True
            assert store.load_sandbox("sb-test-101") is None

    def test_nemotron_engine_and_model_runner(self):
        """Verify real LocalModelRunner and NemotronEngine execution."""
        runner = NemotronEngine(
            model_name_or_path="nvidia/Nemotron-Mini-4B-Instruct",
            device="cpu",
        )
        assert runner.is_loaded is False

        # Load model
        loaded = runner.load_model()
        assert loaded is True
        assert runner.is_loaded is True

        # Generate text
        res = runner.generate("Explain microVM security in 2 sentences.", max_new_tokens=50)
        assert res.text is not None
        assert len(res.text) > 0
        assert res.tokens_generated > 0

        # Chat Nemotron formatting
        messages = [
            {"role": "system", "content": "You are an AI developer assistant."},
            {"role": "user", "content": "Write a Python function to compute fibonacci."},
        ]
        prompt_formatted = runner.format_nemotron_prompt(messages)
        assert "<extra_id_0>System" in prompt_formatted
        assert "<extra_id_1>User" in prompt_formatted

        chat_res = runner.chat_nemotron(messages, max_new_tokens=60)
        assert chat_res.text is not None
        assert chat_res.tokens_generated > 0

        runner.unload()
        assert runner.is_loaded is False

    def test_local_sandbox_disk_persistence_roundtrip(self):
        """Verify LocalSandbox persist_to_disk and restore_from_disk roundtrip."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_file = os.path.join(temp_dir, "sandbox_persist.db")
            
            # Create sandbox and execute code
            sb1 = LocalSandbox(auto_start=True)
            sb1_id = sb1.sandbox_id
            try:
                res1 = sb1.execute("alpha = 777\nbeta = [1, 2, 3]")
                assert res1.is_success

                snap_id = sb1.create_snapshot("checkpoint_beta")
                assert snap_id is not None

                # Persist to disk
                persisted_id = sb1.persist_to_disk(storage_path=db_file, name="saved_session")
                assert persisted_id == sb1_id
            finally:
                sb1.terminate()

            # Restore into a fresh LocalSandbox instance
            sb2 = LocalSandbox(sandbox_id=sb1_id, auto_start=True)
            try:
                restored = sb2.restore_from_disk(storage_path=db_file)
                assert restored is True

                res2 = sb2.execute("alpha + sum(beta)")
                assert res2.is_success
                assert res2.result == "783"  # 777 + 6
            finally:
                sb2.terminate()

    def test_mcp_tools_model_and_persistence(self):
        """Verify MCP tools for local model generation and disk persistence."""
        import asyncio
        async def _run():
            registry = MCPToolRegistry()

            # 1. Load model via MCP
            load_res = await registry.call_tool("load_model", {
                "model_path": "nvidia/Nemotron-Mini-4B-Instruct",
                "model_id": "test-nemotron-01",
                "device": "cpu",
            })
            assert load_res["isError"] is False

            # 2. Model Generate via MCP
            gen_res = await registry.call_tool("model_generate", {
                "model_id": "test-nemotron-01",
                "prompt": "What is Firecracker microVM?",
                "max_new_tokens": 30,
            })
            assert gen_res["isError"] is False

            # 3. Model Chat via MCP
            chat_res = await registry.call_tool("model_chat", {
                "model_id": "test-nemotron-01",
                "messages": [
                    {"role": "user", "content": "How do AI agent sandboxes work?"}
                ],
                "max_new_tokens": 30,
            })
            assert chat_res["isError"] is False

            # 4. Create sandbox & persist via MCP
            sb_res = await registry.call_tool("create_sandbox", {"mode": "local"})
            import json
            sb_info = json.loads(sb_res["content"][0]["text"])
            sb_id = sb_info["sandbox_id"]

            try:
                await registry.call_tool("execute_code", {
                    "sandbox_id": sb_id,
                    "code": "persistent_val = 999",
                })

                persist_res = await registry.call_tool("persist_sandbox", {
                    "sandbox_id": sb_id,
                    "name": "mcp_persisted_session",
                })
                assert persist_res["isError"] is False

                list_res = await registry.call_tool("list_persisted_sandboxes", {})
                assert list_res["isError"] is False
            finally:
                registry.sandbox_manager.destroy_sandbox(sb_id)

        asyncio.run(_run())
