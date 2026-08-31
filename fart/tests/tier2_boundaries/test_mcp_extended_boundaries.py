"""
Tier 2: Boundary & Edge Case Testing - Extended MCP Tools.
Verifies error handling, invalid parameters, missing files, non-existent persistence IDs.
"""

import asyncio
import json
import pytest
from antigravity.mcp.tools import MCPToolRegistry
from antigravity.mcp.protocol import (
    MODEL_NOT_FOUND,
    PERSISTENCE_NOT_FOUND,
    INVALID_PARAMS,
)
from antigravity.sandbox.manager import SandboxManager


class TestMCPExtendedBoundaries:
    """Boundary testing for 6 extended MCP tools."""

    def test_load_model_missing_file(self):
        """Tests load_model with a nonexistent local path."""
        async def _run():
            registry = MCPToolRegistry()
            res = await registry.call_tool(
                "load_model",
                {
                    "model_path": "/nonexistent/path/to/weights_never_exists",
                    "model_id": "missing-model",
                    "model_format": "transformers",
                },
            )
            # Either error or gracefully handled with error payload
            assert res["isError"] is True
            parsed = json.loads(res["content"][0]["text"])
            assert "error" in parsed or "is_error" in parsed

        asyncio.run(_run())

    def test_model_generate_invalid_args(self):
        """Tests model_generate with missing required prompt."""
        async def _run():
            registry = MCPToolRegistry()
            res = await registry.call_tool(
                "model_generate",
                {
                    "model_id": "test-model",
                    # missing prompt
                },
            )
            assert res["isError"] is True

        asyncio.run(_run())

    def test_model_chat_empty_messages(self):
        """Tests model_chat with empty messages list."""
        async def _run():
            registry = MCPToolRegistry()
            res = await registry.call_tool(
                "model_chat",
                {
                    "model_id": "test-model",
                    "messages": [],
                },
            )
            assert res["isError"] is True

        asyncio.run(_run())

    def test_persist_sandbox_nonexistent_sandbox(self):
        """Tests persist_sandbox on an invalid sandbox ID."""
        async def _run():
            registry = MCPToolRegistry()
            res = await registry.call_tool(
                "persist_sandbox",
                {
                    "sandbox_id": "sb-never-existed-12345",
                },
            )
            assert res["isError"] is True

        asyncio.run(_run())

    def test_restore_sandbox_disk_missing_record(self, tmp_path):
        """Tests restore_sandbox_disk with non-existent persisted ID."""
        async def _run():
            storage_dir = str(tmp_path / "empty_storage")
            registry = MCPToolRegistry()
            res = await registry.call_tool(
                "restore_sandbox_disk",
                {
                    "persisted_id": "persisted-nonexistent-id",
                    "storage_path": storage_dir,
                },
            )
            assert res["isError"] is True
            parsed = json.loads(res["content"][0]["text"])
            assert "error" in parsed

        asyncio.run(_run())
