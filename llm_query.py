# ./32-google_gemma-3-12b-it-Q4_K_M.llamafile --server --nobrowser -ngl 15

import asyncio
import sys
from pathlib import Path
try:
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import HumanMessage
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain_community.vectorstores import FAISS
    from langchain_community.embeddings import HuggingFaceEmbeddings
    import httpx
    _HAS_LANGCHAIN = True
except Exception:  # pragma: no cover - optional dev dependency
    _HAS_LANGCHAIN = False
    # Define lightweight stand-ins to avoid NameErrors; real functionality
    # will not be available when langchain packages are missing.
    ChatOpenAI = None
    HumanMessage = None
    RecursiveCharacterTextSplitter = None
    FAISS = None
    HuggingFaceEmbeddings = None
    httpx = None

# Global RAG components
vector_store = None


def get_welcome_message() -> str:
    """
    Devuelve un mensaje de bienvenida multilínea y legible.
    Centraliza el texto para que sea fácil de modificar.
    """
    return (
        "Bienvenido a llm_query!\n\n"
        "Esta herramienta consulta un LLM a través del puente MCP y, opcionalmente, usa RAG para contexto.\n\n"
        "Para suprimir este mensaje, pasa show_welcome=False.\n\n"
        "--------------------------------------------------\n"
    )


def load_rag(file):
    """Load the Silmarillion text and create a vector store for RAG"""
    global vector_store

    silmarillion_path = Path(__file__).parent / file  # "silmarillion.txt"

    # Read the text file
    with open(silmarillion_path, 'r', encoding='utf-8') as f:
        text = f.read()

    # If langchain libs are not installed, skip RAG creation
    if not _HAS_LANGCHAIN:
        print("RAG disabled: langchain libraries not installed", file=sys.stderr)
        return

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

    print(f"Loaded file {f} with {len(chunks)} chunks")


def retrieve_context(query: str, k: int = 3) -> str:
    """Retrieve relevant context from RAG"""
    if vector_store is None:
        return ""

    docs = vector_store.similarity_search(query, k=k)
    # Limit context size to avoid overwhelming the LLM
    context = "\n\n".join([doc.page_content[:400] for doc in docs])
    return context[:1500]  # Max 1500 chars of context


async def main(prompt, query, llm_ip, port, timeout, file, show_welcome: bool = True):
    # Mostrar mensaje de bienvenida si está habilitado
    if show_welcome:
        print(get_welcome_message())

    # Check if MCP bridge is running (only when real httpx/langchain available)
    if _HAS_LANGCHAIN and httpx is not None:
        print("Checking MCP bridge connection...")
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"http://{llm_ip}:{port}/v1/models", timeout=timeout)
                print(f"MCP bridge is running: {response.status_code}\n")
        except Exception as e:
            print(f"ERROR: Cannot connect to MCP bridge at http://{llm_ip}:{port}")
            print(f"Make sure to start the bridge first: uv run python mcp_bridge.py")
            print(f"Error: {e}")
            return
    else:
        print("Skipping MCP bridge connectivity check (langchain/httpx not installed)")

    # Load Silmarillion for RAG
    if file is not None:
        print(f"Loading text in file {file} for RAG...")
        load_rag(file)

    # If langchain and real ChatOpenAI are available, use them. Otherwise
    # provide a simple mock response for testing the example client.
    if _HAS_LANGCHAIN and ChatOpenAI is not None:
        # Configure LangChain to connect to the MCP bridge (not directly to llamafile)
        llm = ChatOpenAI(
            base_url=f"http://{llm_ip}:{port}/v1",
            api_key="not-needed",  # type: ignore
            model="local-model",
            temperature=0.7,
            max_tokens=600,  # Limit response length for faster generation
            max_retries=2,
            request_timeout=300.0  # type: ignore
        )

        print("Requesting answer from llamafile via MCP bridge...\n")

        # Retrieve relevant context from Silmarillion (reduced k for less context)
        context = retrieve_context(query, k=2)

        prompt = prompt(context)

        messages = [HumanMessage(content=prompt)]

        # Get response from LLM (via MCP bridge)
        response = llm.invoke(messages)
        return response
    else:
        # Mock response for environments without language-model dependencies.
        class MockResp:
            def __init__(self, content):
                self.content = content

        context = "" if file is None else f"(RAG disabled in mock; file={file})"
        mock_text = (
            "[MOCK RESPONSE] This is a mock short Tolkien-style story. "
            "Install langchain and start the MCP bridge to get real responses.\n\n"
            "Story:\nEldar of gentle skill took brush to light, and in Valinor's soft glow began a painting that echoed the Two Trees."
        )
        return MockResp(mock_text)
    


def query(query, prompt=lambda context: "", llm_ip="localhost", port=8081, timeout=5.0, file=None, show_welcome: bool = True):
    return asyncio.run(main(prompt, query, llm_ip, port, timeout, file, show_welcome=show_welcome))

