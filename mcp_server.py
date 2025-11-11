import asyncio
import random
import sys
import inspect
from typing import Callable, Dict, Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# --- Data used by default tools ---
ELF_FIRST_NAMES = [
    "Luis"
]

ELF_LAST_NAMES = [
    "Agulló"
]

LOCATIONS = [
    "the Golden Wood of Lothlórien",
    "the Grey Havens by the sea",
    "the halls of Rivendell",
    "the gardens of Valinor",
    "the forests of Mirkwood",
    "the towers of Gondolin",
    "the shores of Númenor",
    "the realm of Doriath"
]

LOCATION_FEATURES = [
    "where ancient trees whisper secrets of old",
    "bathed in the eternal light of the Two Trees",
    "where the stars shine brighter than elsewhere in Middle-earth",
    "protected by enchantments woven in the Elder Days",
    "where time flows differently than in mortal lands",
    "adorned with fountains that sing melodious songs",
    "where the air itself seems to shimmer with magic",
    "overlooking valleys filled with silver mist"
]

EVENTS = [
    "discovers a hidden talent they never knew they possessed",
    "must choose between duty and personal desire",
    "receives a mysterious visitor bearing urgent news",
    "finds an ancient artifact with unknown powers",
    "witnesses a rare celestial phenomenon that changes everything",
    "must overcome their greatest fear to help a friend",
    "uncovers a long-buried secret about their heritage",
    "faces a challenge that tests their deepest beliefs"
]


def _normalize_handler_result(res: Any) -> list[TextContent]:
    """Normalize various handler return types into a list[TextContent]."""
    if isinstance(res, list):
        # If list of TextContent-like objects or strings
        contents: list[TextContent] = []
        for item in res:
            if isinstance(item, TextContent):
                contents.append(item)
            elif isinstance(item, str):
                contents.append(TextContent(type="text", text=item))
            else:
                # Fallback: convert to string
                contents.append(TextContent(type="text", text=str(item)))
        return contents
    elif isinstance(res, TextContent):
        return [res]
    else:
        return [TextContent(type="text", text=str(res))]


def default_tools() -> Dict[str, Dict[str, Any]]:
    """Return a mapping of default tool definitions and handlers.

    Each entry maps tool_name -> { 'tool': Tool(...), 'handler': callable }
    The handler will receive a single argument: the parsed arguments dict.
    """
    def get_elf_name_handler(arguments: dict):
        count = int(arguments.get("count", 1))
        names = []
        for _ in range(count):
            first = random.choice(ELF_FIRST_NAMES)
            last = random.choice(ELF_LAST_NAMES)
            names.append(f"{first} {last}")
        return ", ".join(names) if count > 1 else names[0]

    def get_location_description_handler(arguments: dict):
        style = arguments.get("style", "brief")
        location = random.choice(LOCATIONS)
        feature = random.choice(LOCATION_FEATURES)
        return f"{location}, {feature}" if style == "detailed" else location

    def get_random_event_handler(arguments: dict):
        return random.choice(EVENTS)

    # By default the library exposes no built-in tools.
    # Callers should provide their own tools mapping when starting the server.
    return {}


def create_mcp_server(tools: Dict[str, Dict[str, Any]], server_name: str = "mcp-server") -> Server:
    """Create and return an MCP Server instance that exposes the provided tools.

    tools: mapping tool_name -> { 'tool': Tool, 'handler': callable }
    Handlers may be sync or async callables that accept a single dict argument.
    """
    app = Server(server_name)

    @app.list_tools()
    async def _list_tools() -> list[Tool]:
        return [entry["tool"] for entry in tools.values()]

    @app.call_tool()
    async def _call_tool(name: str, arguments: dict) -> list[TextContent]:
        if name not in tools:
            raise ValueError(f"Unknown tool: {name}")

        handler = tools[name]["handler"]

        # Support both sync and async handlers
        if inspect.iscoroutinefunction(handler):
            res = await handler(arguments)
        else:
            res = handler(arguments)

        return _normalize_handler_result(res)

    return app


async def start_mcp_server(tools: Dict[str, Dict[str, Any]], server_name: str = "mcp-server") -> None:
    """Start the MCP server over stdio using the provided tools mapping."""
    app = create_mcp_server(tools, server_name=server_name)
    # Log to stderr so it doesn't interfere with stdio communication
    print(f"MCP Server '{server_name}' starting...", file=sys.stderr)
    async with stdio_server() as (read_stream, write_stream):
        print("MCP Server connected", file=sys.stderr)
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    # Backwards-compatible CLI: start the default tools
    asyncio.run(start_mcp_server(default_tools(), server_name="elf-name-server"))
