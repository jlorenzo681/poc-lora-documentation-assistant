"""
Streamlit App for LoRA-Enhanced RAG Chatbot
"""

import streamlit as st
import os
import requests
import json
import time

# Internal imports
# Internal imports
from src.chatbot.services.chat_service import ChatService
from src.chatbot.core.storage.vector_store_manager import VectorStoreManager
from src.chatbot.core.processing.document_processor import DocumentProcessor
from src.chatbot.core.factories.logger_factory import LoggerFactory
from config import settings

# Page Config
st.set_page_config(
    page_title="LoRA RAG Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Session State Initialization ---
def initialize_session_state():
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "chat_service" not in st.session_state:
        st.session_state.chat_service = None
    if "processing" not in st.session_state:
        st.session_state.processing = False
    
    # Initialize Logging once
    if "logger_initialized" not in st.session_state:
        LoggerFactory.setup_global_file_logger()
        st.session_state.logger_initialized = True
    
    # Initialize Managers
    if "vector_store_manager" not in st.session_state:
        st.session_state.vector_store_manager = VectorStoreManager()
        # Try to load existing store if available
        try:
            # Look for default store
            default_path = os.path.join(settings.VECTOR_STORE_PATH, "faiss_index")
            if os.path.exists(settings.VECTOR_STORE_PATH):
                 # Simple attempt to find any index in the directory
                 st.session_state.vector_store_manager.load_vector_store(default_path)
        except Exception:
            pass # It's fine, we'll create one later
    
    if "chat_service" not in st.session_state or st.session_state.chat_service is None:
        st.session_state.chat_service = ChatService(st.session_state.vector_store_manager)

    if "document_processor" not in st.session_state:
        st.session_state.document_processor = DocumentProcessor(
            vector_store_manager=st.session_state.vector_store_manager
        )

# Logger for the app
logger = LoggerFactory.get_logger("streamlit_app")

# --- Init Chatbot ---
def initialize_chatbot():
    """Initialize the chatbot logic using Service."""
    try:
        provider = st.session_state.get("llm_provider", settings.DEFAULT_LLM_PROVIDER)
        st.session_state.chat_service.llm_provider = provider
        
        success = st.session_state.chat_service.initialize_chatbot()
        if success:
           logger.info("Chatbot initialization successful")
        else:
           logger.warning("Chatbot init failed - likely no vector store")
        return success
        
    except Exception as e:
        st.error(f"Failed to init chatbot: {e}")
        return False

# --- UI Layout ---
def main():
    initialize_session_state()
    
    st.title("🤖 LoRA RAG Assistant")
    st.markdown("Retrieval Augmented Generation with LoRA fine-tuning.")

    # Sidebar: Config & Upload
    with st.sidebar:
        st.header("⚙️ Configuration")
        provider = st.selectbox(
            "LLM Provider",
            ["mlx", "lmstudio"],
            index=0 if settings.DEFAULT_LLM_PROVIDER == "mlx" else 1,
            key="llm_provider_selection"
        )
        st.session_state.llm_provider = provider

        st.divider()

        st.header("📚 Knowledge Base")
        
        uploaded_file = st.file_uploader("Upload Document", type=["pdf", "txt", "md"])
        
        if uploaded_file and st.button("Process Document"):
            with st.spinner("Processing..."):
                try:
                    # Save temp
                    os.makedirs("data/documents", exist_ok=True)
                    temp_path = os.path.join("data/documents", uploaded_file.name)
                    with open(temp_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    # Process (Chunk & Embed)
                    # Use a fresh instance of document processor if needed to ensure VSM is linked? 
                    # session_state one is fine.
                    
                    # NOTE: DocumentProcessor.process_document internally calls VSM.add_documents
                    # If VSM has no store, it adds documents and CREATES one. 
                    # We need to make sure VSM.add_documents handles creation if None.
                    # Checking VSM code... it raises Error if None!
                    # I will fix this in VSM next.
                    
                    st.session_state.document_processor.process_document(temp_path)
                    st.toast("✅ Document added to Knowledge Base!", icon="🎉")
                    
                    # Re-init to refresh retriever now that store exists
                    if initialize_chatbot():
                        st.success("Chatbot initialized and ready!")
                    
                    time.sleep(1.5) # Give user time to see toast
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Error processing: {e}")

        st.divider()
        if not st.session_state.chat_service.chatbot:
             # Try to init
             if initialize_chatbot():
                 pass # Success
             else:
                 st.info("⚠️ No Knowledge Base found.\n\nPlease upload a document to initialize the system.")
            
        if st.button("Clear Chat"):
            st.session_state.messages = []
            st.session_state.chat_service.reset_conversation()

    # Chat Interface
    if st.session_state.chat_service.chatbot:
        # Display History
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                if "sources" in msg and msg["sources"]:
                     with st.expander("Sources"):
                         for s in msg["sources"]:
                             st.markdown(f"**{s['index']}**: {s['content']}")

        # User Input
        if prompt := st.chat_input("Ask a question based on your documents..."):
            # Render User Msg
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            # Generate Response
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    try:
                        response = st.session_state.chat_service.process_query(prompt)
                        answer = response.get("answer", "Error generating response.")
                        sources = response.get("sources", [])
                        
                        st.markdown(answer)
                        if sources:
                            with st.status("📚 Referenced Sources", expanded=False):
                                 for s in sources:
                                     st.markdown(f"**{s['index']}. {s.get('location', 'Unknown Source')}**")
                                     st.caption(s['content'])
                                     st.divider()
                        
                        # Save History
                        st.session_state.messages.append({
                            "role": "assistant", 
                            "content": answer,
                            "sources": sources
                        })
                    except Exception as e:
                        st.error(f"Error: {e}")
    else:
        # Welcome / Empty State
        st.info("👋 Welcome! Please upload a PDF or Text file in the sidebar to create your Knowledge Base.")

if __name__ == "__main__":
    main()
