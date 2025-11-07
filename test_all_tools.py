"""Test all three MCP tools working together"""
import requests

def test():
    url = "http://127.0.0.1:8081/v1/chat/completions"
    
    payload = {
        "model": "local-model",
        "messages": [
            {
                "role": "user", 
                "content": """Create a very short story setup (50 words):
1. First call get_elf_name to get a character name
2. Then call get_location_description with style='detailed' to get a setting
3. Then call get_random_event to get a plot point
4. Finally, write a brief story setup using all three elements"""
            }
        ],
        "temperature": 0.7,
        "max_tokens": 400
    }
    
    print("Testing ALL THREE tools with Gemma...")
    print("=" * 60)
    print("Requesting: Character + Location + Event\n")
    
    try:
        response = requests.post(url, json=payload, timeout=180.0)
        response.raise_for_status()
        result = response.json()
        
        content = result["choices"][0]["message"]["content"]
        
        print("="*60)
        print("Final Story Setup:")
        print("="*60)
        print(content)
        print("="*60)
        
        # Check if all tools were used
        tools_found = []
        if "Luis" in content or "Agulló" in content:
            tools_found.append("✓ get_elf_name")
        if any(loc in content for loc in ["Lothlórien", "Rivendell", "Valinor", "Mirkwood", "Gondolin", "Númenor", "Doriath", "Grey Havens"]):
            tools_found.append("✓ get_location_description")
        if any(event in content for event in ["discovers", "choose", "visitor", "artifact", "phenomenon", "fear", "secret", "challenge"]):
            tools_found.append("✓ get_random_event")
        
        print("\nTools Used:")
        for tool in tools_found:
            print(f"  {tool}")
        
        if len(tools_found) == 3:
            print("\n🎉 SUCCESS! All three tools were called and used!")
        else:
            print(f"\n⚠️  Only {len(tools_found)}/3 tools detected in output")
        
    except requests.exceptions.Timeout:
        print("✗ Request timed out")
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test()
