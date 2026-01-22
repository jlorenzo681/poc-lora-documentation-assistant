
from typing import Optional, Dict, Any, List
from langchain_core.documents import Document
from ..core.lora_chain import LoRAChain, LoRAChatbot
from ..repositories.vector_repository import VectorRepository
from config import settings

class ChatService:
    """
    Service layer for Chatbot operations.
    Decouples business logic from UI.
    """
    
    def __init__(self, vector_repository: VectorRepository, llm_provider: str = settings.DEFAULT_LLM_PROVIDER):
        self.vector_repo = vector_repository
        self.llm_provider = llm_provider
        self.chatbot: Optional[LoRAChatbot] = None
        
    def initialize_chatbot(self) -> bool:
        """Initialize the RAG chatbot using the repository."""
        try:
            retriever = self.vector_repo.get_retriever(k=settings.DEFAULT_RETRIEVAL_K)
            
            chain = LoRAChain(
                retriever=retriever,
                llm_provider=self.llm_provider,
                lmstudio_base_url=settings.LM_STUDIO_URL,
                model_name=settings.MLX_MODEL_PATH,
                temperature=settings.DEFAULT_TEMPERATURE
            )
            
            conversational_chain = chain.create_conversational_chain()
            
            self.chatbot = LoRAChatbot(
                chain=conversational_chain,
                return_sources=True,
                langfuse_handler=chain.langfuse_handler
            )
            return True
        except ValueError:
            # Repository might be empty
            return False
            
    def process_query(self, query: str) -> Dict[str, Any]:
        """Process a user query."""
        if not self.chatbot:
            raise ValueError("Chatbot not initialized. Load documents first.")
            
        return self.chatbot.ask(query)
        
    def reset_conversation(self):
        """Reset conversation history."""
        if self.chatbot:
            self.chatbot.reset_conversation()
