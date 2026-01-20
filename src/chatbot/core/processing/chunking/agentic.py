"""
Agentic Chunking Strategy
Uses an LLM to determine semantic chunk boundaries.
"""

from typing import List, Optional, Any
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import PromptTemplate
import logging
from .base import BaseChunker
from ...factories.logger_factory import LoggerFactory

logger = LoggerFactory.get_logger("document_processor")

# Default Prompt for Agentic Decision
AGENTIC_CHUNK_DECISION_PROMPT = """You are a smart document processing agent. Your task is to decide if a new piece of text belongs to the SAME semantic chunk as the previous context, or if it starts a NEW topic/chunk.

Current Chunk Topic/Context:
"{current_context}"

New Text to Evaluate:
"{new_text}"

Decision Rules:
1. If the New Text continues the same thought, argument, or topic, return 'MERGE'.
2. If the New Text starts a new section, topic, or distinct thought, return 'SPLIT'.
3. If the Current Chunk is getting too long (over ~500 words) and there is a natural break, return 'SPLIT'.

Return ONLY 'MERGE' or 'SPLIT'. No other text.
"""

class AgenticChunker(BaseChunker):
    """
    Splits documents by using an LLM to evaluate semantic shifts.
    """

    def __init__(
        self, 
        llm: Any,
        initial_chunk_size: int = 200, # Granularity for initial breakdown (e.g. sentences/paragraphs)
        max_chunk_size: int = 2000, # Safety limit
        prompt_template: Optional[str] = None
    ):
        self.llm = llm
        self.max_chunk_size = max_chunk_size
        
        # We need a primary splitter to break text into atomic units (sentences/paragraphs) first
        # Recursive with small chunk size acts as a decent sentence/paragraph splitter
        self.atomic_splitter = RecursiveCharacterTextSplitter(
            chunk_size=initial_chunk_size,
            chunk_overlap=0,
            separators=["\n\n", "\n", ". ", "!", "?", " "]
        )
        
        template = prompt_template or AGENTIC_CHUNK_DECISION_PROMPT
        self.prompt = PromptTemplate.from_template(template)

    def _get_llm_decision(self, current_context: str, new_text: str) -> str:
        """
        Ask LLM whether to MERGE or SPLIT.
        """
        try:
            # Create chain
            chain = self.prompt | self.llm
            result = chain.invoke({
                "current_context": current_context[-500:], # Pass recent context only to save tokens
                "new_text": new_text
            })
            
            # Allow for object based access if needed (depending on LLM wrapper)
            content = result.content if hasattr(result, 'content') else str(result)
            decision = content.strip().upper()
            
            if "MERGE" in decision: return "MERGE"
            if "SPLIT" in decision: return "SPLIT"
            return "MERGE" # Default to merge if ambiguous
            
        except Exception as e:
            print(f"⚠ Agentic Chunker LLM Error: {e}. Defaulting to MERGE.")
            return "MERGE"

    def split_documents(self, documents: List[Document]) -> List[Document]:
        final_chunks = []

        for doc in documents:
            # 1. Split into atomic units
            atomic_docs = self.atomic_splitter.split_documents([doc])
            
            if not atomic_docs:
                continue

            current_chunk_text = ""
            current_chunk_metadata = doc.metadata.copy()
            
            # Start with first unit
            current_chunk_text = atomic_docs[0].page_content
            
            for i in range(1, len(atomic_docs)):
                next_unit = atomic_docs[i].page_content
                
                # Safety check: if current chunk is huge, force split
                if len(current_chunk_text) > self.max_chunk_size:
                    final_chunks.append(Document(page_content=current_chunk_text, metadata=current_chunk_metadata))
                    current_chunk_text = next_unit
                    continue

                # Ask Agent
                decision = self._get_llm_decision(current_chunk_text, next_unit)
                
                if decision == "MERGE":
                    current_chunk_text += "\n" + next_unit
                else:
                    logger.info(f"Agentic Split Decision: SPLIT (Context len: {len(current_chunk_text)})")
                    # Commit current chunk
                    final_chunks.append(Document(page_content=current_chunk_text, metadata=current_chunk_metadata))
                    # Start new chunk
                    current_chunk_text = next_unit
            
            # Add the last remaining chunk
            if current_chunk_text:
                final_chunks.append(Document(page_content=current_chunk_text, metadata=current_chunk_metadata))
                
        logger.info(f"✨ Agentic Chunking: Converted {len(documents)} docs into {len(final_chunks)} semantic chunks.")
        return final_chunks
