import asyncio
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn
import httpx

app = FastAPI()

# Global MCP session
mcp_session: Optional[ClientSession] = None
mcp_streams = None
mcp_init_task = None

# Llamafile backend
LLAMAFILE_URL = "http://localhost:8080"

async def initialize_mcp():
    """Initialize MCP client connection"""
    global mcp_session, mcp_streams
    
    print("Initializing MCP server...")
    server_path = Path(__file__).parent / "mcp_server.py"
    server_params = StdioServerParameters(
        command="python",
        args=[str(server_path)],
        env=None
    )
    
    try:
        mcp_streams = stdio_client(server_params)
        read, write = await mcp_streams.__aenter__()
        
        session = ClientSession(read, write)
        await session.initialize()
        mcp_session = session
        
        print("✓ MCP server initialized successfully")
        return session
    except Exception as e:
        print(f"✗ Error initializing MCP: {e}")
        import traceback
        traceback.print_exc()
        raise

async def call_mcp_tool(tool_name: str, arguments: dict) -> str:
    """Call an MCP tool and return the result"""
    if mcp_session is None:
        await initialize_mcp()
    
    print(f"[MCP] Calling tool: {tool_name} with args: {arguments}")
    result = await mcp_session.call_tool(tool_name, arguments=arguments) # type: ignore
    tool_result = result.content[0].text # type: ignore
    print(f"[MCP] Tool result: {tool_result}")
    return tool_result

def create_system_prompt_with_tools() -> str:
    """Create a system prompt that teaches the LLM how to call tools"""
    return """You are a helpful assistant with access to tools/functions. When you need to use a tool, output EXACTLY in this format:

TOOL_CALL: function_name(arg1=value1, arg2=value2)

Available tools:
- get_elf_name(count=1): Returns randomly generated elf names from Tolkien's legendarium

Example:
User: Generate an elf name
Assistant: TOOL_CALL: get_elf_name(count=1)

After you see a TOOL_RESULT, use it naturally in your response.
"""

def extract_tool_call(text: str) -> Optional[tuple[str, dict]]:
    """Extract tool call from LLM response"""
    # Look for pattern: TOOL_CALL: function_name(arg1=value1, arg2=value2)
    pattern = r'TOOL_CALL:\s*(\w+)\((.*?)\)'
    match = re.search(pattern, text, re.IGNORECASE)
    
    if not match:
        return None
    
    function_name = match.group(1)
    args_str = match.group(2).strip()
    
    # Parse arguments
    arguments = {}
    if args_str:
        # Simple parsing: arg=value, arg=value
        for arg_pair in args_str.split(','):
            if '=' in arg_pair:
                key, value = arg_pair.split('=', 1)
                key = key.strip()
                value = value.strip()
                # Try to convert to int if possible
                try:
                    value = int(value)
                except ValueError:
                    # Remove quotes if present
                    value = value.strip('"\'')
                arguments[key] = value
    
    print(f"[PARSE] Extracted tool call: {function_name}({arguments})")
    return function_name, arguments

@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    """Proxy chat completions with simulated MCP tool support"""
    try:
        body = await request.json()
        messages = body.get("messages", [])
        
        # Add system prompt with tool instructions
        enhanced_messages = [
            {"role": "system", "content": create_system_prompt_with_tools()}
        ] + messages
        
        max_iterations = 5
        
        async with httpx.AsyncClient(timeout=180.0) as client:
            for iteration in range(max_iterations):
                print(f"\n{'='*60}")
                print(f"Iteration {iteration + 1}")
                print(f"{'='*60}")
                
                # Prepare request for llamafile (WITHOUT tools - plain text)
                llm_request = {
                    "model": body.get("model", "local-model"),
                    "messages": enhanced_messages,
                    "temperature": body.get("temperature", 0.7),
                    "max_tokens": body.get("max_tokens", 1000)
                }
                
                # Call llamafile
                try:
                    response = await client.post(
                        f"{LLAMAFILE_URL}/v1/chat/completions",
                        json=llm_request,
                        timeout=180.0  # Increased timeout for slow models like DeepSeek-R1
                    )
                    response.raise_for_status()
                except httpx.HTTPError as e:
                    return JSONResponse(
                        content={"error": f"Llamafile request failed: {str(e)}"},
                        status_code=502
                    )
                
                result = response.json()
                assistant_message = result["choices"][0]["message"]["content"]
                
                print(f"[LLM Response]:\n{assistant_message}\n")
                
                # Check if LLM wants to call a tool
                tool_call = extract_tool_call(assistant_message)
                
                if tool_call:
                    function_name, arguments = tool_call
                    
                    # Call the MCP tool
                    try:
                        tool_result = await call_mcp_tool(function_name, arguments)
                        
                        # Add assistant message and tool result to conversation
                        enhanced_messages.append({
                            "role": "assistant",
                            "content": assistant_message
                        })
                        enhanced_messages.append({
                            "role": "user",
                            "content": f"TOOL_RESULT: {tool_result}\n\nNow continue with your response using this information."
                        })
                        
                        # Continue to next iteration
                        continue
                        
                    except Exception as e:
                        print(f"[ERROR] Tool call failed: {e}")
                        enhanced_messages.append({
                            "role": "assistant",
                            "content": assistant_message
                        })
                        enhanced_messages.append({
                            "role": "user",
                            "content": f"TOOL_ERROR: {str(e)}\n\nPlease continue without the tool."
                        })
                        continue
                else:
                    # No tool call, return final response
                    print("[DONE] No tool call detected, returning response")
                    return JSONResponse(content=result)
            
            # Max iterations reached
            return JSONResponse(
                content={"error": "Maximum tool call iterations reached"},
                status_code=500
            )
    
    except Exception as e:
        print(f"Error in chat_completions: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            content={"error": f"Internal error: {str(e)}"},
            status_code=500
        )

@app.get("/health")
async def health():
    """Health check"""
    return {
        "status": "ok",
        "mcp_initialized": mcp_session is not None,
        "mode": "simulated_tool_calling"
    }

@app.get("/v1/models")
async def list_models():
    """Proxy models endpoint"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{LLAMAFILE_URL}/v1/models")
            return JSONResponse(content=response.json())
    except Exception as e:
        return JSONResponse(
            content={"error": f"Cannot reach llamafile: {str(e)}"},
            status_code=503
        )

@app.on_event("startup")
async def startup_event():
    """Initialize MCP on startup"""
    global mcp_init_task
    print("FastAPI startup - scheduling MCP initialization...")
    mcp_init_task = asyncio.create_task(initialize_mcp())

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup MCP on shutdown"""
    global mcp_streams
    if mcp_streams:
        try:
            await mcp_streams.__aexit__(None, None, None)
        except Exception as e:
            print(f"Error closing MCP: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("MCP Bridge Server (SIMULATED TOOL CALLING)")
    print("=" * 60)
    print(f"Bridge:    http://127.0.0.1:8081")
    print(f"Llamafile: {LLAMAFILE_URL}")
    print("Mode:      Simulated (text-based tool calls)")
    print("=" * 60)
    print("\nStarting server...\n")
    
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8081,
        log_level="info"
    )
