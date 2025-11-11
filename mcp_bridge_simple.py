"""Simple, reliable MCP bridge with simulated tool calling"""
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional
# Flask is imported lazily inside create_bridge_app so the module can be imported
# even when Flask is not installed. This makes the library usable without the
# web framework for programmatic use.
try:
    import requests
except Exception:  # pragma: no cover - optional dependency
    requests = None


# Llamafile backend
LLAMAFILE_URL = "http://localhost:8080"

# MCP server process (optional subprocess starter kept for compatibility)
mcp_process = None

def start_mcp_server_subprocess():
    """Start the MCP server as a subprocess using the local mcp_server.py
    (kept for backward compatibility with older workflows).
    """
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

def call_mcp_tool_stub(tool_name: str, arguments: dict) -> str:
    """Stub function for MCP tool calls used when no tool executor is provided.

    This function simply returns a diagnostic string and should be replaced
    by an actual MCP tool executor (for example, calling `start_mcp_server` /
    talking to stdio, or sending requests to a running MCP process).
    """
    print(f"[MCP-STUB] No tool executor configured. Called: {tool_name} with {arguments}", file=sys.stderr)
    return f"MCP_STUB_RESULT: {tool_name}({arguments})"


# Pluggable MCP tool executor. Callers may assign a different callable that
# accepts (tool_name: str, arguments: dict) -> str. By default we use the stub.
mcp_tool_executor = call_mcp_tool_stub

def create_system_prompt(available_tools: list[str] | None = None) -> str:
    """Return the system prompt teaching the LLM how to call tools.

    If `available_tools` is provided, list them in the prompt. Otherwise the
    prompt will mention that tools are available without enumerating them.
    """
    tools_section = "Available tools are provided by the MCP bridge."
    if available_tools:
        tools_lines = [f"- {t}" for t in available_tools]
        tools_section = "Available tools:\n" + "\n".join(tools_lines)

    return f"""You are a helpful assistant with access to tools. When you need to use a tool, you MUST output it in this EXACT format on a line by itself:

TOOL_CALL: function_name(arg1=value1, arg2=value2)

{tools_section}

IMPORTANT: 
- Output the TOOL_CALL on its own line
- After you output a TOOL_CALL, STOP and wait for the result
- When you receive a TOOL_RESULT, use it naturally in your response
- Do NOT invent or hallucinate tool results - always use the provided TOOL_RESULT

Example:
User: Generate an elf name and a location
Assistant: TOOL_CALL: get_elf_name(count=1)
[System provides result]
Assistant: TOOL_CALL: get_location_description(style='detailed')
[System provides result]
Assistant: Here's your character: [use the provided name] in [use the provided location]
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

def create_bridge_app(llamafile_url: str = LLAMAFILE_URL, mcp_executor=None):
    """Factory that creates and returns a Flask app wired to the bridge handlers.

    This avoids importing Flask at module import time; callers who want to run
    the HTTP bridge can call this function.
    """
    from flask import Flask, request, jsonify

    app = Flask(__name__)

    # Use provided executor or the module-level default
    executor = mcp_executor or mcp_tool_executor

    @app.route('/v1/chat/completions', methods=['POST'])
    def chat_completions():
        """Handle chat completions with simulated tool calling"""
        try:
            body = request.get_json()
            messages = body.get("messages", [])

            # Add system prompt (do not enumerate tools here to keep it generic)
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
                        f"{llamafile_url}/v1/chat/completions",
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

                    # Call the MCP tool (pluggable executor)
                    try:
                        tool_result = executor(function_name, arguments)
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

                    # Add messages to conversation with the tool result
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
            response = requests.get(f"{llamafile_url}/v1/models", timeout=5.0)
            return jsonify(response.json())
        except Exception as e:
            return jsonify({"error": f"Cannot reach llamafile: {str(e)}"}), 503

    return app


def run_bridge(host: str = "127.0.0.1", port: int = 8081, llamafile_url: str = LLAMAFILE_URL, mcp_executor=None):
    """Convenience helper to create and run the Flask bridge app.

    Keeps the module usable as a library: callers can import `create_bridge_app`
    or call `run_bridge` to run the HTTP bridge.
    """
    app = create_bridge_app(llamafile_url=llamafile_url, mcp_executor=mcp_executor)
    app.run(host=host, port=port, debug=False, threaded=True)
