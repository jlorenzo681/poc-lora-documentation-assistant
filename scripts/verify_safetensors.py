import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from chatbot.core.vector_store_manager import VectorStoreManager

def verify_safetensors():
    print("Verifying SafeTensors enforcement...")
    
    try:
        # Initialize VectorStoreManager which initializes HuggingFaceEmbeddings
        vsm = VectorStoreManager()
        
        # Access the underlying SentenceTransformer model
        # HuggingFaceEmbeddings wraps SentenceTransformer in .client
        if hasattr(vsm.embeddings, 'client'):
            # This is how we might check internally, but just initialization without error 
            # and printing the confirmation above is good for a start.
            # We can also check if the model loaded is indeed using safetensors if possible
            # but usually 'use_safetensors=True' passed to creating it creates the constraint.
            
            print("✓ VectorStoreManager initialized successfully")
            print(f"✓ Model Name: {vsm.embeddings.model_name}")
            print(f"✓ Model Kwargs: {vsm.embeddings.model_kwargs}")
            
            if vsm.embeddings.model_kwargs.get('use_safetensors') is True:
                print("✓ use_safetensors is set to True")
            else:
                 print("❌ use_safetensors is NOT set to True")
                 sys.exit(1)
                 
        else:
             print("⚠ Could not access underlying client to verify kwargs, but initialization succeeded.")

    except Exception as e:
        print(f"❌ Failed to initialize VectorStoreManager: {e}")
        sys.exit(1)

if __name__ == "__main__":
    verify_safetensors()
