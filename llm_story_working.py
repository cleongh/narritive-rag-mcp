from llm_query import query

if __name__ == "__main__":

    response = query("elf painting art Valinor",  # Shorter query
                     file="silmarillion.txt",
                     port=8081,
                     timeout=10.0,  # Increased timeout
                     prompt=lambda context: f"""Write a short story about an elf learning to paint. Context from Tolkien:

{context[:500]}  

STEP 1: Call get_elf_name tool: TOOL_CALL: get_elf_name(count=1)
STEP 2: Write 150-word story using the name, inspired by Tolkien's elves and their love of beauty.""")

    if response:
        output = response.content

        # Print the story
        print("\nStory:")
        print("=" * 60)
        print(output)
        print("=" * 60)
    else:
        print("No response received")
