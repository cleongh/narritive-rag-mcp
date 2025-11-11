# MCP Tools Reference

## Available Tools

The MCP server now provides **three tools** for story generation:

### 1. `get_elf_name`

**Purpose:** Generate authentic elf names from Tolkien's legendarium.

**Parameters:**
- `count` (integer, optional): Number of names to generate (default: 1)

**Usage:**
```
TOOL_CALL: get_elf_name(count=1)
```

**Example Result:**
```
Luis Agulló
```

**Use Cases:**
- Character creation
- NPC generation
- Populating elf societies

---

### 2. `get_location_description`

**Purpose:** Generate Tolkien-inspired location descriptions for story settings.

**Parameters:**
- `style` (string, optional): Description style
  - `'brief'` - Just the location name (default)
  - `'detailed'` - Location name + atmospheric detail

**Usage:**
```
TOOL_CALL: get_location_description(style='brief')
TOOL_CALL: get_location_description(style='detailed')
```

**Example Results:**
- Brief: `"the Golden Wood of Lothlórien"`
- Detailed: `"the gardens of Valinor, bathed in the eternal light of the Two Trees"`

**Available Locations:**
- the Golden Wood of Lothlórien
- the Grey Havens by the sea
- the halls of Rivendell
- the gardens of Valinor
- the forests of Mirkwood
- the towers of Gondolin
- the shores of Númenor
- the realm of Doriath

**Atmospheric Features:**
- where ancient trees whisper secrets of old
- bathed in the eternal light of the Two Trees
- where the stars shine brighter than elsewhere in Middle-earth
- protected by enchantments woven in the Elder Days
- where time flows differently than in mortal lands
- adorned with fountains that sing melodious songs
- where the air itself seems to shimmer with magic
- overlooking valleys filled with silver mist

---

### 3. `get_random_event`

**Purpose:** Generate random story events or conflicts to drive narratives forward.

**Parameters:** None

**Usage:**
```
TOOL_CALL: get_random_event()
```

**Example Results:**
- `"discovers a hidden talent they never knew they possessed"`
- `"must choose between duty and personal desire"`
- `"finds an ancient artifact with unknown powers"`

**Available Events:**
- discovers a hidden talent they never knew they possessed
- must choose between duty and personal desire
- receives a mysterious visitor bearing urgent news
- finds an ancient artifact with unknown powers
- witnesses a rare celestial phenomenon that changes everything
- must overcome their greatest fear to help a friend
- uncovers a long-buried secret about their heritage
- faces a challenge that tests their deepest beliefs

---

## Complete Example

### Multi-Tool Story Generation

**Prompt:**
```
Create a story opening using:
1. get_elf_name for a character
2. get_location_description(style='detailed') for setting
3. get_random_event for plot
```

**Tool Calls:**
```
TOOL_CALL: get_elf_name(count=1)
→ TOOL_RESULT: Luis Agulló

TOOL_CALL: get_location_description(style='detailed')
→ TOOL_RESULT: the shores of Númenor, where the air itself seemed to shimmer with magic

TOOL_CALL: get_random_event()
→ TOOL_RESULT: witnesses a rare celestial phenomenon that changes everything
```

**Generated Story:**
```
Luis Agulló, a scholar of forgotten lore, stood upon the shores of 
Númenor, where the air itself seemed to shimmer with magic. Suddenly, 
he witnessed a rare celestial phenomenon—a convergence of stars unlike 
any recorded—that irrevocably altered the course of his life and the 
fate of the island kingdom.
```

---

## Testing Tools

### Test Individual Tools
```bash
# Quick test of all tools
uv run python test_all_tools.py
```

### Use in Story Generation
```bash
# Simple story with multiple tools
uv run python llm_story_with_tools.py

# Full RAG + tools
uv run python llm_story_working.py
```

---

## Adding Your Own Tools

### 1. Edit `mcp_server.py`

Add tool definition:
```python
Tool(
    name="your_tool_name",
    description="What your tool does",
    inputSchema={
        "type": "object",
        "properties": {
            "param_name": {
                "type": "string",
                "description": "Parameter description"
            }
        }
    }
)
```

Add implementation:
```python
elif name == "your_tool_name":
    param = arguments.get("param_name", "default")
    result = your_logic_here(param)
    return [TextContent(type="text", text=result)]
```

### 2. Edit `mcp_bridge_flask.py`

Update system prompt:
```python
Available tools:
- get_elf_name(count=1): ...
- get_location_description(style='brief'): ...
- get_random_event(): ...
- your_tool_name(param_name='value'): Your tool description
```

Update `call_mcp_tool()`:
```python
elif tool_name == "your_tool_name":
    param = arguments.get("param_name", "default")
    result = your_logic_here(param)
    print(f"[MCP] Tool result: {result}", file=sys.stderr)
    return result
```

### 3. Test Your Tool

```bash
# Restart bridge
pkill -f mcp_bridge_simple
uv run python mcp_bridge_simple.py

# Test
uv run python test_simple_bridge.py
```

---

## Tool Design Best Practices

### 1. Keep It Simple
- Single, clear purpose
- Minimal parameters
- Predictable output

### 2. Make It Deterministic (When Possible)
- Same inputs → same outputs (unless randomness is the feature)
- Clear error messages
- Validate inputs

### 3. Document Well
- Clear description
- Parameter types and defaults
- Example usage

### 4. Return Text
- Tools return `TextContent`
- Keep output concise
- Format for LLM consumption

### 5. Test Thoroughly
- Create test script
- Try edge cases
- Verify in stories

---

## Tool Ideas for Extension

### Story Elements:
- `get_weather_condition()` - atmospheric details
- `get_time_of_day()` - temporal setting
- `get_magical_object()` - artifacts and items
- `get_creature()` - monsters and beings

### Character Development:
- `get_character_trait()` - personality attributes
- `get_motivation()` - character goals
- `get_backstory_element()` - history details
- `get_relationship()` - character connections

### World Building:
- `get_historical_event()` - lore elements
- `get_custom_or_tradition()` - cultural details
- `get_prophecy()` - mystical predictions
- `get_legend()` - myths and tales

### Plot Mechanics:
- `get_plot_twist()` - story reversals
- `get_moral_dilemma()` - ethical choices
- `get_quest_objective()` - mission goals
- `get_obstacle()` - challenges

---

## Performance Notes

- Each tool call adds ~2-3 seconds
- Multiple tools in one request: iterative processing
- Tool execution is fast, LLM inference is slow
- Total time = (number of tool calls × LLM inference) + tool overhead

Example timing:
```
1 tool:  ~15-20 seconds
2 tools: ~30-40 seconds
3 tools: ~45-60 seconds
```

---

## Troubleshooting

### Tool not called?
1. Check system prompt includes the tool
2. Verify bridge has the tool implementation
3. Test with explicit instruction to use the tool

### Wrong output format?
1. LLM might be making up content
2. Strengthen system prompt
3. Add examples of tool usage

### Timeout with multiple tools?
1. Reduce max_tokens
2. Use simpler prompts
3. Call tools separately instead of all at once

---

**Last Updated:** November 7, 2025  
**Tools Available:** 3 (get_elf_name, get_location_description, get_random_event)
