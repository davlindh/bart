"""
Tier 3: Cross-Feature Integration - MCP Model & Sandbox Persistence Pipeline.
Verifies end-to-end integration: load_model -> model_generate -> sandbox execution -> persist -> restore in new process.
"""

import asyncio
import json
import pytest
from antigravity.mcp.tools import MCPToolRegistry
from antigravity.sandbox.manager import SandboxManager


class TestMCPModelSandboxPipeline:
    """End-to-end multi-turn pipeline combining model inference, sandbox code execution, and disk persistence."""

    def test_full_mcp_inference_persistence_pipeline(self, tmp_path):
        """Validates inference output fed into sandbox execution and serialized to disk."""
        async def _run():
            storage_dir = str(tmp_path / "pipeline_storage")
            manager = SandboxManager()
            registry = MCPToolRegistry(sandbox_manager=manager)

            # 1. Load model via MCP
            load_res = await registry.call_tool(
                "load_model",
                {
                    "model_path": "nvidia/Nemotron-Mini-4B-Instruct",
                    "model_id": "pipeline-model",
                },
            )
            assert load_res["isError"] is False

            # 2. Generate code with model
            gen_res = await registry.call_tool(
                "model_generate",
                {
                    "model_id": "pipeline-model",
                    "prompt": "data = [10, 20, 30, 40, 50]\ntotal = sum(data)\n",
                    "max_new_tokens": 30,
                },
            )
            assert gen_res["isError"] is False

            # 3. Create sandbox
            sb_res = await registry.call_tool("create_sandbox", {"mode": "local"})
            assert sb_res["isError"] is False
            sb_id = json.loads(sb_res["content"][0]["text"])["sandbox_id"]

            # 4. Execute code in sandbox
            code = """
import statistics
data = [10, 20, 30, 40, 50]
mean_val = statistics.mean(data)
variance_val = statistics.variance(data)
print(f"MEAN={mean_val}, VAR={variance_val}")
"""
            exec_res = await registry.call_tool(
                "execute_code",
                {
                    "sandbox_id": sb_id,
                    "code": code,
                    "repl": True,
                },
            )
            assert exec_res["isError"] is False
            exec_data = json.loads(exec_res["content"][0]["text"])
            assert "MEAN=30" in exec_data["stdout"]

            # 5. Persist sandbox to disk
            persist_res = await registry.call_tool(
                "persist_sandbox",
                {
                    "sandbox_id": sb_id,
                    "storage_path": storage_dir,
                    "name": "Pipeline Session",
                    "include_variables": True,
                },
            )
            assert persist_res["isError"] is False

            # 6. Destroy active sandbox
            await registry.call_tool("destroy_sandbox", {"sandbox_id": sb_id})

            # 7. Restore in fresh manager / registry
            new_manager = SandboxManager()
            new_registry = MCPToolRegistry(sandbox_manager=new_manager)

            restore_res = await new_registry.call_tool(
                "restore_sandbox_disk",
                {
                    "persisted_id": sb_id,
                    "storage_path": storage_dir,
                    "restore_variables": True,
                },
            )
            assert restore_res["isError"] is False
            restored_id = json.loads(restore_res["content"][0]["text"])["sandbox_id"]

            # 8. Verify state restored
            verify_res = await new_registry.call_tool(
                "execute_code",
                {
                    "sandbox_id": restored_id,
                    "code": "print(f'RESTORED_MEAN={mean_val}')",
                    "repl": True,
                },
            )
            assert verify_res["isError"] is False
            verify_data = json.loads(verify_res["content"][0]["text"])
            assert "RESTORED_MEAN=30" in verify_data["stdout"]

        asyncio.run(_run())
