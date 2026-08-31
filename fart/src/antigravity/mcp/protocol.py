"""
JSON-RPC 2.0 Protocol Implementation for Model Context Protocol (MCP).

Provides message parsing, serialization, error schemas, and stdio framing
ensuring JSON-RPC traffic is strictly routed to stdout while diagnostic
logging routes to stderr.
"""

from __future__ import annotations

import json
import logging
import sys
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Union

# Configure stderr logger for MCP protocol
logger = logging.getLogger("antigravity.mcp.protocol")


# ---------------------------------------------------------------------------
# Standard JSON-RPC 2.0 and MCP Domain Error Codes
# ---------------------------------------------------------------------------
PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603

# MCP Domain Specific Error Codes
SANDBOX_NOT_FOUND = -32000
EXECUTION_TIMEOUT = -32001
AST_SECURITY_VIOLATION = -32002
E2B_PROVIDER_ERROR = -32003
WORKER_SCHEDULE_ERROR = -32004
SNAPSHOT_CORRUPTED = -32005
TOOL_ERROR = -32006

# Model Inference Error Codes
MODEL_NOT_FOUND = -32010
MODEL_LOAD_ERROR = -32011
MODEL_INFERENCE_ERROR = -32012

# Persistence Error Codes
PERSISTENCE_NOT_FOUND = -32020
PERSISTENCE_WRITE_ERROR = -32021
PERSISTENCE_READ_ERROR = -32022

ERROR_MESSAGES = {
    PARSE_ERROR: "Parse error: Invalid JSON was received by the server.",
    INVALID_REQUEST: "Invalid Request: The JSON sent is not a valid Request object.",
    METHOD_NOT_FOUND: "Method not found: The method does not exist / is not available.",
    INVALID_PARAMS: "Invalid params: Invalid method parameter(s).",
    INTERNAL_ERROR: "Internal error: Internal JSON-RPC error.",
    SANDBOX_NOT_FOUND: "Sandbox not found or has been terminated.",
    EXECUTION_TIMEOUT: "Code execution timed out.",
    AST_SECURITY_VIOLATION: "Security violation: Code failed AST validation.",
    E2B_PROVIDER_ERROR: "E2B microVM provider encountered an error.",
    WORKER_SCHEDULE_ERROR: "Invalid worker trigger schedule specification.",
    SNAPSHOT_CORRUPTED: "Sandbox snapshot is corrupted or could not be loaded.",
    TOOL_ERROR: "Tool execution failed.",
    MODEL_NOT_FOUND: "Model not found or weights path does not exist.",
    MODEL_LOAD_ERROR: "Failed to load model weights or initialize engine.",
    MODEL_INFERENCE_ERROR: "Error during model token generation or inference.",
    PERSISTENCE_NOT_FOUND: "Persisted sandbox or snapshot not found in storage.",
    PERSISTENCE_WRITE_ERROR: "Failed to persist state or write to storage.",
    PERSISTENCE_READ_ERROR: "Failed to read or deserialize persisted state from disk.",
}


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------
class JsonRpcError(Exception):
    """Base exception for JSON-RPC 2.0 protocol and domain errors."""

    def __init__(self, code: int, message: Optional[str] = None, data: Optional[Any] = None) -> None:
        self.code = code
        self.message = message or ERROR_MESSAGES.get(code, "Unknown error")
        self.data = data
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {"code": self.code, "message": self.message}
        if self.data is not None:
            result["data"] = self.data
        return result


class ParseError(JsonRpcError):
    def __init__(self, message: Optional[str] = None, data: Optional[Any] = None) -> None:
        super().__init__(PARSE_ERROR, message or ERROR_MESSAGES[PARSE_ERROR], data)


class InvalidRequestError(JsonRpcError):
    def __init__(self, message: Optional[str] = None, data: Optional[Any] = None) -> None:
        super().__init__(INVALID_REQUEST, message or ERROR_MESSAGES[INVALID_REQUEST], data)


class MethodNotFoundError(JsonRpcError):
    def __init__(self, message: Optional[str] = None, data: Optional[Any] = None) -> None:
        super().__init__(METHOD_NOT_FOUND, message or ERROR_MESSAGES[METHOD_NOT_FOUND], data)


class InvalidParamsError(JsonRpcError):
    def __init__(self, message: Optional[str] = None, data: Optional[Any] = None) -> None:
        super().__init__(INVALID_PARAMS, message or ERROR_MESSAGES[INVALID_PARAMS], data)


class InternalError(JsonRpcError):
    def __init__(self, message: Optional[str] = None, data: Optional[Any] = None) -> None:
        super().__init__(INTERNAL_ERROR, message or ERROR_MESSAGES[INTERNAL_ERROR], data)


class ToolError(JsonRpcError):
    def __init__(self, message: Optional[str] = None, data: Optional[Any] = None) -> None:
        super().__init__(TOOL_ERROR, message or ERROR_MESSAGES[TOOL_ERROR], data)


class SandboxNotFoundError(JsonRpcError):
    def __init__(self, message: Optional[str] = None, data: Optional[Any] = None) -> None:
        super().__init__(SANDBOX_NOT_FOUND, message or ERROR_MESSAGES[SANDBOX_NOT_FOUND], data)


class ModelNotFoundError(JsonRpcError):
    def __init__(self, message: Optional[str] = None, data: Optional[Any] = None) -> None:
        super().__init__(MODEL_NOT_FOUND, message or ERROR_MESSAGES[MODEL_NOT_FOUND], data)


