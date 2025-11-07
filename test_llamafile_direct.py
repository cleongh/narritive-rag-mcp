"""Test llamafile directly"""
import httpx

url = "http://localhost:8080/v1/chat/completions"

payload = {
    "model": "local-model",
    "messages": [
        {"role": "user", "content": "Say hello in exactly 5 words."}
    ],
    "temperature": 0.7,
    "max_tokens": 20
}

print("Testing DeepSeek directly (no bridge)...")

try:
    response = httpx.post(url, json=payload, timeout=30.0)
    result = response.json()
    
    content = result["choices"][0]["message"]["content"]
    print(f"\nResponse: {content}\n")
    print("✓ DeepSeek is working!")
    
except httpx.ReadTimeout:
    print("✗ Timeout - DeepSeek is too slow or not responding")
except Exception as e:
    print(f"✗ Error: {e}")
