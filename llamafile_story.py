import asyncio
import os
from pathlib import Path
from langchain_openai import ChatOpenAI
from langchain_core.tools import Tool
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, AIMessage
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Global MCP session
mcp_session = None
mcp_read = None
mcp_write = None

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

async def get_elf_name(count: int = 1) -> str:
    """Get elf name(s) from MCP server"""
    global mcp_session
    if mcp_session is None:
        raise RuntimeError("MCP session not initialized")
    
    result = await mcp_session.call_tool("get_elf_name", arguments={"count": count})
    return result.content[0].text # type: ignore

def create_elf_name_tool():
    """Create a LangChain tool that wraps the MCP server"""
    def sync_get_elf_name(count: str = "1") -> str:
        """Returns a randomly generated typical elf name. Use this when you need an elf character name."""
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(get_elf_name(int(count)))
    
    return Tool(
        name="get_elf_name",
        func=sync_get_elf_name,
        description="Returns a randomly generated typical elf name. Input should be the number of names to generate (default 1)."
    )

async def main():
    global mcp_session, mcp_read, mcp_write
    
    # Load Silmarillion for RAG
    print("Loading Silmarillion text for RAG...")
    load_silmarillion_rag()
    
    # Start MCP server
    server_path = Path(__file__).parent / "mcp_server.py"
    server_params = StdioServerParameters(
        command="python",
        args=[str(server_path)],
        env=None
    )
    
    print("Starting MCP server...\n")
    async with stdio_client(server_params) as (read, write):
        mcp_read, mcp_write = read, write
        async with ClientSession(read, write) as session:
            mcp_session = session
            await session.initialize()
            print("MCP server connected\n")
            
            # Configure LangChain to connect to the local llamafile
            llm = ChatOpenAI(
                base_url="http://localhost:8080/v1",
                api_key="not-needed", # type: ignore
                model="local-model",
                temperature=0.7
            )
            
            # Create tool and agent
            tools = [create_elf_name_tool()]
            llm_with_tools = llm.bind_tools(tools)
            
            # Ask for a story with RAG context
            print("Requesting story from llamafile with MCP tool access and RAG...\n")
            
            # Retrieve relevant context from Silmarillion
            query = "elf painting art creativity Valinor"
            context = retrieve_context(query, k=3)
            
            messages = [
                HumanMessage(content=f"""You are writing a story inspired by J.R.R. Tolkien's legendarium.

Here is some relevant context from The Silmarillion:

{context}

Now, write a short creative story about an elf learning to paint. First, use the get_elf_name tool to generate an elf name, then write the story using that name. Draw inspiration from the context provided above, incorporating themes of beauty, creativity, and the Elven love of art.""")
            ]
            
            # First call - LLM should request to use the tool
            response = llm_with_tools.invoke(messages)
            messages.append(response)
            
            # Check if tool was called
            if response.tool_calls:
                print(f"LLM is calling tool: {response.tool_calls[0]['name']}\n")
                # Execute the tool
                loop = asyncio.get_event_loop()
                tool_result = loop.run_until_complete(get_elf_name(int(response.tool_calls[0]['args'].get('count', 1))))
                
                # Add tool result to messages
                from langchain_core.messages import ToolMessage
                messages.append(ToolMessage(
                    content=tool_result,
                    tool_call_id=response.tool_calls[0]['id']
                ))
                
                # Get final response with the story
                final_response = llm_with_tools.invoke(messages)
                output = final_response.content
            else:
                output = response.content
            
            # Print the story
            print("\nStory:")
            print("=" * 60)
            print(output)
            print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
