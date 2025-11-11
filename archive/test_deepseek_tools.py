#!/usr/bin/env python3
"""Test if DeepSeek supports function calling"""
import httpx
import json
import asyncio

async def test_deepseek_tool_calling():
    # DeepSeek runs on port 8080 when you start it
    url = "http://localhost:8080/v1/chat/completions"
    
    payload = {
        "model": "local-model",
        "messages": [
            {
                "role": "user",
                "content": "Please generate an elf name using the get_elf_name function. Just call the function, don't make up a name."
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
        "temperature": 0.1,
        "max_tokens": 200
    }
    
    print("Testing DeepSeek-R1-Distill-Qwen function calling support...")
    print(f"URL: {url}\n")
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            result = response.json()
            
            message = result["choices"][0]["message"]
            print("="*60)
            print("Response Message:")
            print(f"Keys: {list(message.keys())}")
            print(f"\nContent: {message.get('content', 'No content')}")
            
            if "tool_calls" in message and message["tool_calls"]:
                print("\n✓ SUCCESS! DeepSeek SUPPORTS native function calling!")
                print(f"\nTool calls: {json.dumps(message['tool_calls'], indent=2)}")
                return True
            else:
                print("\n✗ DeepSeek does NOT support native function calling")
                print("You should use the simulated bridge instead")
                return False
            
        except httpx.ReadTimeout:
            print("✗ Request timed out - model might not support this")
            return False
        except Exception as e:
            print(f"✗ Error: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    print("IMPORTANT: Make sure DeepSeek is running first!")
    print("Start it with: ~/programas/DeepSeek-R1-Distill-Qwen-14B-Q4_K_M.llamafile --server --nobrowser -ngl 32 --gpu nvidia")
    print("\n")
    
    asyncio.run(test_deepseek_tool_calling())
