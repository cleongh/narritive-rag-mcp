import asyncio
import json
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
    
    result = await mcp_session.call_tool(tool_name, arguments=arguments) # type: ignore
    return result.content[0].text # type: ignore

def format_tools_for_openai() -> List[Dict[str, Any]]:
    """Format MCP tools as OpenAI function definitions"""
    return [
        {
            "type": "function",
            "function": {
                "name": "get_elf_name",
                "description": "Returns a randomly generated typical elf name from Tolkien's legendarium",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "count": {
                            "type": "integer",
                            "description": "Number of elf names to generate",
                            "default": 1
                        }
                    },
                    "required": []
                }
            }
        }
    ]

async def process_tool_calls(messages: List[Dict], response_message: Dict) -> List[Dict]:
    """Process tool calls from LLM response and add results to messages"""
    if "tool_calls" not in response_message:
        return messages
    
    # Add assistant message with tool calls
    messages.append(response_message)
    
    # Execute each tool call
    for tool_call in response_message["tool_calls"]:
        function_name = tool_call["function"]["name"]
        function_args = json.loads(tool_call["function"]["arguments"])
        
        print(f"Executing MCP tool: {function_name} with args: {function_args}")
        
        # Call the MCP tool
        result = await call_mcp_tool(function_name, function_args)
        
        # Add tool response to messages
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call["id"],
            "name": function_name,
            "content": result
        })
    
    return messages

@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    """Proxy chat completions with MCP tool support"""
    try:
        body = await request.json()
        
        # Add tools to the request if not present
        if "tools" not in body:
            body["tools"] = format_tools_for_openai()
        
        # Enable tool calling - "auto" lets the model decide when to use tools
        if "tool_choice" not in body:
            body["tool_choice"] = "auto"
        
        messages = body.get("messages", [])
        max_iterations = 5
        
        # Test llamafile connection first
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                test_response = await client.get(f"{LLAMAFILE_URL}/v1/models")
                print(f"Llamafile connection OK: {test_response.status_code}")
            except Exception as e:
                return JSONResponse(
                    content={"error": f"Cannot connect to llamafile at {LLAMAFILE_URL}: {str(e)}"},
                    status_code=503
                )
            
            for iteration in range(max_iterations):
                print(f"\n=== Iteration {iteration + 1} ===")
                print(f"Sending {len(messages)} messages to llamafile")
                print(f"Tools available: {len(body.get('tools', []))}")
                print(f"Tool choice: {body.get('tool_choice', 'not set')}")
                
                # Call llamafile
                try:
                    response = await client.post(
                        f"{LLAMAFILE_URL}/v1/chat/completions",
                        json=body,
                        timeout=300.0
                    )
                    response.raise_for_status()
                except httpx.HTTPError as e:
                    return JSONResponse(
                        content={"error": f"Llamafile request failed: {str(e)}"},
                        status_code=502
                    )
                
                result = response.json()
                response_message = result["choices"][0]["message"]
                
                print(f"Response message keys: {response_message.keys()}")
                print(f"Response message content preview: {response_message.get('content', '')[:200]}")
                print(f"Has tool_calls: {'tool_calls' in response_message}")
                if 'tool_calls' in response_message:
                    print(f"Tool calls: {response_message['tool_calls']}")
                
                # Check if there are tool calls
                if "tool_calls" in response_message and response_message["tool_calls"]:
                    print(f"Tool calls detected: {len(response_message['tool_calls'])}")
                    
                    # Process tool calls and update messages
                    messages = await process_tool_calls(messages, response_message)
                    body["messages"] = messages
                    
                    # Continue to next iteration to get final response
                    continue
                else:
                    # No more tool calls, return the response
                    print("No tool calls, returning final response")
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
        "mcp_initialized": mcp_session is not None
    }

@app.get("/v1/models")
async def list_models():
    """Proxy models endpoint"""
    print("Received /v1/models request")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{LLAMAFILE_URL}/v1/models")
            return JSONResponse(content=response.json())
    except Exception as e:
        print(f"Error proxying models: {e}")
        return JSONResponse(
            content={"error": f"Cannot reach llamafile: {str(e)}"},
            status_code=503
        )

@app.on_event("startup")
async def startup_event():
    """Initialize MCP on startup - but don't block"""
    global mcp_init_task
    print("FastAPI startup - scheduling MCP initialization...")
    # Initialize MCP in background
    mcp_init_task = asyncio.create_task(initialize_mcp())

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup MCP on shutdown"""
    global mcp_streams
    print("Shutting down...")
    if mcp_streams:
        try:
            await mcp_streams.__aexit__(None, None, None)
        except Exception as e:
            print(f"Error closing MCP: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("MCP Bridge Server")
    print("=" * 60)
    print(f"Bridge:    http://127.0.0.1:8081")
    print(f"Llamafile: {LLAMAFILE_URL}")
    print("=" * 60)
    print("\nStarting server...\n")
    
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8081,
        log_level="info"
    )
