"""Enhanced story generator using all three MCP tools"""
from llm_query import query

if __name__ == "__main__":

    response = query("elf adventure quest magic",
                     file=None,  # No RAG for faster response
                     port=8081,
                     prompt=lambda context: f"""Write a creative story opening (100-150 words) about an elf on a quest.

STEP 1: Call get_elf_name(count=1) to get the character's name
STEP 2: Call get_location_description(style='detailed') to get the setting
STEP 3: Call get_random_event() to get a plot event

Then write a compelling story opening that incorporates:
- The character name from the tool
- The location from the tool
- The event from the tool

Make it engaging and in Tolkien's style.""")

    if response:
        output = response.content

        print("\nEnhanced Story with Multiple Tools:")
        print("=" * 60)
        print(output)
        print("=" * 60)
    else:
        print("No response received")
