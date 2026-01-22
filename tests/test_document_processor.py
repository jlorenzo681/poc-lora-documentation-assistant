
import pytest
from unittest.mock import MagicMock, patch
from src.chatbot.core.processing.document_processor import DocumentProcessor
from langchain_core.documents import Document

class TestDocumentProcessor:
    
    def test_initialization(self, mock_vector_store_manager, mock_event_bus):
        processor = DocumentProcessor(
            vector_store_manager=mock_vector_store_manager,
            chunk_size=500,
            chunk_overlap=50,
            event_bus=mock_event_bus
        )
        assert processor.chunk_size == 500
        assert processor.chunk_overlap == 50
        assert processor.strategy_type == "recursive"
        
    def test_split_documents(self, mock_vector_store_manager):
        processor = DocumentProcessor(chunk_size=100, chunk_overlap=20)
        docs = [Document(page_content="A" * 200, metadata={"source": "test"})]
        
        chunks = processor.split_documents(docs)
        
        assert len(chunks) > 1
        assert len(chunks[0].page_content) <= 100
        
    @patch("src.chatbot.core.processing.document_processor.LoaderFactory")
    def test_process_document_flow(self, mock_loader_factory, mock_vector_store_manager, mock_event_bus):
        # Setup mocks
        mock_loader = MagicMock()
        mock_loader.load.return_value = [Document(page_content="Test content", metadata={})]
        mock_loader_factory.get_loader.return_value = mock_loader
        
        processor = DocumentProcessor(
            vector_store_manager=mock_vector_store_manager,
            event_bus=mock_event_bus
        )
        
        # Execute
        chunks = processor.process_document("test.txt")
        
        # Verify
        assert len(chunks) > 0
        mock_loader_factory.get_loader.assert_called_once()
        mock_vector_store_manager.add_documents.assert_called_once()
        # Verify events triggered
        assert mock_event_bus.publish.call_count >= 2 # Start and Complete events
