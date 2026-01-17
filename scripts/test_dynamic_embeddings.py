
import sys
import os
from langchain.docstore.document import Document

# Add project root and src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

# Mock settings just for test if needed, or rely on actual settings
# os.environ["EMBEDDING_MODEL_EN"] = "nomic-embed-text"
# os.environ["EMBEDDING_MODEL_MULTILINGUAL"] = "bge-m3"

try:
    from chatbot.core.vector_store_manager import VectorStoreManager
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)

def test_dynamic_embedding_selection():
    print("🧪 Testing Dynamic Embedding Selection...")
    
    # Initialize VectorStoreManager
    vsm = VectorStoreManager()
    
    if not vsm.ft_model:
        print("❌ FastText model not loaded. Please run download_models.py")
        return

    # Test cases
    test_cases = [
        {
            "text": "This is a simple English document about artificial intelligence.",
            "expected_lang": "en",
            "expected_model": "nomic-embed-text" 
        },
        {
            "text": "Este es un documento simple en español sobre inteligencia artificial.",
            "expected_lang": "es",
            "expected_model": "bge-m3"
        },
        {
            "text": "Ceci est un document simple en français sur l'intelligence artificielle.",
            "expected_lang": "fr",
            "expected_model": "bge-m3" # Should fallback to multilingual
        }
    ]

    for case in test_cases:
        print(f"\nEvaluating text: '{case['text'][:50]}...'")
        
        # Test Language Detection
        detected_lang = vsm.detect_language(case['text'])
        print(f"  Detected Language: {detected_lang}")
        
        if detected_lang != case['expected_lang']:
            print(f"  ❌ Mismatch! Expected: {case['expected_lang']}, Got: {detected_lang}")
        else:
            print(f"  ✓ Language detection correct")

        # Test Embedding Selection Logic (not full load to avoid Ollama dependency in pure python test if possible, but VSM loads it)
        # We check specific logic in _get_embeddings_for_language or by creating a dummy doc
        
        try:
            embeddings = vsm._get_embeddings_for_language(detected_lang)
            print(f"  Selected Model: {embeddings.model}")
            
            if embeddings.model == case['expected_model']:
                print("  ✓ Correct model selected")
            else:
                print(f"  ❌ Incorrect model! Expected: {case['expected_model']}, Got: {embeddings.model}")
                
        except Exception as e:
            print(f"  ❌ Error initializing embeddings: {e}")

    print("\n✓ Verification Logic Complete")

if __name__ == "__main__":
    test_dynamic_embedding_selection()
