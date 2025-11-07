#!/usr/bin/env python3
"""Quick test for DeepSeek function calling"""
import httpx
import json

def test_sync():
    url = "http://localhost:8080/v1/chat/completions"
    
    payload = {
        "model": "local-model",
        "messages": [
            {"role": "user", "content": "Call the get_elf_name function with count=1"}
        ],
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": "get_elf_name",
                    "description": "Returns a randomly generated elf name",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "count": {"type": "integer", "default": 1}
                        }
                    }
                }
            }
        ],
        "tool_choice": "auto",
        "temperature": 0.1,
        "max_tokens": 50
    }
    
    print("Testing DeepSeek function calling (quick test)...")
    
    try:
        response = httpx.post(url, json=payload, timeout=20.0)
        result = response.json()
        
        message = result["choices"][0]["message"]
        
        print("\n" + "="*60)
        print(f"Response keys: {list(message.keys())}")
        
        if "tool_calls" in message and message["tool_calls"]:
            print("\n✓✓✓ SUCCESS! DeepSeek SUPPORTS function calling! ✓✓✓")
            print(f"\nTool call: {json.dumps(message['tool_calls'][0], indent=2)}")
            print("\nYou can use the ORIGINAL mcp_bridge.py!")
            return True
        else:
            print("\n✗ DeepSeek does NOT support function calling")
            print(f"Content: {message.get('content', '')[:200]}")
            print("\nUse mcp_bridge_simulated.py instead")
            return False
            
    except httpx.ReadTimeout:
        print("✗ Timeout - trying to generate response")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    return False

if __name__ == "__main__":
    test_sync()
