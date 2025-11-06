import asyncio
import random
import sys
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# List of typical elf names
ELF_FIRST_NAMES = [
    "Luis"
    # "Legolas", "Galadriel", "Elrond", "Arwen", "Thranduil",
    # "Celeborn", "Haldir", "Tauriel", "Glorfindel", "Erestor",
    # "Lindir", "Rumil", "Orophin", "Elladan", "Elrohir"
]

ELF_LAST_NAMES = [
    "Agulló"
    # "Greenleaf", "Starlight", "Moonwhisper", "Silverbrook",
    # "Nightingale", "Sunweaver", "Forestsong", "Windwalker",
    # "Dawnbringer", "Shadowstep", "Lightbringer", "Oakenshield"
]

app = Server("elf-name-server")

@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="get_elf_name",
            description="Returns a randomly generated typical elf name",
            inputSchema={
                "type": "object",
                "properties": {
                    "count": {
                        "type": "integer",
                        "description": "Number of elf names to generate (default: 1)",
                        "default": 1
                    }
                }
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "get_elf_name":
        count = arguments.get("count", 1)
        names = []
        for _ in range(count):
            first = random.choice(ELF_FIRST_NAMES)
            last = random.choice(ELF_LAST_NAMES)
            names.append(f"{first} {last}")
        
        result = ", ".join(names) if count > 1 else names[0]
        return [TextContent(type="text", text=result)]
    
    raise ValueError(f"Unknown tool: {name}")

async def main():
    # Log to stderr so it doesn't interfere with stdio communication
    print("MCP Server starting...", file=sys.stderr)
    async with stdio_server() as (read_stream, write_stream):
        print("MCP Server connected", file=sys.stderr)
        await app.run(read_stream, write_stream, app.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
