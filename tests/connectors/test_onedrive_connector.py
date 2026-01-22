import unittest
from unittest.mock import MagicMock, patch, mock_open
from src.chatbot.connectors.onedrive_connector import OneDriveConnector

class TestOneDriveConnector(unittest.TestCase):
    
    def setUp(self):
        self.config = {
            "id": "test_onedrive_1",
            "name": "Test OneDrive",
            "provider": "onedrive",
            "oauth_credentials": '{"access_token": "test_token", "refresh_token": "refresh"}',
            "folders_to_sync": ["root"]
        }
        self.connector = OneDriveConnector("test_onedrive_1", self.config)

    def test_authenticate_success(self):
        # Test with existing access token
        result = self.connector.authenticate()
        
        self.assertTrue(result)
        self.assertEqual(self.connector.access_token, "test_token")

    @patch('src.chatbot.connectors.onedrive_connector.requests.get')
    def test_list_files(self, mock_get):
        # Setup
        self.connector.access_token = "test_token"
        
        # Mock API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "value": [
                {
                    "id": "file1",
                    "name": "doc1.pdf",
                    "lastModifiedDateTime": "2024-01-01T10:00:00Z",
                    "size": 100,
                    "file": {
                        "hashes": {"sha1Hash": "abc123"},
                        "mimeType": "application/pdf"
                    }
                }
            ]
        }
        mock_get.return_value = mock_response
        
        # Act
        files = self.connector.list_files("root")
        
        # Assert
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0]["id"], "file1")
        self.assertEqual(files[0]["source"], "onedrive")
        self.assertEqual(files[0]["hash"], "abc123")

    @patch('src.chatbot.connectors.onedrive_connector.requests.get')
    def test_download_file(self, mock_get):
        # Setup
        self.connector.access_token = "test_token"
        
        # Mock download response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.iter_content = lambda chunk_size: [b"test content"]
        mock_get.return_value = mock_response
        
        with patch('builtins.open', mock_open()) as mocked_file:
            result = self.connector.download_file("file1", "/tmp/doc1.pdf")
            
        self.assertTrue(result)

    def test_connector_manager_instantiation(self):
        from src.chatbot.connectors.connector_manager import ConnectorManager
        
        manager = ConnectorManager()
        config = {
            "id": "onedrive_1",
            "provider": "onedrive",
            "name": "My OneDrive"
        }
        
        connector = manager._instantiate_connector(config)
        self.assertIsInstance(connector, OneDriveConnector)
        self.assertEqual(connector.connector_id, "onedrive_1")
