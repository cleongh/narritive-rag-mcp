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

# Tolkien-inspired locations
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

# Story events/conflicts
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

app = Server("elf-name-server")

@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="get_elf_name",
            description="Returns a randomly generated typical elf name from Tolkien's legendarium",
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
        ),
        Tool(
            name="get_location_description",
            description="Returns a description of a Tolkien-inspired location for story settings",
            inputSchema={
                "type": "object",
                "properties": {
                    "style": {
                        "type": "string",
                        "description": "Style of description: 'brief' or 'detailed' (default: 'brief')",
                        "default": "brief",
                        "enum": ["brief", "detailed"]
                    }
                }
            }
        ),
        Tool(
            name="get_random_event",
            description="Returns a random story event or conflict to drive the narrative forward",
            inputSchema={
                "type": "object",
                "properties": {}
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
    
    elif name == "get_location_description":
        style = arguments.get("style", "brief")
        location = random.choice(LOCATIONS)
        feature = random.choice(LOCATION_FEATURES)
        
        if style == "detailed":
            result = f"{location}, {feature}"
        else:
            result = location
        
        return [TextContent(type="text", text=result)]
    
    elif name == "get_random_event":
        event = random.choice(EVENTS)
        return [TextContent(type="text", text=event)]
    
    raise ValueError(f"Unknown tool: {name}")

async def main():
    # Log to stderr so it doesn't interfere with stdio communication
    print("MCP Server starting...", file=sys.stderr)
    async with stdio_server() as (read_stream, write_stream):
        print("MCP Server connected", file=sys.stderr)
        await app.run(read_stream, write_stream, app.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
