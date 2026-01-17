
import sys
import os
import time
from langchain_core.documents import Document
import config.settings as settings

# Fix paths
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.chatbot.core.graph_store_manager import GraphStoreManager

def test_graph_rag():
    print("🕸️ Testing GraphRAG Integration...")
    
    # 1. Initialize Manager
    print("1. Initializing GraphStoreManager...")
    gsm = GraphStoreManager()
    
    if not gsm.graph:
        print("❌ Failed to connect to Neo4j. Ensure container is running.")
        sys.exit(1)
        
    print("✓ Connected to Neo4j")
    
    # 2. Add sample document
    print("\n2. Extracting Graph Data (this might take time)...")
    sample_text = """
    Alice works at TechCorp as a generic Software Engineer.
    TechCorp is located in San Francisco.
    Bob is Alice's manager.
    """
    
    doc = Document(page_content=sample_text, metadata={"source": "test_script"})
    
    gsm.add_documents_to_graph([doc])
    
    # 3. Query Graph
    print("\n3. Querying Graph...")
    queries = [
        "Who works at TechCorp?",
        "Where is TechCorp located?",
        "Who is Alice's manager?"
    ]
    
    for q in queries:
        print(f"\nQuery: {q}")
        result = gsm.query_graph(q)
        print(f"Result: {result}")
        if not result or "I don't know" in result:
            print("⚠ Weak or no result from graph.")
        else:
            print("✓ Got answer from graph")

    print("\n✓ GraphRAG Test Complete")

if __name__ == "__main__":
    test_graph_rag()
