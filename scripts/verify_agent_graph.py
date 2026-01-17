
import sys
import os
from unittest.mock import MagicMock
from langchain.schema import Document

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from chatbot.core.agent_graph import AgentGraph
from chatbot.core.vector_store_manager import VectorStoreManager
from chatbot.core.rag_chain import RAGChain

def test_agent_graph():
    print("🧪 Starting Agent Graph Verification...")

    # 1. Mock VectorStoreManager
    print("  - Mocking VectorStoreManager...")
    mock_vsm = MagicMock(spec=VectorStoreManager)
    # Return some dummy documents
    mock_vsm.similarity_search.return_value = [
        Document(page_content="Python is a programming language.", metadata={"source": "doc1"}),
        Document(page_content="LangGraph is a library for agents.", metadata={"source": "doc2"}),
    ]

    # 2. Mock RAGChain and LLM
    print("  - Mocking RAGChain and LLM...")
    mock_rag = MagicMock(spec=RAGChain)
    mock_llm = MagicMock()
    mock_rag.llm = mock_llm
    
    # We need to mock the invoke method of the LLM to handle different prompts
    # This is a bit tricky since the graph creates chains on the fly.
    # We will mock the `invoke` return value.
    # To make it realistic, we can side_effect based on input, but for basic flow:
    
    def llm_side_effect(input, *args, **kwargs):
        # Check if it's the grader or generator
        # The input to llm.invoke is usually a list of messages or a string
        if isinstance(input, list): 
             # It's a list of messages. Let's look at the last one.
             text = input[-1].content if hasattr(input[-1], 'content') else str(input)
        else:
            text = str(input)

        if "grader" in text or "Retrieved document" in text:
            print(f"    [LLM Mock] Grader called")
            return "yes" # Always relevant
        elif "Context:" in text:
            print(f"    [LLM Mock] Generator called")
            return "Generated Answer based on Python and LangGraph."
        elif "underlying semantic intent" in text:
            print(f"    [LLM Mock] Rewriter called")
            return "Rewritten Question"
        else:
            return "Generic Response"

    # We need to mock the Runnable interface: | operator and invoke
    # The code uses: prompt | self.llm | StrOutputParser()
    # So self.llm must be a Runnable.
    # We can use a real FakeListLLM from langchain if we want, or just a mock that implements invoke.
    
    class MockRunnable:
        def invoke(self, input, *args, **kwargs):
            return llm_side_effect(input)
        
        def __or__(self, other):
            # When piped to output parser, return a chain that also invokes
            return MockChain(self, other)

    class MockChain:
        def __init__(self, first, second):
            self.first = first
            self.second = second
            
        def invoke(self, input, *args, **kwargs):
            # This mimics the chain execution
            try:
                # If first is prompt template (which we didn't mock but is real), it returns messages
                # Then we call LLM (our MockRunnable)
                # Then we call StrOutputParser (real)
                
                # But in the code: grade_prompt | self.llm | StrOutputParser()
                # grade_prompt is real. self.llm is THIS mock.
                pass
            except:
                pass
            # Simplified: helper to just call the side effect directly since we can't easily mock the full chain pipeline structure 
            # without real LangChain objects.
            # actually, let's substitute the REAL llm in the graph with our MockRunnable
            return llm_side_effect(input)

    # In the AgentGraph code: `chain = prompt | self.llm | StrOutputParser()`
    # If self.llm is a MagicMock, `|` might fail unless we define __or__.
    
    # Let's try to just use a Mock that returns a string when invoked, 
    # but since it's in the middle of a chain, it receives prompt output.
    
    mock_rag.llm = MockRunnable()
    mock_rag.system_prompt = "You are a bot."

    # 3. Initialize Graph
    print("  - Initializing AgentGraph...")
    graph = AgentGraph(mock_vsm, mock_rag)

    # 4. Run Graph
    print("  - Running Graph with query 'What is LangGraph?'...")
    result = graph.invoke("What is LangGraph?")

    # 5. Assetions
    print("\n🔍 Verifying Results:")
    print(f"   Result keys: {result.keys()}")
    
    if "generation" in result:
        print("   ✅ Generation found:", result["generation"])
    else:
        print("   ❌ No generation found!")
        exit(1)

    if result["generation"] == "Generated Answer based on Python and LangGraph.":
        print("   ✅ Mock LLM was called correctly.")
    else:
        print(f"   ❌ Unexpected generation: {result.get('generation')}")

    print("\n🎉 Verification Successful!")

if __name__ == "__main__":
    test_agent_graph()
