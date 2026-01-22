
import pytest
from unittest.mock import MagicMock, patch
from src.chatbot.services.chat_service import ChatService
from config import settings

class TestChatService:
    
    @pytest.fixture
    def mock_repo(self):
        return MagicMock()

    @patch("src.chatbot.services.chat_service.LoRAChain")
    @patch("src.chatbot.services.chat_service.LoRAChatbot")
    def test_initialize_chatbot_success(self, mock_chatbot_cls, mock_chain_cls, mock_repo):
        # Setup
        service = ChatService(vector_repository=mock_repo)
        mock_repo.get_retriever.return_value = MagicMock()
        mock_chain_instance = MagicMock()
        mock_chain_cls.return_value = mock_chain_instance
        
        # Execute
        success = service.initialize_chatbot()
        
        # Verify
        assert success is True
        assert service.chatbot is not None
        mock_repo.get_retriever.assert_called_once()
        mock_chain_cls.assert_called_once()
        mock_chatbot_cls.assert_called_once()

    def test_initialize_chatbot_failure_no_store(self, mock_repo):
        # Setup
        service = ChatService(vector_repository=mock_repo)
        mock_repo.get_retriever.side_effect = ValueError("No store")
        
        # Execute
        success = service.initialize_chatbot()
        
        # Verify
        assert success is False
        assert service.chatbot is None

    def test_process_query_without_init(self, mock_repo):
        service = ChatService(vector_repository=mock_repo)
        with pytest.raises(ValueError, match="Chatbot not initialized"):
            service.process_query("test")
