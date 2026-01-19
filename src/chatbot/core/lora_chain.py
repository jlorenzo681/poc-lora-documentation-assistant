"""
LoRA Chain Module
Implements the LoRA-augmented generation chain with conversation memory.
(Standard RAG Version - Graph Removed)
"""

from typing import Optional, Dict, Any, Literal, List
from langchain_core.documents import Document
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory, ConversationBufferWindowMemory
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
import time
from .event_bus import EventBus, ChatQueryEvent, ChatResponseEvent, ErrorEvent
import config.settings as settings

class LoRAChain:
    """
    Creates and manages LoRA chains with RAG support.
    """

    DEFAULT_SYSTEM_PROMPT = """You are a helpful assistant answering questions based on provided documents.
Use the context provided to answer questions accurately and comprehensively.
"""

    def __init__(
        self,
        retriever,
        llm_provider: Literal["mlx", "lmstudio"] = "mlx",
        lmstudio_base_url: str = "http://localhost:1234/v1",
        model_name: str = "local-model",
        temperature: float = 0.3,
        max_tokens: int = 500,
        system_prompt: Optional[str] = None
    ):
        """
        Initialize the LoRA chain.
        """
        self.retriever = retriever
        self.system_prompt = system_prompt or self.DEFAULT_SYSTEM_PROMPT
        self.llm_provider = llm_provider

        # Initialize LLM based on provider
        # Initialize LLM based on provider
        if llm_provider == "mlx":
            try:
                # Try to load local MLX
                from .mlx_llm import MLXChatModel
                
                model_path = getattr(settings, "MLX_MODEL_PATH", None)
                adapter_path = getattr(settings, "MLX_ADAPTER_PATH", None)
                
                if not model_path:
                    print("⚠ MLX Model Path not set in settings, attempting default")
                
                self.llm = MLXChatModel(
                    model_path=model_path,
                    adapter_path=adapter_path,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                print(f"⚡ Initialized MLX LoRA LLM (Local)")
                print(f"   Model: {model_path}")
                print(f"   Adapters: {adapter_path}")
                
            except ImportError:
                print("⚠ 'mlx_lm' not found. Assuming Docker/Client mode.")
                print("🔄 Connecting to MLX Server on Host...")
                
                from langchain_openai import ChatOpenAI
                # Use MLX_SERVER_BASE_URL from settings, or fallback to localhost if not set
                mlx_base_url = getattr(settings, "MLX_SERVER_BASE_URL", "http://host.docker.internal:8080/v1")
                
                self.llm = ChatOpenAI(
                    base_url=mlx_base_url,
                    api_key="mlx",
                    model=model_name,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    timeout=300.0,
                )
                print(f"📡 Initialized MLX Client for Server: {mlx_base_url}")

        elif llm_provider == "lmstudio":
             from langchain_openai import ChatOpenAI
             self.llm = ChatOpenAI(
                base_url=lmstudio_base_url,
                api_key="lm-studio",
                model=model_name,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=300.0,
            )
             print(f"🤖 Initialized LM Studio LLM: {model_name}")

        else:
            raise ValueError(f"Unsupported LLM provider: {llm_provider}")

    def create_conversational_chain(
        self,
        memory_type: str = "buffer",
        window_size: int = 5
    ) -> Any:
        """Create a conversational LoRA chain."""
        if memory_type == "buffer":
            memory = ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True,
                output_key="answer"
            )
        elif memory_type == "window":
            memory = ConversationBufferWindowMemory(
                memory_key="chat_history",
                return_messages=True,
                output_key="answer",
                k=window_size
            )
        else:
            raise ValueError(f"Unsupported memory type: {memory_type}")

        from langchain.prompts import PromptTemplate

        condense_template = """Given the following conversation and a follow-up question, rephrase the follow-up question to be a standalone question.
        
        Chat History:
        {chat_history}
        
        Follow Up Input: {question}
        
        Standalone question:"""
        condense_question_prompt = PromptTemplate.from_template(condense_template)

        qa_template = """You are a helpful assistant answering questions based STRICTLY on the provided documents.
        
        Instructions:
        1. Use ONLY the Context provided below to answer the question.
        2. Do NOT use outside knowledge or training data.
        3. If the answer is not in the Context, say "I cannot answer this based on the provided documents."
        4. Cite specific details from the documents where possible.
        
        Context:
        {context}
        
        Question: {question}
        
        Answer:"""
        qa_prompt = PromptTemplate.from_template(qa_template)

        conversational_chain = ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            retriever=self.retriever,
            memory=memory,
            return_source_documents=True,
            verbose=False,
            condense_question_prompt=condense_question_prompt,
            combine_docs_chain_kwargs={"prompt": qa_prompt}
        )

        print("✓ Conversational LoRA chain created")
        return conversational_chain


class LoRAChatbot:
    """
    High-level interface for the LoRA chatbot.
    """

    def __init__(
        self,
        chain,
        return_sources: bool = True,
        event_bus: Optional[EventBus] = None,
        event_metadata: Optional[Dict[str, Any]] = None
    ):
        self.chain = chain
        self.return_sources = return_sources
        self.event_bus = event_bus
        self.event_metadata = event_metadata or {}

    def ask(self, question: str) -> Dict[str, Any]:
        try:
            start_time = time.time()
            
            if self.event_bus:
                self.event_bus.publish(ChatQueryEvent(
                    question=question,
                    llm_provider=self.event_metadata.get("llm_provider", "unknown"),
                    model_name=self.event_metadata.get("model_name", "unknown")
                ))

            if hasattr(self.chain, 'memory'):
                response = self.chain({"question": question})
            else:
                response = self.chain.invoke({"input": question})

            result = {
                "question": question,
                "answer": response.get("answer", ""),
            }

            if self.return_sources:
                sources = response.get("source_documents") or response.get("context", [])
                if sources:
                    result["sources"] = self._format_sources(sources)

            if self.event_bus:
                self.event_bus.publish(ChatResponseEvent(
                    question=question,
                    answer=result["answer"],
                    source_count=len(result.get("sources", [])),
                    duration_seconds=time.time() - start_time
                ))

            return result

        except Exception as e:
            if self.event_bus:
                self.event_bus.publish(ErrorEvent(
                    error_type=type(e).__name__,
                    message=str(e),
                    context={"question": question}
                ))
            import traceback
            error_details = traceback.format_exc()
            print(f"Error in LoRA chain: {error_details}")
            return {
                "question": question,
                "answer": f"Error processing question: {str(e)}\n\nDetails: {type(e).__name__}",
                "error": True
            }
            
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
        if hasattr(self.chain, 'memory'):
            self.chain.memory.clear()
            print("✓ Conversation history cleared")
        else:
            print("⚠ This chain doesn't have conversation memory")

if __name__ == "__main__":
    print("LoRA Chain module initialized successfully!")
