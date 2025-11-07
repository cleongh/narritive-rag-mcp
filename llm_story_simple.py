from llm_query import query

if __name__ == "__main__":

    response = query("simple elf story",
                     file=None,  # No RAG for now - keep it simple
                     port=8081,
                     prompt=lambda context: f"""Write a very short story (100-150 words) about an elf painter.

STEP 1: First call the get_elf_name tool.
        Output exactly: TOOL_CALL: get_elf_name(count=1)
        
STEP 2: Use the name you receive to write a brief story about an elf who loves to paint.

Keep it short and simple.""")

    if response:
        output = response.content

        print("\nStory:")
        print("=" * 60)
        print(output)
        print("=" * 60)
    else:
        print("No response received")
