"""
Tier 1: Feature Coverage - Extended MCP Tools (6 New Tools - Requirement R4 / Milestone M7).
Verifies load_model, model_generate, model_chat, persist_sandbox, restore_sandbox_disk, list_persisted_sandboxes.
"""

import asyncio
import json
import pytest
from antigravity.mcp.tools import MCPToolRegistry
from antigravity.mcp.protocol import (
    MODEL_NOT_FOUND,
    MODEL_LOAD_ERROR,
    MODEL_INFERENCE_ERROR,
    PERSISTENCE_NOT_FOUND,
    PERSISTENCE_WRITE_ERROR,
    PERSISTENCE_READ_ERROR,
)
from antigravity.sandbox.manager import SandboxManager


class TestMCPExtendedTools:
    """Test suite verifying all 6 extended MCP tools registered in MCPToolRegistry."""

    def test_all_13_tools_registered(self):
        """Validates that MCPToolRegistry registers all 13 tools."""
        registry = MCPToolRegistry()
        tools_list = registry.list_tools()
        assert len(tools_list) == 13

        names = {t["name"] for t in tools_list}
        expected = {
            "create_sandbox",
            "execute_code",
            "pause_sandbox",
            "resume_sandbox",
            "destroy_sandbox",
            "manage_snapshot",
            "spawn_worker",
            "load_model",
            "model_generate",
            "model_chat",
            "persist_sandbox",
            "restore_sandbox_disk",
            "list_persisted_sandboxes",
        }
        assert expected.issubset(names)

    def test_load_model_tool(self):
        """Validates load_model tool execution."""
        async def _run():
            registry = MCPToolRegistry()
            res = await registry.call_tool(
                "load_model",
                {
                    "model_path": "nvidia/Nemotron-Mini-4B-Instruct",
                    "model_id": "test-nemotron",
                    "model_format": "nemotron",
                    "device": "cpu",
                    "precision": "fp16",
                },
            )
            assert res["isError"] is False
            parsed = json.loads(res["content"][0]["text"])
            assert parsed["model_id"] == "test-nemotron"
            assert parsed["status"] == "loaded"

        asyncio.run(_run())

    def test_model_generate_tool(self):
        """Validates model_generate tool execution."""
        async def _run():
            registry = MCPToolRegistry()
            # First load model
            await registry.call_tool(
                "load_model",
                {
                    "model_path": "nvidia/Nemotron-Mini-4B-Instruct",
                    "model_id": "test-gen-model",
                },
            )
            res = await registry.call_tool(
                "model_generate",
                {
                    "model_id": "test-gen-model",
                    "prompt": "Hello AI",
                    "max_new_tokens": 10,
                    "temperature": 0.5,
                },
            )
            assert res["isError"] is False
            parsed = json.loads(res["content"][0]["text"])
            assert parsed["model_id"] == "test-gen-model"
            assert "text" in parsed
            assert parsed["tokens_generated"] > 0

        asyncio.run(_run())

    def test_model_chat_tool(self):
        """Validates model_chat tool execution."""
        async def _run():
            registry = MCPToolRegistry()
            await registry.call_tool(
                "load_model",
                {
                    "model_path": "nvidia/Nemotron-Mini-4B-Instruct",
                    "model_id": "test-chat-model",
                },
            )
            res = await registry.call_tool(
                "model_chat",
                {
                    "model_id": "test-chat-model",
                    "messages": [
                        {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user", "content": "What is 2+2?"},
                    ],
                    "chat_template": "nemotron",
                    "max_new_tokens": 15,
                },
            )
            assert res["isError"] is False
            parsed = json.loads(res["content"][0]["text"])
            assert parsed["model_id"] == "test-chat-model"
            assert "message" in parsed
            assert parsed["message"]["role"] == "assistant"
            assert len(parsed["message"]["content"]) > 0

        asyncio.run(_run())

    def test_persistence_roundtrip_tools(self, tmp_path):
        """Validates persist_sandbox, list_persisted_sandboxes, and restore_sandbox_disk tools."""
        async def _run():
            storage_dir = str(tmp_path / "test_storage")
            manager = SandboxManager()
            registry = MCPToolRegistry(sandbox_manager=manager)

            # 1. Create sandbox and execute code
            create_res = await registry.call_tool("create_sandbox", {"mode": "local"})
            assert create_res["isError"] is False
            sb_id = json.loads(create_res["content"][0]["text"])["sandbox_id"]

            exec_res = await registry.call_tool(
                "execute_code",
                {
                    "sandbox_id": sb_id,
                    "code": "x = 42\ny = 'persistent_data'\nz = [1, 2, 3]",
                    "repl": True,
                },
            )
            assert exec_res["isError"] is False

            # 2. Persist sandbox
            persist_res = await registry.call_tool(
                "persist_sandbox",
                {
                    "sandbox_id": sb_id,
                    "storage_path": storage_dir,
                    "name": "My Persisted Session",
                    "description": "Session with variables x, y, z",
                },
            )
            assert persist_res["isError"] is False
            persist_data = json.loads(persist_res["content"][0]["text"])
            assert persist_data["status"] == "persisted"
            assert persist_data["variable_count"] >= 3

            # 3. List persisted sandboxes
            list_res = await registry.call_tool(
                "list_persisted_sandboxes",
                {
                    "storage_path": storage_dir,
                    "filter_name": "Session",
                },
            )
            assert list_res["isError"] is False
            list_data = json.loads(list_res["content"][0]["text"])
            assert list_data["total_count"] >= 1
            assert any(s["sandbox_id"] == sb_id for s in list_data["sandboxes"])

            # 4. Destroy active sandbox
            await registry.call_tool("destroy_sandbox", {"sandbox_id": sb_id})

            # 5. Restore sandbox from disk in fresh manager / registry
            fresh_manager = SandboxManager()
            fresh_registry = MCPToolRegistry(sandbox_manager=fresh_manager)

            restore_res = await fresh_registry.call_tool(
                "restore_sandbox_disk",
                {
                    "persisted_id": sb_id,
                    "storage_path": storage_dir,
                    "restore_variables": True,
                },
            )
            assert restore_res["isError"] is False
            restore_data = json.loads(restore_res["content"][0]["text"])
            restored_sb_id = restore_data["sandbox_id"]

            # 6. Execute code on restored sandbox to verify variables are rehydrated
            verify_res = await fresh_registry.call_tool(
                "execute_code",
                {
                    "sandbox_id": restored_sb_id,
                    "code": "print(f'VAL_X={x}, VAL_Y={y}, VAL_Z={z}')",
                    "repl": True,
                },
            )
            assert verify_res["isError"] is False
            verify_data = json.loads(verify_res["content"][0]["text"])
            assert "VAL_X=42" in verify_data["stdout"]
            assert "VAL_Y=persistent_data" in verify_data["stdout"]

        asyncio.run(_run())
