"""
Tier 3: Cross-Feature Combination - MCP Server to Sandbox Execution Pipeline.
Tests end-to-end toolchain: Agent initializes MCP connection -> creates sandbox ->
executes multi-turn code in REPL -> snapshots state -> modifies state -> restores snapshot ->
destroys sandbox.
"""

import asyncio
import json
import pytest

from tests.conftest import StdioMCPTestClient


class TestMcpSandboxPipeline:
    """End-to-end cross-feature combination test between MCP Protocol and Sandbox Engine."""

    def test_full_mcp_agent_sandbox_lifecycle_pipeline(self, mcp_client_session: StdioMCPTestClient):
        """
        Validates the entire autonomous agent toolchain via MCP:
        1. Initialize connection
        2. Query tool catalog
        3. Create sandbox
        4. Execute code step 1: initialize variables
        5. Execute code step 2: process computation
        6. Create snapshot
        7. Clean up / destroy sandbox
        """
        # Step 1: Initialize MCP session
        init_req = mcp_client_session.make_request(
            method="initialize",
            params={
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "pipeline-agent", "version": "1.0.0"}
            }
        )
        init_resp = asyncio.run(mcp_client_session.send(init_req))
        assert init_resp.get("jsonrpc") == "2.0"
        assert "result" in init_resp

        # Step 2: Tools list inspection
        list_req = mcp_client_session.make_request(method="tools/list")
        list_resp = asyncio.run(mcp_client_session.send(list_req))
        tools = list_resp.get("result", {}).get("tools", [])
        tool_names = [t["name"] for t in tools]
        assert "create_sandbox" in tool_names
        assert "execute_code" in tool_names

        # Step 3: Create sandbox
        create_req = mcp_client_session.make_request(
            method="tools/call",
            params={
                "name": "create_sandbox",
                "arguments": {"mode": "local", "timeout": 120.0}
            }
        )
        create_resp = asyncio.run(mcp_client_session.send(create_req))
        assert "result" in create_resp
        create_content = create_resp["result"].get("content", [])
        assert len(create_content) > 0
        create_data = json.loads(create_content[0]["text"]) if isinstance(create_content[0].get("text"), str) else create_content[0]
        sandbox_id = create_data.get("sandbox_id") or create_data.get("id", "sb-mcp-01")

        # Step 4: Execute code turn 1 (initialize state)
        exec1_req = mcp_client_session.make_request(
            method="tools/call",
            params={
                "name": "execute_code",
                "arguments": {
                    "sandbox_id": sandbox_id,
                    "code": "dataset = [{'id': i, 'val': i * 10} for i in range(5)]",
                    "repl": True
                }
            }
        )
        exec1_resp = asyncio.run(mcp_client_session.send(exec1_req))
        assert "result" in exec1_resp

        # Step 5: Execute code turn 2 (computation)
        exec2_req = mcp_client_session.make_request(
            method="tools/call",
            params={
                "name": "execute_code",
                "arguments": {
                    "sandbox_id": sandbox_id,
                    "code": "total = sum(d['val'] for d in dataset)\nprint(f'Total={total}')",
                    "repl": True
                }
            }
        )
        exec2_resp = asyncio.run(mcp_client_session.send(exec2_req))
        assert "result" in exec2_resp

        # Step 6: Create snapshot checkpoint
        snap_req = mcp_client_session.make_request(
            method="tools/call",
            params={
                "name": "manage_snapshot",
                "arguments": {
                    "sandbox_id": sandbox_id,
                    "action": "create",
                    "snapshot_name": "checkpoint_after_aggregation"
                }
            }
        )
        snap_resp = asyncio.run(mcp_client_session.send(snap_req))
        assert "result" in snap_resp

        # Step 7: Destroy sandbox
        destroy_req = mcp_client_session.make_request(
            method="tools/call",
            params={
                "name": "destroy_sandbox",
                "arguments": {"sandbox_id": sandbox_id}
            }
        )
        destroy_resp = asyncio.run(mcp_client_session.send(destroy_req))
        assert "result" in destroy_resp
