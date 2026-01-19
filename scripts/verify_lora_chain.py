
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")

from src.chatbot.core.lora_chain import LoRAChain
from src.chatbot.core.vector_store_manager import VectorStoreManager
import config.settings as settings

def test_lora_chain():
    print("🧪 Verifying LoRA Chain Integration...")
    
    # Mock settings for MLX
    print(f"   Model Path: {getattr(settings, 'MLX_MODEL_PATH', 'Not set')}")
    print(f"   Adapter Path: {getattr(settings, 'MLX_ADAPTER_PATH', 'Not set')}")
    
    try:
        # Mock Retriever
        class MockRetriever:
            def invoke(self, query):
                return []
            def get_relevant_documents(self, query):
                return []

        retriever = MockRetriever()
        
        # Initialize Chain
        print("   Initializing LoRAChain with MLX provider...")
        chain = LoRAChain(
            retriever=retriever,
            llm_provider="mlx",
            temperature=0.1
        )
        
        print("✅ LoRAChain initialized successfully.")
        
        # Check LLM type
        if hasattr(chain.llm, "_llm_type"):
            print(f"   LLM Type: {chain.llm._llm_type}")
            
        # Basic Invoke Test (Optional, requires loaded model which takes time)
        # We skip actual inference to avoid 30s load time in this quick check,
        # unless user specifically wants to wait.
        print("✅ Verification Passed: Class structure and initialization logic are correct.")
        
    except Exception as e:
        print(f"❌ Verification Failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    test_lora_chain()
