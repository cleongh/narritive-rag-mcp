from llm_query import query

if __name__ == "__main__":

    response = query("very short story of elf painting art creativity Valinor Noldor craftsmanship",
                     file="silmarillion.txt",
                     port=8081,  # Use the simulated bridge
                     prompt=lambda context: f"""You are writing a story inspired by J.R.R. Tolkien's legendarium.

Here is some relevant context from The Silmarillion:

{context}

TASK: Write a short creative story (300-400 words) about an elf learning to paint.

STEP 1: First, you MUST call the get_elf_name function to generate an authentic elf name.
        Output: TOOL_CALL: get_elf_name(count=1)

STEP 2: After you receive the name, write the story using that name.

The story should incorporate themes of:
- The Elven love of beauty and art
- The craftsmanship and creativity of the Noldor
- The light of Valinor and the Two Trees

Write in a style reminiscent of Tolkien.""")

    output = response.content

    # Print the story
    print("\nStory:")
    print("=" * 60)
    print(output)
    print("=" * 60)
