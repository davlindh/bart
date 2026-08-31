"""
Antigravity MCP Server: Async Stdio JSON-RPC 2.0 Server.

Processes Model Context Protocol (MCP) lifecycle handshakes, tool catalogs,
and tool calls while enforcing stdio isolation (stdout for JSON-RPC, stderr for logs).
"""

from __future__ import annotations

import asyncio
import json
import logging
import sys
from typing import Any, Dict, Optional, Union

from antigravity.sandbox.manager import SandboxManager

from .protocol import (
    INTERNAL_ERROR,
    INVALID_PARAMS,
    INVALID_REQUEST,
    METHOD_NOT_FOUND,
    PARSE_ERROR,
    InvalidParamsError,
    InvalidRequestError,
    JsonRpcError,
    MethodNotFoundError,
    ParseError,
    create_error_response,
    create_notification,
    create_response,
    encode_message,
    log_stderr,
    parse_jsonrpc_message,
    write_stdout,
)
from .schemas import (
    InitializeParams,
    InitializeResult,
    ServerCapabilities,
    ServerInfo,
    ToolCallParams,
)
from .tools import MCPToolRegistry, ServiceWorkerDaemon

logger = logging.getLogger("antigravity.mcp.server")


class AntigravityMCPServer:
    """
    Model Context Protocol (MCP) server managing execution sandboxes and
    scheduled background workers over JSON-RPC 2.0 stdio transport.
    """

    def __init__(
        self,
        sandbox_manager: Optional[SandboxManager] = None,
        scheduler_daemon: Optional[ServiceWorkerDaemon] = None,
        tool_registry: Optional[MCPToolRegistry] = None,
    ) -> None:
        self.sandbox_manager = sandbox_manager or SandboxManager()
        self.scheduler_daemon = scheduler_daemon or ServiceWorkerDaemon(sandbox_manager=self.sandbox_manager)
        self.tool_registry = tool_registry or MCPToolRegistry(
            sandbox_manager=self.sandbox_manager,
            scheduler_daemon=self.scheduler_daemon,
        )
        self._initialized = False
        self._client_info: Optional[Dict[str, Any]] = None
        self._running = False

    async def handle_request_async(self, request_payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Process a parsed JSON-RPC request dictionary asynchronously and return
        the JSON-RPC response dictionary, or None if the request was a notification.
        """
        if not isinstance(request_payload, dict):
            return create_error_response(None, INVALID_REQUEST, "Payload must be a JSON object")

        req_id = request_payload.get("id")
        method = request_payload.get("method")
        params = request_payload.get("params", {}) or {}

        if not method or not isinstance(method, str):
            if req_id is not None:
                return create_error_response(req_id, INVALID_REQUEST, "Missing or invalid 'method' field")
            return None

        # Handle notifications (requests without 'id')
        is_notification = req_id is None

        try:
            # ---------------------------------------------------------------
            # 1. MCP Lifecycle: initialize
            # ---------------------------------------------------------------
            if method == "initialize":
                try:
                    init_params = InitializeParams(**params)
                    self._client_info = init_params.clientInfo.model_dump() if init_params.clientInfo else {}
                except Exception:
                    self._client_info = params.get("clientInfo", {})

                result = {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {"listChanged": True},
                        "logging": {},
                        "resources": {"subscribe": True, "listChanged": True},
                    },
                    "serverInfo": {
                        "name": "antigravity-sandbox-mcp",
                        "version": "1.0.0",
                    },
                }
                self._initialized = True
                log_stderr("Client initialized connection.", level="INFO")
                return create_response(req_id, result)

            # ---------------------------------------------------------------
            # 2. MCP Lifecycle: notifications/initialized
            # ---------------------------------------------------------------
            elif method == "notifications/initialized":
                self._initialized = True
                log_stderr("Client sent initialized confirmation.", level="INFO")
                if is_notification:
                    return None
                return create_response(req_id, {})

            # ---------------------------------------------------------------
            # 3. MCP Diagnostic: ping
            # ---------------------------------------------------------------
            elif method == "ping":
                return create_response(req_id, {})

            # ---------------------------------------------------------------
            # 4. MCP Tools: tools/list
            # ---------------------------------------------------------------
            elif method == "tools/list":
                tools_catalog = self.tool_registry.list_tools()
                return create_response(req_id, {"tools": tools_catalog})

            # ---------------------------------------------------------------
            # 5. MCP Tools: tools/call
            # ---------------------------------------------------------------
            elif method == "tools/call":
                tool_name = params.get("name")
                tool_args = params.get("arguments", {})

                if not tool_name:
                    if is_notification:
                        return None
                    return create_error_response(req_id, INVALID_PARAMS, "Missing 'name' in tools/call")

                if not self.tool_registry.has_tool(tool_name):
                    if is_notification:
                        return None
                    return create_error_response(req_id, METHOD_NOT_FOUND, f"Unknown tool: '{tool_name}'")

                tool_result = await self.tool_registry.call_tool(tool_name, tool_args)
                return create_response(req_id, tool_result)

            # ---------------------------------------------------------------
            # 6. Unknown RPC Method
            # ---------------------------------------------------------------
            else:
                log_stderr(f"Unknown JSON-RPC method: {method}", level="WARNING")
                if is_notification:
                    return None
                return create_error_response(req_id, METHOD_NOT_FOUND, f"Method not found: '{method}'")

        except JsonRpcError as j_err:
            if is_notification:
                return None
            return create_error_response(req_id, j_err.code, j_err.message, j_err.data)
        except Exception as exc:
            log_stderr(f"Unhandled server error handling '{method}': {exc}", level="ERROR")
            if is_notification:
                return None
            return create_error_response(req_id, INTERNAL_ERROR, f"Internal server error: {exc}")

    def handle_request(self, request_payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Synchronous wrapper for handle_request_async."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # In nested event loop, create a new loop in worker thread or run directly
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                    return pool.submit(asyncio.run, self.handle_request_async(request_payload)).result()
            return loop.run_until_complete(self.handle_request_async(request_payload))
        except Exception:
            return asyncio.run(self.handle_request_async(request_payload))

    async def dispatch(self, request_payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Alias for handle_request_async for compatibility."""
        return await self.handle_request_async(request_payload)

    async def run_stdio(self) -> None:
        """
        Main Stdio Message Processing Loop.
        Reads JSON-RPC lines from sys.stdin, dispatches them, and writes
        responses strictly to sys.stdout while flushing.
        """
        self._running = True
        log_stderr("Antigravity MCP Server started on stdio transport.", level="INFO")
        loop = asyncio.get_running_loop()

        while self._running:
            try:
                # Read line asynchronously in thread pool to avoid blocking event loop
                line = await loop.run_in_executor(None, sys.stdin.readline)
                if not line:
                    # EOF reached
                    log_stderr("Received EOF on stdin. Shutting down MCP server.", level="INFO")
                    break

                line = line.strip()
                if not line:
                    continue

                # Parse JSON-RPC message
                try:
                    payload = parse_jsonrpc_message(line)
                except ParseError as p_err:
                    write_stdout(create_error_response(None, PARSE_ERROR, p_err.message))
                    continue
                except InvalidRequestError as i_err:
                    write_stdout(create_error_response(None, INVALID_REQUEST, i_err.message))
                    continue

                response = await self.handle_request_async(payload)
                if response is not None:
                    write_stdout(response)

            except asyncio.CancelledError:
                break
            except Exception as e:
                log_stderr(f"Fatal loop error: {e}", level="ERROR")
                write_stdout(create_error_response(None, INTERNAL_ERROR, str(e)))

        self._running = False
        log_stderr("Antigravity MCP Server terminated cleanly.", level="INFO")
