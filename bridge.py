"""Entry point module for the MCP bridge.

This is a clearer, short name for the bridge library. It wraps the
functionality previously exposed by `mcp_bridge_simple.py` and simply re-exports
its public API so callers can import `bridge.create_bridge_app` or
`bridge.run_bridge`.
"""
from mcp_bridge_simple import create_bridge_app, run_bridge, LLAMAFILE_URL  # re-export

__all__ = ["create_bridge_app", "run_bridge", "LLAMAFILE_URL"]
