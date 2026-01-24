
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
            # We still need the chain for the LLM and base retrieval
            retriever = self.vector_repo.get_retriever(k=settings.DEFAULT_RETRIEVAL_K)
            
            chain = LoRAChain(
                retriever=retriever,
                llm_provider=self.llm_provider,
                lmstudio_base_url=settings.LM_STUDIO_URL,
                model_name=settings.MLX_MODEL_PATH,
                temperature=settings.DEFAULT_TEMPERATURE
            )
            
            # Use Multi-Step Reasoning Agent
            from ..core.agent_lora import AgentLoRA
            self.chatbot = AgentLoRA(self.vector_repo, chain) # AgentLoRA takes VSM and Chain
            
            return True
        except ValueError:
            # Repository might be empty
            return False
            
    def process_query(self, query: str) -> Dict[str, Any]:
        """Process a user query using the agent."""
        if not self.chatbot:
            raise ValueError("Chatbot not initialized. Load documents first.")
            
        # Agent.invoke() returns dict with keys: documents, question, generation, reasoning_trace
        response = self.chatbot.invoke(query)
        
        # Helper to extract generation from state dict
        answer = response.get("generation", "No answer generated.")
        
        result = {
            "question": query,
            "answer": answer,
            "reasoning": response.get("reasoning_trace", ""), # Capture reasoning
            "context": response.get("documents", []) # Capture context
        }
        
        # Format sources for UI
        if response.get("documents"):
             result["sources"] = self._format_sources(response.get("documents"))
        
        return result
        
    def _format_sources(self, documents: List[Document]) -> List[Dict[str, Any]]:
        sources = []
        for i, doc in enumerate(documents, 1):
            # Extract filename from path
            source_path = doc.metadata.get("source", "Unknown")
            filename = source_path.split("/")[-1] if isinstance(source_path, str) else "Unknown"
            
            # Extract page if available
            page = doc.metadata.get("page", "")
            page_info = f" (Page {page + 1})" if isinstance(page, int) else ""
            
            source_info = {
                "index": i,
                "source": filename,
                "location": f"{filename}{page_info}",
                "content": doc.page_content[:300] + "..." if len(doc.page_content) > 300 else doc.page_content,
                "metadata": doc.metadata
            }
            sources.append(source_info)
        return sources
        
    def reset_conversation(self):
        """Reset conversation history."""
        if self.chatbot:
            self.chatbot.reset_conversation()
