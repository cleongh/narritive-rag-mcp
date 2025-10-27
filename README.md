# Llamafile Story Generator

A Python project that uses LangChain to connect to a locally running llamafile and an MCP server to generate stories with elf characters, using The Silmarillion as RAG context.

## Installation

Install dependencies using uv:

```bash
uv sync
```

## Usage

1. Start your llamafile (typically runs on http://localhost:8080)

2. Run the story generator:

```bash
uv run python llamafile_story.py
```

## Components

- `llamafile_story.py` - Main script that connects to llamafile and MCP server with RAG
- `mcp_server.py` - MCP server that provides elf name generation tool
- `silmarillion.txt` - Source text for RAG (Retrieval-Augmented Generation)
- `pyproject.toml` - Project dependencies managed by uv

## Features

- **RAG**: Uses The Silmarillion text to provide contextual knowledge
- **MCP**: Elf name generation through Model Context Protocol server
- **LLM**: Connects to local llamafile for story generation
