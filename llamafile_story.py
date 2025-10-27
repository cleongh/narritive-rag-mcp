# ./32-google_gemma-3-12b-it-Q4_K_M.llamafile --server --nobrowser -ngl 15

import asyncio
from pathlib import Path
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
import httpx

# Global RAG components
vector_store = None

def load_silmarillion_rag():
    """Load the Silmarillion text and create a vector store for RAG"""
    global vector_store
    
    silmarillion_path = Path(__file__).parent / "silmarillion.txt"
    
    # Read the text file
    with open(silmarillion_path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    # Split into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
    )
    chunks = text_splitter.split_text(text)
    
    # Create embeddings and vector store
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vector_store = FAISS.from_texts(chunks, embeddings)
    
    print(f"Loaded Silmarillion with {len(chunks)} chunks")

def retrieve_context(query: str, k: int = 3) -> str:
    """Retrieve relevant context from the Silmarillion"""
    if vector_store is None:
        return ""
    
    docs = vector_store.similarity_search(query, k=k)
    context = "\n\n".join([doc.page_content for doc in docs])
    return context

async def main():
    # Check if MCP bridge is running
    print("Checking MCP bridge connection...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8081/v1/models", timeout=5.0)
            print(f"MCP bridge is running: {response.status_code}\n")
    except Exception as e:
        print(f"ERROR: Cannot connect to MCP bridge at http://localhost:8081")
        print(f"Make sure to start the bridge first: uv run python mcp_bridge.py")
        print(f"Error: {e}")
        return
    
    # Load Silmarillion for RAG
    print("Loading Silmarillion text for RAG...")
    load_silmarillion_rag()
    
    # Configure LangChain to connect to the MCP bridge (not directly to llamafile)
    llm = ChatOpenAI(
        base_url="http://localhost:8081/v1",
        api_key="not-needed", # type: ignore
        model="local-model",
        temperature=0.7,
        max_retries=2,
        request_timeout=300.0 # type: ignore
    )
    
    print("Requesting story from llamafile via MCP bridge...\n")
    
    # Retrieve relevant context from Silmarillion
    query = "elf painting art creativity Valinor Noldor craftsmanship"
    context = retrieve_context(query, k=3)
    
    prompt = f"""You are writing a story inspired by J.R.R. Tolkien's legendarium.

Here is some relevant context from The Silmarillion:

{context}

Now, write a short creative story about an elf learning to paint. Use the get_elf_name function to generate an elf name for the character, then write the story using that name. 

Draw inspiration from the context provided above, incorporating themes of:
- The Elven love of beauty and art
- The craftsmanship and creativity of the Noldor
- The light of Valinor and the Two Trees

Write the story in a style reminiscent of Tolkien (about 300-400 words)."""

    messages = [HumanMessage(content=prompt)]
    
    # Get response from LLM (via MCP bridge)
    response = llm.invoke(messages)
    output = response.content
    
    # Print the story
    print("\nStory:")
    print("=" * 60)
    print(output)
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
