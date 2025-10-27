# Llamafile Story Generator

A Python project that uses LangChain to connect to a locally running llamafile and an MCP server to generate stories with elf characters.

## Installation

Install dependencies using uv:

```bash
uv sync
```

Or if you don't have a virtual environment yet:

```bash
uv venv
uv pip install -e .
```

## Usage

1. Start your llamafile (typically runs on http://localhost:8080)

2. Run the story generator:

```bash
uv run python llamafile_story.py
```

## Components

- `llamafile_story.py` - Main script that connects to llamafile and MCP server
- `mcp_server.py` - MCP server that provides elf name generation tool
- `pyproject.toml` - Project dependencies managed by uv
