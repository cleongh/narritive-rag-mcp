# Llamafile Story Generator with MCP and RAG

A Python project that uses LangChain to connect to a locally running llamafile, with an MCP (Model Context Protocol) bridge for tool calling and RAG (Retrieval-Augmented Generation) using The Silmarillion as context.

## Features

- **MCP Bridge**: Translates between OpenAI-compatible API and MCP protocol
- **Tool Calling**: Llamafile can call MCP tools (e.g., elf name generation)
- **RAG**: Uses The Silmarillion text to provide rich contextual knowledge
- **Local LLM**: Runs entirely locally using llamafile

## Installation

Install dependencies using uv:

```bash
uv sync
```

## Usage

### 1\. Start your llamafile (Terminal 1)

```bash
./32-google_gemma-3-12b-it-Q4_K_M.llamafile --server --nobrowser -ngl 15
```

Wait until you see it's serving on http://localhost:8080

### 2\. Start the MCP bridge (Terminal 2)

```bash
uv run python mcp_bridge.py
```

You should see:

- "MCP Bridge Server" header
- "FastAPI startup - scheduling MCP initialization..."
- "✓ MCP server initialized successfully"
- Server running on http://127.0.0.1:8081

### 3\. Run the story generator (Terminal 3)

```bash
uv run python llamafile_story.py
```

This will:

1. Check MCP bridge connectivity
2. Load The Silmarillion for RAG
3. Request a story about an elf learning to paint
4. The LLM will call the MCP tool to get an elf name
5. Generate a Tolkien-style story using that name and RAG context

## Testing

Test the MCP bridge is working:

```bash
uv run python test_bridge.py
```

Or manually:

```bash
curl http://127.0.0.1:8081/health
curl http://127.0.0.1:8081/v1/models
```

## Project Structure