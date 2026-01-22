import unittest
from unittest.mock import MagicMock, patch, mock_open
import datetime
from src.chatbot.connectors.google_drive_connector import GoogleDriveConnector

class TestGoogleDriveConnector(unittest.TestCase):
    
    def setUp(self):
        self.config = {
            "id": "test_connector_1",
            "name": "Test Drive",
            "provider": "google_drive",
            "oauth_credentials": '{"token": "abc", "refresh_token": "def"}',
            "folders_to_sync": ["root"]
        }
        self.connector = GoogleDriveConnector("test_connector_1", self.config)

    @patch('src.chatbot.connectors.google_drive_connector.build')
    @patch('src.chatbot.connectors.google_drive_connector.Credentials')
    def test_authenticate_success(self, mock_creds, mock_build):
        # Mock successful auth
        mock_creds_instance = MagicMock()
        mock_creds_instance.expired = False
        mock_creds.from_authorized_user_info.return_value = mock_creds_instance
        
        # Act
        result = self.connector.authenticate()
        
        # Assert
        self.assertTrue(result)
        self.assertIsNotNone(self.connector.service)
        mock_build.assert_called_once_with('drive', 'v3', credentials=mock_creds_instance)

    @patch('src.chatbot.connectors.google_drive_connector.build')
    def test_list_files(self, mock_build):
        # Setup mock service
        mock_service = MagicMock()
        self.connector.service = mock_service
        self.connector.authenticate = MagicMock(return_value=True) # Skip auth check logic
        
        # Mock API response
        mock_list = mock_service.files().list()
        mock_execute = mock_list.execute
        mock_execute.return_value = {
            "files": [
                {"id": "file1", "name": "doc1.pdf", "modifiedTime": "2024-01-01T10:00:00Z", "size": "100", "md5Checksum": "abc", "mimeType": "application/pdf"}
            ]
        }
        
        # Act
        files = self.connector.list_files("root")
        
        # Assert
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0]["id"], "file1")
        self.assertEqual(files[0]["source"], "google_drive")

    @patch('src.chatbot.connectors.google_drive_connector.MediaIoBaseDownload') 
    def test_download_file(self, mock_downloader):
        # Setup
        mock_service = MagicMock()
        self.connector.service = mock_service
        self.connector.authenticate = MagicMock(return_value=True)
        
        # Mock download chunks
        mock_downloader_instance = MagicMock()
        # First call: (status(progress=0.5), False)
        # Second call: (status(progress=1.0), True)
        mock_downloader.return_value = mock_downloader_instance
        mock_downloader_instance.next_chunk.side_effect = [(MagicMock(progress=lambda: 0.5), False), (MagicMock(progress=lambda: 1.0), True)]
        
        with patch('builtins.open', mock_open()) as mocked_file:
             result = self.connector.download_file("file1", "/tmp/doc1.pdf")
             
        self.assertTrue(result)
