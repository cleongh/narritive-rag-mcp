# Llamafile Story Generator with MCP and RAG

A Python project that uses LangChain to connect to a locally running llamafile, with an MCP (Model Context Protocol) bridge for **simulated tool calling** and RAG (Retrieval-Augmented Generation) using The Silmarillion as context.

## Features

- **Simulated MCP Tool Calling**: Works with ANY LLM (Gemma, DeepSeek, etc.) using prompt-based tool invocation
- **RAG**: Uses The Silmarillion text to provide rich contextual knowledge
- **Local LLM**: Runs entirely locally using llamafile
- **Reliable**: Simple Flask-based bridge that's easy to debug and understand

## How It Works

Most open-source LLMs (including Gemma and DeepSeek-R1) **don't support native OpenAI-style function calling**. This project solves that by:

1. **Teaching the LLM** to output tool calls in a specific format: `TOOL_CALL: function_name(args)`
2. **Parsing** the LLM's text output to detect tool calls
3. **Executing** the MCP tool and injecting the result back into the conversation
4. **Continuing** the conversation with the tool result

This "simulated" approach is more reliable than native function calling for many models.

## Installation

Install dependencies using uv:

```bash
uv sync
```

Dependencies include:
- `langchain` and `langchain-openai` for LLM integration
- `flask` and `requests` for the MCP bridge
- `faiss-cpu` and `sentence-transformers` for RAG
- `mcp` for MCP server protocol

## Usage

### 1. Start your llamafile (Terminal 1)

**Recommended: Gemma (faster)**
```bash
~/programas/google_gemma-3-12b-it-Q4_K_M.llamafile --server --nobrowser -ngl 18 --gpu nvidia
```

**Alternative: DeepSeek (slower but larger)**
```bash
~/programas/DeepSeek-R1-Distill-Qwen-14B-Q4_K_M.llamafile --server --nobrowser -ngl 32 --gpu nvidia
```

Wait until you see `llama server listening at http://localhost:8080`

### 2. Start the MCP bridge (Terminal 2)

```bash
uv run python mcp_bridge_simple.py
```

You should see:
```
============================================================
SIMPLE MCP Bridge Server
============================================================
Bridge:    http://127.0.0.1:8081
Llamafile: http://localhost:8080
Mode:      Simple simulated tool calling (Flask + requests)
============================================================
 * Running on http://127.0.0.1:8081
```

### 3. Run the story generator (Terminal 3)

**Simple version (no RAG, fast):**
```bash
uv run python llm_story_simple.py
```

**Full version (with RAG from Silmarillion):**
```bash
uv run python llm_story_working.py
```

This will:
1. Check MCP bridge connectivity
2. Load The Silmarillion for RAG (if using `llm_story_working.py`)
3. Retrieve relevant context about elves, art, and Valinor
4. Request a story about an elf learning to paint
5. The LLM outputs `TOOL_CALL: get_elf_name(count=1)`
6. The bridge calls the MCP tool and gets a name (e.g., "Luis Agulló")
7. The LLM generates a Tolkien-style story using that name and RAG context

## Testing

**Test the bridge is working:**
```bash
uv run python test_simple_bridge.py
```

**Check bridge health:**
```bash
curl http://127.0.0.1:8081/health
```

**Test tool calling directly:**
```bash
uv run python test_tool_calling.py
```

## Project Structure

```
.
├── mcp_bridge_simple.py      # Working simulated MCP bridge (Flask-based)
├── mcp_server.py              # MCP server with get_elf_name tool
├── llm_query.py               # LangChain integration with RAG
├── llm_story_simple.py        # Simple story generator (no RAG)
├── llm_story_working.py       # Full RAG + MCP story generator
├── test_simple_bridge.py      # Test the bridge
├── test_deepseek_tools.py     # Test if models support native function calling
├── silmarillion.txt           # RAG knowledge base
└── README.md                  # This file
```

## Which Models Support Native Function Calling?

Based on testing:

### ✅ Support Native Function Calling:
- GPT-4, GPT-4 Turbo, GPT-3.5-turbo (OpenAI API)
- Claude 3+ (Anthropic API)
- Mistral Large, Mistral 7B-Instruct-v0.2+
- Nous-Hermes models (specifically trained)
- Functionary models (specifically designed)

### ❌ Don't Support Native Function Calling:
- **Gemma** (what we're using) - Use simulated bridge
- **DeepSeek-R1** - Use simulated bridge
- LLaMA 2 (LLaMA 3 has partial support)
- Phi models
- Vicuna

**Solution:** Use `mcp_bridge_simple.py` which works with ALL models!

## Troubleshooting

### Bridge times out
- **DeepSeek-R1** is very slow due to chain-of-thought reasoning
- Switch to **Gemma** for faster responses
- Reduce context size or story length
- Increase timeouts in the bridge

### LLM doesn't call the tool
- Make sure you're using `mcp_bridge_simple.py` (not `mcp_bridge.py`)
- The simulated bridge teaches the LLM the tool calling syntax
- Check bridge logs to see if tool calls are being detected

### Port already in use
```bash
pkill -f "mcp_bridge"
```

## Advanced: Creating Your Own MCP Tools

Edit `mcp_server.py` to add new tools:

```python
@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="your_tool_name",
            description="What your tool does",
            inputSchema={
                "type": "object",
                "properties": {
                    "param": {"type": "string", "description": "Parameter description"}
                }
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "your_tool_name":
        result = do_something(arguments["param"])
        return [TextContent(type="text", text=result)]
```

Then add the tool to `mcp_bridge_simple.py` in the `call_mcp_tool()` function.

## License

MIT