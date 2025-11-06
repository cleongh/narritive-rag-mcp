
from llm_query import query

if __name__ == "__main__":

    response = query("very short story of elf painting art creativity Valinor Noldor craftsmanship",
                     file="silmarillion.txt",
                     prompt=lambda context: f"""You are writing a story inspired by J.R.R. Tolkien's legendarium.

Here is some relevant context from The Silmarillion:

{context}

Now, write a short creative story about an elf learning to paint. Use the get_elf_name function to generate an elf name for the character, then write the story using that name. 

the get_elf_name function Returns a randomly generated typical elf name from Tolkien's legendarium. Use it, it is mandatory.

Draw inspiration from the context provided above, incorporating themes of:
- The Elven love of beauty and art
- The craftsmanship and creativity of the Noldor
- The light of Valinor and the Two Trees

Write the story in a style reminiscent of Tolkien (about 300-400 words).""")

    output = response.content

    # Print the story
    print("\nStory:")
    print("=" * 60)
    print(output)
    print("=" * 60)
