"""
CLI Runner and Main Entry Point for Antigravity MCP Server.

Provides entry point `antigravity-mcp-server` and async execution helpers.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path

# Ensure src directory is in sys.path when runner is launched directly
_SRC_DIR = str(Path(__file__).resolve().parent.parent.parent)
while _SRC_DIR in sys.path:
    sys.path.remove(_SRC_DIR)
sys.path.insert(0, _SRC_DIR)
if "antigravity" in sys.modules and not hasattr(sys.modules["antigravity"], "__path__"):
    del sys.modules["antigravity"]

from antigravity.sandbox.manager import SandboxManager

try:
    from .protocol import log_stderr
    from .server import AntigravityMCPServer
    from .tools import MCPToolRegistry, ServiceWorkerDaemon
except (ImportError, ValueError):
    from antigravity.mcp.protocol import log_stderr
    from antigravity.mcp.server import AntigravityMCPServer
    from antigravity.mcp.tools import MCPToolRegistry, ServiceWorkerDaemon


def parse_args() -> argparse.Namespace:
    """Parse command line arguments for MCP server runner."""
    parser = argparse.ArgumentParser(
        prog="antigravity-mcp-server",
        description="Antigravity MCP Server over stdio JSON-RPC 2.0 transport.",
    )
    parser.add_argument(
        "--mode",
        choices=["auto", "local", "e2b"],
        default=os.environ.get("ANTIGRAVITY_SANDBOX_MODE", "auto"),
        help="Default sandbox execution isolation backend (default: auto)",
    )
    parser.add_argument(
        "--default-timeout",
        type=float,
        default=float(os.environ.get("ANTIGRAVITY_DEFAULT_TIMEOUT", "300.0")),
        help="Default sandbox timeout in seconds (default: 300.0)",
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default=os.environ.get("ANTIGRAVITY_LOG_LEVEL", "INFO"),
        help="Server logging level written to stderr (default: INFO)",
    )
    return parser.parse_args()


def configure_logging(level_name: str = "INFO") -> None:
    """
    Configure logging to write strictly to stderr so stdout remains 100% clean
    for JSON-RPC framing.
    """
    numeric_level = getattr(logging, level_name.upper(), logging.INFO)
    handler = logging.StreamHandler(sys.stderr)
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    # Remove existing handlers that might touch stdout
    root_logger.handlers = [handler]


async def run_server_async(args: Optional[argparse.Namespace] = None) -> None:
    """Asynchronous entry point to create and run the MCP Server."""
    if args is None:
        args = parse_args()

    configure_logging(args.log_level)
    log_stderr(f"Starting Antigravity MCP Server (mode={args.mode}, default_timeout={args.default_timeout})...")

    manager = SandboxManager()
    daemon = ServiceWorkerDaemon(sandbox_manager=manager)
    server = AntigravityMCPServer(sandbox_manager=manager, scheduler_daemon=daemon)

    try:
        await server.run_stdio()
    finally:
        manager.destroy_all()


def main() -> None:
    """Synchronous CLI entry point for console script."""
    args = parse_args()
    try:
        asyncio.run(run_server_async(args))
    except KeyboardInterrupt:
        log_stderr("MCP Server received keyboard interrupt, exiting.")
        sys.exit(0)
    except Exception as exc:
        log_stderr(f"Fatal error in MCP Server: {exc}", level="ERROR")
        sys.exit(1)


if __name__ == "__main__":
    main()
