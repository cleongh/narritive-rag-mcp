
from llm_query import query

if __name__ == "__main__":
    # Generate and print the story (no welcome message)
    response = query("very short story of elf painting art creativity Valinor Noldor craftsmanship",
                     file="silmarillion.txt",
                     prompt=lambda context: f"""You are writing a story inspired by J.R.R. Tolkien's legendarium.

Here is some relevant context from The Silmarillion:

{context}

TASK: Write a short creative story about an elf learning to paint. 

IMPORTANT: You MUST use the get_elf_name tool/function to generate an authentic elf name for your character. Call the tool first, then use the returned name in your story.

Draw inspiration from the context provided above, incorporating themes of:
- The Elven love of beauty and art
- The craftsmanship and creativity of the Noldor
- The light of Valinor and the Two Trees

Write the story in a style reminiscent of Tolkien (about 300-400 words).""")

    output = response.content

    # Print the story
    print(output)
