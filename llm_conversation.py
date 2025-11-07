#!/usr/bin/env python3
"""
Conversational narrative generation with MCP-guided structure.

The LLM engages in a conversation with the MCP to build a well-structured story.
The MCP provides narrative structure guidance (introduction, development, conclusion)
and the LLM can reflect and iterate as needed.
"""

import sys
import httpx
from llm_query import query as llm_query_raw, retrieve_context

def check_bridge_status(ip="localhost", port=8081):
    """Check if the MCP bridge is running"""
    try:
        response = httpx.get(f"http://{ip}:{port}/health", timeout=5.0)
        return response.status_code == 200
    except Exception:
        return False

def llm_query(prompt_text):
    """Wrapper around llm_query that simplifies the interface"""
    response = llm_query_raw(
        query="",
        prompt=lambda context: prompt_text,
        port=8081,
        timeout=180.0,
        file=None
    )
    return response.content if hasattr(response, 'content') else str(response)

# Narrative structure phases
NARRATIVE_PHASES = [
    {
        "name": "introduction",
        "prompt": """You are beginning a story. Use the available tools to:
1. Get a character name using get_elf_name()
2. Get a location using get_location_description(style='detailed')
3. Set the scene in 100-150 words

Write ONLY the introduction. End with a clear transition point.""",
        "max_words": 150
    },
    {
        "name": "development",
        "prompt": """Continue the story from where we left off. Use the available tools to:
1. Introduce a complication using get_random_event()
2. Develop the plot in 150-200 words
3. Build tension and conflict

Write ONLY the development section. End with the story at its peak.""",
        "max_words": 200
    },
    {
        "name": "conclusion",
        "prompt": """Conclude the story. You may use tools if needed for final elements.
1. Resolve the conflict
2. Provide closure in 100-150 words
3. End with a satisfying conclusion

Write ONLY the conclusion.""",
        "max_words": 150
    }
]

def conversation_turn(phase_info, previous_text, rag_context):
    """
    Execute one conversation turn with the MCP.
    
    Args:
        phase_info: Dictionary with phase name, prompt, and constraints
        previous_text: Text generated in previous phases
        rag_context: RAG context from The Silmarillion
        
    Returns:
        Generated text for this phase
    """
    print(f"\n{'='*60}")
    print(f"PHASE: {phase_info['name'].upper()}")
    print(f"{'='*60}")
    
    # Build the full prompt with context
    full_prompt = f"""You are writing a story in the style of J.R.R. Tolkien.

RAG Context from The Silmarillion:
{rag_context}

"""
    
    if previous_text:
        full_prompt += f"""Story so far:
{previous_text}

"""
    
    full_prompt += f"""{phase_info['prompt']}

Target length: {phase_info['max_words']} words maximum.
Style: Tolkien-esque, poetic, mythological.
"""
    
    print(f"\nPrompt for this phase:")
    print(f"{phase_info['prompt'][:200]}...")
    print(f"\nGenerating {phase_info['name']}...")
    
    # Query the LLM through the bridge
    response = llm_query(full_prompt)  # RAG already included
    
    print(f"\n--- {phase_info['name'].upper()} OUTPUT ---")
    print(response)
    print(f"--- END {phase_info['name'].upper()} ---")
    
    return response

def reflect_and_refine(text, phase_name):
    """
    Optional: Have the LLM reflect on generated text and suggest improvements.
    
    Args:
        text: The generated text to reflect on
        phase_name: Name of the phase being reflected on
        
    Returns:
        Reflection and suggestions
    """
    reflection_prompt = f"""Review this {phase_name} section of a story:

{text}

Provide brief feedback (2-3 sentences):
1. Does it fit the narrative structure?
2. Are the tools used effectively?
3. Any improvements needed?

Keep it concise."""
    
    print(f"\n🤔 Reflecting on {phase_name}...")
    reflection = llm_query(reflection_prompt)
    print(f"\nReflection: {reflection}")
    
    return reflection

def build_narrative_conversation():
    """
    Main function: Build a complete narrative through conversational turns.
    Each phase is a separate conversation with the MCP guiding structure.
    """
    print("="*60)
    print("CONVERSATIONAL NARRATIVE GENERATION")
    print("LLM + MCP + RAG Working Together")
    print("="*60)
    
    # Check bridge connectivity
    print("\n1. Checking MCP bridge status...")
    if not check_bridge_status():
        print("❌ Bridge is not responding. Please start it first:")
        print("   uv run python mcp_bridge_simple.py")
        return
    print("✓ Bridge is ready")
    
    # Load RAG context once (we'll reuse it)
    print("\n2. Loading RAG context from The Silmarillion...")
    # Get context about storytelling, creation, and narrative
    rag_query = "storytelling, creation of the world, Ainulindalë, music, narrative, beginnings"
    rag_context = retrieve_context(rag_query, k=3)
    print(f"✓ Retrieved {len(rag_context)} characters of context")
    
    # Store the complete narrative
    complete_story = []
    
    # Execute each narrative phase as a conversation turn
    print("\n3. Beginning narrative construction...")
    print("   The LLM will converse with the MCP through multiple turns")
    
    for i, phase in enumerate(NARRATIVE_PHASES):
        # Get the story so far
        previous_text = "\n\n".join(complete_story)
        
        # Execute this conversation turn
        phase_text = conversation_turn(phase, previous_text, rag_context)
        
        # Optional: Reflect on the generated text
        if i < len(NARRATIVE_PHASES) - 1:  # Don't reflect on the last phase
            user_input = input(f"\nReflect on {phase['name']}? (y/N): ").strip().lower()
            if user_input == 'y':
                reflect_and_refine(phase_text, phase['name'])
                
                # Optional: Regenerate if needed
                regen = input("Regenerate this phase? (y/N): ").strip().lower()
                if regen == 'y':
                    print(f"\n🔄 Regenerating {phase['name']}...")
                    phase_text = conversation_turn(phase, previous_text, rag_context)
        
        # Add to complete story
        complete_story.append(phase_text)
        
        # Small pause between phases
        if i < len(NARRATIVE_PHASES) - 1:
            print(f"\n{'·'*60}")
            print(f"Phase {i+1}/{len(NARRATIVE_PHASES)} complete. Continuing...")
            print(f"{'·'*60}")
    
    # Display the complete narrative
    print("\n" + "="*60)
    print("COMPLETE NARRATIVE")
    print("="*60)
    
    for i, (phase, text) in enumerate(zip(NARRATIVE_PHASES, complete_story)):
        print(f"\n[{phase['name'].upper()}]")
        print(text)
        if i < len(NARRATIVE_PHASES) - 1:
            print(f"\n{'─'*60}")
    
    print("\n" + "="*60)
    print("NARRATIVE COMPLETE")
    print("="*60)
    
    # Final statistics
    total_words = sum(len(text.split()) for text in complete_story)
    print(f"\nTotal words: {total_words}")
    print(f"Phases: {len(NARRATIVE_PHASES)}")
    print(f"Average words per phase: {total_words // len(NARRATIVE_PHASES)}")
    
    # Save to file
    output_file = "generated_narrative.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("NARRATIVE GENERATED BY LLM + MCP + RAG\n")
        f.write("="*60 + "\n\n")
        for phase, text in zip(NARRATIVE_PHASES, complete_story):
            f.write(f"[{phase['name'].upper()}]\n")
            f.write(text)
            f.write("\n\n" + "─"*60 + "\n\n")
    
    print(f"\n✓ Saved to: {output_file}")

def main():
    """Entry point for the conversational narrative generator."""
    try:
        build_narrative_conversation()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
