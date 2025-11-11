"""
Example runner for the generic MCP bridge.

This script contains the story-generation example that used to live in
`mcp_bridge_simple.py`'s `__main__` block. It defines the local example tools
and starts the Flask bridge using the library's factory.
"""
import random
from mcp_bridge_flask import run_bridge, LLAMAFILE_URL

first_names = ["Luis"]
last_names = ["Agulló"]

locations = [
    "the Golden Wood of Lothlórien",
    "the Grey Havens by the sea",
    "the halls of Rivendell",
    "the gardens of Valinor",
    "the forests of Mirkwood",
    "the towers of Gondolin",
    "the shores of Númenor",
    "the realm of Doriath"
]

features = [
    "where ancient trees whisper secrets of old",
    "bathed in the eternal light of the Two Trees",
    "where the stars shine brighter than elsewhere in Middle-earth",
    "protected by enchantments woven in the Elder Days",
    "where time flows differently than in mortal lands",
    "adorned with fountains that sing melodious songs",
    "where the air itself seems to shimmer with magic",
    "overlooking valleys filled with silver mist"
]

events = [
    "discovers a hidden talent they never knew they possessed",
    "must choose between duty and personal desire",
    "receives a mysterious visitor bearing urgent news",
    "finds an ancient artifact with unknown powers",
    "witnesses a rare celestial phenomenon that changes everything",
    "must overcome their greatest fear to help a friend",
    "uncovers a long-buried secret about their heritage",
    "faces a challenge that tests their deepest beliefs"
]


def local_executor(tool_name: str, arguments: dict) -> str:
    if tool_name == "get_elf_name":
        count = int(arguments.get("count", 1))
        names = [f"{random.choice(first_names)} {random.choice(last_names)}" for _ in range(count)]
        return ", ".join(names) if count > 1 else names[0]

    if tool_name == "get_location_description":
        style = arguments.get("style", "brief")
        loc = random.choice(locations)
        feat = random.choice(features)
        return f"{loc}, {feat}" if style == "detailed" else loc

    if tool_name == "get_random_event":
        return random.choice(events)

    return f"UNKNOWN_TOOL: {tool_name}"


if __name__ == "__main__":
    print("Starting example bridge on http://127.0.0.1:8081 using local example tools")
    run_bridge(host="127.0.0.1", port=8081, llamafile_url=LLAMAFILE_URL, mcp_executor=local_executor)
