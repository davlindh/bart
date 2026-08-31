"""
Tier 1: Feature Coverage - Antigravity MCP Server & JSON-RPC Protocol.
Verifies MCP initialize handshake, tool listing catalog (7 required tools),
and tool execution dispatches (create_sandbox, execute_code, manage_snapshot, spawn_worker, destroy_sandbox).
"""

import asyncio
import json
import pytest

from tests.conftest import StdioMCPTestClient


class TestMcpFeatures:
    """Feature test suite for Model Context Protocol (MCP) Server (Requirement R2)."""

    def test_mcp_initialize_handshake(self, mcp_client_session: StdioMCPTestClient):
        """Tests standard JSON-RPC 2.0 initialize request, verifying server capabilities and info."""
        req = mcp_client_session.make_request(
            method="initialize",
            params={
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-agent-client", "version": "1.0.0"}
            }
        )
        resp = asyncio.run(mcp_client_session.send(req))

        assert resp.get("jsonrpc") == "2.0"
        assert resp.get("id") == req["id"]
        assert "result" in resp
        result = resp["result"]
        assert "serverInfo" in result
        assert "tools" in result.get("capabilities", {})

    def test_mcp_tools_list_exposes_all_required_tools(self, mcp_client_session: StdioMCPTestClient):
        """Tests that `tools/list` returns the catalog of all 7 lifecycle, execution, snapshot, and worker tools."""
        req = mcp_client_session.make_request(method="tools/list")
        resp = asyncio.run(mcp_client_session.send(req))

        assert "result" in resp
        tools = resp["result"].get("tools", [])
        tool_names = {t["name"] for t in tools}

        expected_tools = {
            "create_sandbox",
            "execute_code",
            "pause_sandbox",
            "resume_sandbox",
            "destroy_sandbox",
            "manage_snapshot",
            "spawn_worker"
        }
        for expected in expected_tools:
            assert expected in tool_names, f"Expected tool '{expected}' missing from tools/list catalog"

        # Verify each tool has an inputSchema definition
        for tool in tools:
            assert "description" in tool
            assert "inputSchema" in tool
            assert isinstance(tool["inputSchema"], dict)

    def test_mcp_create_and_destroy_sandbox_tools(self, mcp_client_session: StdioMCPTestClient):
        """Tests calling `create_sandbox` followed by `destroy_sandbox` via MCP tools/call."""
        # 1. Create sandbox
        create_req = mcp_client_session.make_request(
            method="tools/call",
            params={
                "name": "create_sandbox",
                "arguments": {"mode": "local", "timeout": 120.0}
            }
        )
        create_resp = asyncio.run(mcp_client_session.send(create_req))
        assert "result" in create_resp
        content = create_resp["result"].get("content", [])
        assert len(content) > 0
        text_payload = json.loads(content[0]["text"]) if isinstance(content[0].get("text"), str) else content[0]
        assert "sandbox_id" in text_payload or "id" in text_payload

        sandbox_id = text_payload.get("sandbox_id") or text_payload.get("id", "sb-mcp-01")

        # 2. Destroy sandbox
        destroy_req = mcp_client_session.make_request(
            method="tools/call",
            params={
                "name": "destroy_sandbox",
                "arguments": {"sandbox_id": sandbox_id}
            }
        )
        destroy_resp = asyncio.run(mcp_client_session.send(destroy_req))
        assert "result" in destroy_resp
        destroy_content = destroy_resp["result"].get("content", [])
        assert len(destroy_content) > 0

    def test_mcp_execute_code_tool_call(self, mcp_client_session: StdioMCPTestClient):
        """Tests calling `execute_code` through MCP protocol and receiving structured output."""
        exec_req = mcp_client_session.make_request(
            method="tools/call",
            params={
                "name": "execute_code",
                "arguments": {
                    "sandbox_id": "test-sb-01",
                    "code": "print('MCP tool execution test output')",
                    "repl": True
                }
            }
        )
        resp = asyncio.run(mcp_client_session.send(exec_req))
        assert "result" in resp
        content = resp["result"].get("content", [])
        assert len(content) > 0
        payload = json.loads(content[0]["text"]) if isinstance(content[0].get("text"), str) else content[0]
        assert "stdout" in payload or "text" in payload or "exit_code" in payload

    def test_mcp_manage_snapshot_tool_call(self, mcp_client_session: StdioMCPTestClient):
        """Tests calling `manage_snapshot` to create state checkpoints."""
        snap_req = mcp_client_session.make_request(
            method="tools/call",
            params={
                "name": "manage_snapshot",
                "arguments": {
                    "sandbox_id": "test-sb-01",
                    "action": "create",
                    "snapshot_name": "agent_checkpoint_1"
                }
            }
        )
        resp = asyncio.run(mcp_client_session.send(snap_req))
        assert "result" in resp
        content = resp["result"].get("content", [])
        assert len(content) > 0

    def test_mcp_spawn_worker_tool_call(self, mcp_client_session: StdioMCPTestClient):
        """Tests calling `spawn_worker` to register a scheduled background task."""
        worker_req = mcp_client_session.make_request(
            method="tools/call",
            params={
                "name": "spawn_worker",
                "arguments": {
                    "name": "mcp_heartbeat_worker",
                    "trigger_type": "timer",
                    "trigger_spec": "10.0",
                    "code": "print('worker tick')"
                }
            }
        )
        resp = asyncio.run(mcp_client_session.send(worker_req))
        assert "result" in resp
        content = resp["result"].get("content", [])
        assert len(content) > 0
        payload = json.loads(content[0]["text"]) if isinstance(content[0].get("text"), str) else content[0]
        assert "task_id" in payload or "status" in payload
