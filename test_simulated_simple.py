"""Simple test of the simulated bridge"""
import asyncio
import httpx

async def test():
    url = "http://127.0.0.1:8081/v1/chat/completions"
    
    payload = {
        "model": "local-model",
        "messages": [
            {"role": "user", "content": "Generate an elf name. First call the get_elf_name tool, then tell me the name."}
        ],
        "temperature": 0.7,
        "max_tokens": 300
    }
    
    print("Testing simulated bridge with DeepSeek...")
    print("Sending request...\n")
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            response = await client.post(url, json=payload)
            result = response.json()
            
            content = result["choices"][0]["message"]["content"]
            
            print("="*60)
            print("Response:")
            print("="*60)
            print(content)
            print("="*60)
            
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())
