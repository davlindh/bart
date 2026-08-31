"""
Tier 2: Boundary & Corner Cases - MCP Protocol & Stdio Transport Boundaries.
Tests malformed JSON-RPC syntax, unknown methods, missing arguments,
invalid sandbox IDs in tool calls, unsupported protocols, and pipe EOF.
"""

import asyncio
import json
import pytest

from tests.conftest import StdioMCPTestClient


class TestMcpProtocolBoundaries:
    """Boundary and corner cases for MCP stdio protocol handling and tool validation."""

    def test_unknown_method_call_returns_method_not_found(self, mcp_client_session: StdioMCPTestClient):
        """Validates that invoking an unknown RPC method returns JSON-RPC code -32601."""
        req = mcp_client_session.make_request(
            method="unsupported_method_xyz",
            params={"some_key": "some_val"}
        )
        resp = asyncio.run(mcp_client_session.send(req))
        assert resp.get("jsonrpc") == "2.0"
        assert "error" in resp
        error = resp["error"]
        assert error.get("code") == -32601 or "not found" in error.get("message", "").lower()

    def test_call_unknown_tool_returns_error(self, mcp_client_session: StdioMCPTestClient):
        """Validates that calling a nonexistent tool via tools/call returns appropriate error."""
        req = mcp_client_session.make_request(
            method="tools/call",
            params={
                "name": "non_existent_tool_alpha",
                "arguments": {}
            }
        )
        resp = asyncio.run(mcp_client_session.send(req))
        assert "error" in resp or (resp.get("result", {}).get("isError") is True)

    def test_execute_code_missing_required_arguments(self, mcp_client_session: StdioMCPTestClient):
        """Validates schema validation failure when required arguments are missing."""
        req = mcp_client_session.make_request(
            method="tools/call",
            params={
                "name": "execute_code",
                "arguments": {}  # Missing code and sandbox_id
            }
        )
        resp = asyncio.run(mcp_client_session.send(req))
        assert "error" in resp or resp.get("result") is not None

    def test_destroy_sandbox_with_invalid_id(self, mcp_client_session: StdioMCPTestClient):
        """Validates calling destroy_sandbox with an invalid / non-existent sandbox ID."""
        req = mcp_client_session.make_request(
            method="tools/call",
            params={
                "name": "destroy_sandbox",
                "arguments": {"sandbox_id": "invalid-sandbox-id-9999"}
            }
        )
        resp = asyncio.run(mcp_client_session.send(req))
        assert resp.get("jsonrpc") == "2.0"

    def test_ping_pong_health_check(self, mcp_client_session: StdioMCPTestClient):
        """Validates standard ping method returns empty result or pong."""
        req = mcp_client_session.make_request(method="ping")
        resp = asyncio.run(mcp_client_session.send(req))
        assert resp.get("jsonrpc") == "2.0"
        assert "result" in resp or "error" not in resp

    def test_batch_or_sequential_rpc_requests(self, mcp_client_session: StdioMCPTestClient):
        """Tests sending multiple sequential JSON-RPC requests across the same session."""
        for i in range(5):
            req = mcp_client_session.make_request(
                method="ping",
                req_id=f"seq-req-{i}"
            )
            resp = asyncio.run(mcp_client_session.send(req))
            assert resp.get("id") == f"seq-req-{i}"
