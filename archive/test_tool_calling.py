#!/usr/bin/env python3
"""Test if llamafile supports function calling"""
import httpx
import json

async def test_tool_calling():
    url = "http://localhost:8080/v1/chat/completions"
    
    payload = {
        "model": "local-model",
        "messages": [
            {
                "role": "user",
                "content": "Generate an elf name using the get_elf_name function."
            }
        ],
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": "get_elf_name",
                    "description": "Returns a randomly generated typical elf name",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "count": {
                                "type": "integer",
                                "description": "Number of names to generate",
                                "default": 1
                            }
                        }
                    }
                }
            }
        ],
        "tool_choice": "auto",
        "temperature": 0.7
    }
    
    print("Testing llamafile function calling support...")
    print(f"URL: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}\n")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            result = response.json()
            
            print("Response received:")
            print(json.dumps(result, indent=2))
            
            message = result["choices"][0]["message"]
            print("\n" + "="*60)
            print("Message keys:", message.keys())
            print("Has tool_calls:", "tool_calls" in message)
            
            if "tool_calls" in message:
                print("✓ SUCCESS: Llamafile supports function calling!")
                print(f"Tool calls: {message['tool_calls']}")
            else:
                print("✗ PROBLEM: Llamafile did NOT call the function")
                print(f"Content: {message.get('content', 'No content')}")
                print("\nThis means:")
                print("1. The model might not support function calling")
                print("2. Or the llamafile version doesn't support it")
                print("3. Or the prompt wasn't clear enough")
            
        except Exception as e:
            print(f"✗ Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_tool_calling())