class ModelLoadError(JsonRpcError):
    def __init__(self, message: Optional[str] = None, data: Optional[Any] = None) -> None:
        super().__init__(MODEL_LOAD_ERROR, message or ERROR_MESSAGES[MODEL_LOAD_ERROR], data)


class ModelInferenceError(JsonRpcError):
    def __init__(self, message: Optional[str] = None, data: Optional[Any] = None) -> None:
        super().__init__(MODEL_INFERENCE_ERROR, message or ERROR_MESSAGES[MODEL_INFERENCE_ERROR], data)


class PersistenceNotFoundError(JsonRpcError):
    def __init__(self, message: Optional[str] = None, data: Optional[Any] = None) -> None:
        super().__init__(PERSISTENCE_NOT_FOUND, message or ERROR_MESSAGES[PERSISTENCE_NOT_FOUND], data)


class PersistenceWriteError(JsonRpcError):
    def __init__(self, message: Optional[str] = None, data: Optional[Any] = None) -> None:
        super().__init__(PERSISTENCE_WRITE_ERROR, message or ERROR_MESSAGES[PERSISTENCE_WRITE_ERROR], data)


class PersistenceReadError(JsonRpcError):
    def __init__(self, message: Optional[str] = None, data: Optional[Any] = None) -> None:
        super().__init__(PERSISTENCE_READ_ERROR, message or ERROR_MESSAGES[PERSISTENCE_READ_ERROR], data)


# ---------------------------------------------------------------------------
# Message Dataclasses
# ---------------------------------------------------------------------------
@dataclass
class JsonRpcRequest:
    """Represents a JSON-RPC 2.0 request."""
    method: str
    id: Optional[Union[str, int, float]] = None
    params: Optional[Dict[str, Any]] = None
    jsonrpc: str = "2.0"

    def is_notification(self) -> bool:
        return self.id is None


@dataclass
class JsonRpcNotification:
    """Represents a JSON-RPC 2.0 notification (no ID)."""
    method: str
    params: Optional[Dict[str, Any]] = None
    jsonrpc: str = "2.0"


@dataclass
class JsonRpcResponse:
    """Represents a JSON-RPC 2.0 response."""
    id: Optional[Union[str, int, float]]
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None
    jsonrpc: str = "2.0"

    def to_dict(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"jsonrpc": self.jsonrpc, "id": self.id}
        if self.error is not None:
            payload["error"] = self.error
        else:
            payload["result"] = self.result if self.result is not None else {}
        return payload


# ---------------------------------------------------------------------------
# Serialization & Message Framing Helpers
# ---------------------------------------------------------------------------
def parse_jsonrpc_message(raw_input: Union[str, bytes, Dict[str, Any]]) -> Dict[str, Any]:
    """
    Parse and validate a raw JSON-RPC 2.0 message string or dictionary.

    Raises:
        ParseError: If raw string cannot be parsed as valid JSON.
        InvalidRequestError: If parsed object lacks standard jsonrpc framing.
    """
    if isinstance(raw_input, (str, bytes)):
        try:
            payload = json.loads(raw_input)
        except Exception as e:
            raise ParseError(f"Malformed JSON: {e}") from e
    elif isinstance(raw_input, dict):
        payload = raw_input
    else:
        raise InvalidRequestError(f"Invalid message type: {type(raw_input).__name__}")

    if not isinstance(payload, dict):
        raise InvalidRequestError("Request payload must be a JSON object")

    if payload.get("jsonrpc") != "2.0":
        # Lenient handling: if missing jsonrpc field, default or raise depending on mode
        payload["jsonrpc"] = "2.0"

    return payload


def create_response(req_id: Optional[Union[str, int, float]], result: Any) -> Dict[str, Any]:
    """Construct a successful JSON-RPC 2.0 response dictionary."""
    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "result": result if result is not None else {},
    }


def create_error_response(
    req_id: Optional[Union[str, int, float]],
    code: int,
    message: Optional[str] = None,
    data: Optional[Any] = None,
) -> Dict[str, Any]:
    """Construct a JSON-RPC 2.0 error response dictionary."""
    err_dict: Dict[str, Any] = {
        "code": code,
        "message": message or ERROR_MESSAGES.get(code, "Error"),
    }
    if data is not None:
        err_dict["data"] = data

    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "error": err_dict,
    }


def create_notification(method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Construct a JSON-RPC 2.0 notification dictionary."""
    return {
        "jsonrpc": "2.0",
        "method": method,
        "params": params or {},
    }


def encode_message(payload: Dict[str, Any]) -> str:
    """Encode a dictionary to a newline-delimited JSON string for stdio framing."""
    return json.dumps(payload, ensure_ascii=False) + "\n"


def write_stdout(payload: Dict[str, Any]) -> None:
    """
    Write a JSON-RPC payload strictly to standard output and flush.
    Ensures no stray logging corrupts stdout.
    """
    line = encode_message(payload)
    sys.stdout.write(line)
    sys.stdout.flush()


def log_stderr(message: str, level: str = "INFO") -> None:
    """
    Write diagnostic or server log messages strictly to stderr and flush.
    """
    sys.stderr.write(f"[{level}] [Antigravity-MCP] {message}\n")
    sys.stderr.flush()
