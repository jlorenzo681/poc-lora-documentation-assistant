import unittest
from unittest.mock import MagicMock, patch
from src.chatbot.sync.file_change_detector import FileChangeDetector

class TestFileChangeDetector(unittest.TestCase):
    
    @patch('src.chatbot.sync.file_change_detector.psycopg2')
    def test_should_process_new_file(self, mock_psycopg2):
        # Mock DB
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_psycopg2.connect.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Mock result: None (file not found)
        mock_cursor.fetchone.return_value = None
        
        detector = FileChangeDetector()
        file_meta = {"id": "f1", "hash": "abc"}
        
        result = detector.should_process_file("c1", file_meta)
        self.assertTrue(result)

    @patch('src.chatbot.sync.file_change_detector.psycopg2')
    def test_should_process_modified_file(self, mock_psycopg2):
        # Mock DB
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_psycopg2.connect.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Mock result: hash="old", time=..., processed=True
        mock_cursor.fetchone.return_value = ("old_hash", "2024-01-01", True)
        
        detector = FileChangeDetector()
        # New hash
        file_meta = {"id": "f1", "hash": "new_hash"}
        
        result = detector.should_process_file("c1", file_meta)
        self.assertTrue(result)

    @patch('src.chatbot.sync.file_change_detector.psycopg2')
    def test_should_skip_unchanged_file(self, mock_psycopg2):
        # Mock DB
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_psycopg2.connect.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Mock result: hash="abc", time=..., processed=True
        mock_cursor.fetchone.return_value = ("abc", "2024-01-01", True)
        
        detector = FileChangeDetector()
        file_meta = {"id": "f1", "hash": "abc"}
        
        result = detector.should_process_file("c1", file_meta)
        self.assertFalse(result)
