"""Simple test for the reliable bridge"""
import requests

def test():
    url = "http://127.0.0.1:8081/v1/chat/completions"
    
    payload = {
        "model": "local-model",
        "messages": [
            {"role": "user", "content": "Please generate an elf name using the get_elf_name tool. Then tell me the name you got."}
        ],
        "temperature": 0.7,
        "max_tokens": 300
    }
    
    print("Testing SIMPLE bridge with Gemma...")
    print("Sending request...\n")
    
    try:
        response = requests.post(url, json=payload, timeout=180.0)
        response.raise_for_status()
        result = response.json()
        
        content = result["choices"][0]["message"]["content"]
        
        print("="*60)
        print("Final Response:")
        print("="*60)
        print(content)
        print("="*60)
        
        if "Luis" in content or "Agulló" in content:
            print("\n✓✓✓ SUCCESS! Tool was called and used!")
        else:
            print("\n? Tool may not have been called")
        
    except requests.exceptions.Timeout:
        print("✗ Request timed out")
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test()
