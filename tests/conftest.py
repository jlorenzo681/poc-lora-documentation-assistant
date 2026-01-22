
import pytest
import os
import sys
from unittest.mock import MagicMock
from langchain_core.documents import Document

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@pytest.fixture
def mock_documents():
    return [
        Document(page_content="Test content 1", metadata={"source": "test.txt", "page": 1}),
        Document(page_content="Test content 2", metadata={"source": "test.txt", "page": 2})
    ]

@pytest.fixture
def mock_event_bus():
    return MagicMock()

@pytest.fixture
def mock_vector_store_manager():
    return MagicMock()
