"""Simple, reliable MCP bridge with simulated tool calling"""
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# Llamafile backend
LLAMAFILE_URL = "http://localhost:8080"

# MCP server process
mcp_process = None

def start_mcp_server():
    """Start the MCP server as a subprocess"""
    global mcp_process
    
    if mcp_process is None:
        server_path = Path(__file__).parent / "mcp_server.py"
        print(f"Starting MCP server: {server_path}", file=sys.stderr)
        
        mcp_process = subprocess.Popen(
            ["python", str(server_path)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        print("✓ MCP server started", file=sys.stderr)

def call_mcp_tool(tool_name: str, arguments: dict) -> str:
    """Call an MCP tool directly - simplified version"""
    print(f"[MCP] Calling tool: {tool_name} with args: {arguments}", file=sys.stderr)
    
    # For now, directly implement the elf name generation
    # In a full implementation, this would communicate with the MCP server
    if tool_name == "get_elf_name":
        import random
        first_names = ["Luis"]
        last_names = ["Agulló"]
        count = arguments.get("count", 1)
        
        names = []
        for _ in range(count):
            names.append(f"{random.choice(first_names)} {random.choice(last_names)}")
        
        result = ", ".join(names) if count > 1 else names[0]
        print(f"[MCP] Tool result: {result}", file=sys.stderr)
        return result
    
    return f"Unknown tool: {tool_name}"

def create_system_prompt() -> str:
    """System prompt that teaches the LLM how to call tools"""
    return """You are a helpful assistant with access to tools. When you need to use a tool, you MUST output it in this EXACT format on a line by itself:

TOOL_CALL: function_name(arg1=value1, arg2=value2)

Available tools:
- get_elf_name(count=1): Returns randomly generated elf names from Tolkien's legendarium

IMPORTANT: 
- Output the TOOL_CALL on its own line
- After you output a TOOL_CALL, STOP and wait for the result
- When you receive a TOOL_RESULT, use it naturally in your response
- Do NOT make up names, always use the tool

Example:
User: Generate an elf name for a story
Assistant: TOOL_CALL: get_elf_name(count=1)
[System provides result]
Assistant: Here's your elf name: [use the provided name]
"""

def extract_tool_call(text: str) -> Optional[tuple[str, dict]]:
    """Extract tool call from LLM response"""
    # Look for: TOOL_CALL: function_name(arg1=value1, arg2=value2)
    pattern = r'TOOL_CALL:\s*(\w+)\((.*?)\)'
    match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
    
    if not match:
        return None
    
    function_name = match.group(1)
    args_str = match.group(2).strip()
    
    arguments = {}
    if args_str:
        # Parse: arg=value, arg=value
        for arg_pair in args_str.split(','):
            if '=' in arg_pair:
                key, value = arg_pair.split('=', 1)
                key = key.strip()
                value = value.strip()
                # Try to convert to int
                try:
                    value = int(value)
                except ValueError:
                    value = value.strip('"\'')
                arguments[key] = value
    
    print(f"[PARSE] Extracted: {function_name}({arguments})", file=sys.stderr)
    return function_name, arguments

@app.route('/v1/chat/completions', methods=['POST'])
def chat_completions():
    """Handle chat completions with simulated tool calling"""
    try:
        body = request.get_json()
        messages = body.get("messages", [])
        
        # Add system prompt
        enhanced_messages = [
            {"role": "system", "content": create_system_prompt()}
        ] + messages
        
        max_iterations = 5
        
        for iteration in range(max_iterations):
            print(f"\n{'='*60}", file=sys.stderr)
            print(f"Iteration {iteration + 1}/{max_iterations}", file=sys.stderr)
            print(f"{'='*60}", file=sys.stderr)
            
            # Prepare request for llamafile
            llm_request = {
                "model": body.get("model", "local-model"),
                "messages": enhanced_messages,
                "temperature": body.get("temperature", 0.7),
                "max_tokens": body.get("max_tokens", 600),  # Reasonable limit
                "stream": False
            }
            
            print(f"Sending to llamafile with {len(enhanced_messages)} messages", file=sys.stderr)
            
            # Call llamafile
            try:
                response = requests.post(
                    f"{LLAMAFILE_URL}/v1/chat/completions",
                    json=llm_request,
                    timeout=180.0  # Increased timeout for complex requests
                )
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                print(f"[ERROR] Llamafile request failed: {e}", file=sys.stderr)
                return jsonify({"error": f"Llamafile request failed: {str(e)}"}), 502
            
            result = response.json()
            assistant_message = result["choices"][0]["message"]["content"]
            
            print(f"\n[LLM Response ({len(assistant_message)} chars)]:", file=sys.stderr)
            print(assistant_message[:300], file=sys.stderr)
            if len(assistant_message) > 300:
                print("...(truncated)", file=sys.stderr)
            
            # Check for tool call
            tool_call = extract_tool_call(assistant_message)
            
            if tool_call:
                function_name, arguments = tool_call
                print(f"\n✓ Tool call detected!", file=sys.stderr)
                
                # Call the MCP tool
                try:
                    tool_result = call_mcp_tool(function_name, arguments)
                    
                    # Add messages to conversation
                    enhanced_messages.append({
                        "role": "assistant",
                        "content": assistant_message
                    })
                    enhanced_messages.append({
                        "role": "user",
                        "content": f"TOOL_RESULT: {tool_result}\n\nNow continue with your response using this information. Do not call the tool again."
                    })
                    
                    print(f"[TOOL RESULT] {tool_result}", file=sys.stderr)
                    print("Continuing to next iteration...", file=sys.stderr)
                    continue
                    
                except Exception as e:
                    print(f"[ERROR] Tool call failed: {e}", file=sys.stderr)
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
                print("\n[DONE] No tool call detected, returning response", file=sys.stderr)
                return jsonify(result)
        
        # Max iterations reached
        print(f"\n[WARNING] Max iterations ({max_iterations}) reached", file=sys.stderr)
        return jsonify({"error": "Maximum tool call iterations reached"}), 500
    
    except Exception as e:
        print(f"\n[ERROR] Exception in chat_completions: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Internal error: {str(e)}"}), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({
        "status": "ok",
        "mode": "simple_simulated_tool_calling"
    })

@app.route('/v1/models', methods=['GET'])
def list_models():
    """Proxy models endpoint"""
    try:
        response = requests.get(f"{LLAMAFILE_URL}/v1/models", timeout=5.0)
        return jsonify(response.json())
    except Exception as e:
        return jsonify({"error": f"Cannot reach llamafile: {str(e)}"}), 503

if __name__ == "__main__":
    print("=" * 60)
    print("SIMPLE MCP Bridge Server")
    print("=" * 60)
    print(f"Bridge:    http://127.0.0.1:8081")
    print(f"Llamafile: {LLAMAFILE_URL}")
    print("Mode:      Simple simulated tool calling (Flask + requests)")
    print("=" * 60)
    print()
    
    # Start MCP server (optional for this simplified version)
    # start_mcp_server()
    
    # Run Flask app
    app.run(host="127.0.0.1", port=8081, debug=False, threaded=True)
