import unittest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from src.backend.main import app
import json

client = TestClient(app)

class TestConnectorRouter(unittest.TestCase):
    
    @patch('src.backend.routers.connectors.get_db_connection')
    def test_list_connectors(self, mock_get_conn):
        # Mock DB
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Return 1 row
        mock_cursor.fetchall.return_value = [
            ("c1", "My Drive", "google_drive", '["root"]', '{}', "polling", 15, True, "2024-01-01", None)
        ]
        
        response = client.get("/api/connectors/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["id"], "c1")
        self.assertEqual(data[0]["folders_to_sync"], ["root"])

    @patch('src.backend.routers.connectors.get_db_connection')
    def test_create_connector(self, mock_get_conn):
        # Mock DB
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Mock fetchone for created_at
        mock_cursor.fetchone.return_value = ["2024-01-01"]
        
        payload = {
            "name": "New Drive",
            "provider": "google_drive",
            "folders_to_sync": ["root"],
            "sync_strategy": "polling",
            "sync_interval": 15
        }
        
        response = client.post("/api/connectors/", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["name"], "New Drive")
        self.assertTrue(data["enabled"])

    def test_oauth_authorize(self):
        response = client.get(
            "/api/connectors/oauth/authorize/google_drive",
            params={"redirect_uri": "http://callback", "connector_id": "c123"}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        url = data["authorization_url"]
        self.assertIn("client_id=", url)
        self.assertIn("state=c123", url) # Verify state parameter

    @patch('src.backend.routers.connectors.get_db_connection')
    def test_oauth_callback(self, mock_get_conn):
        # Mock DB
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Mock update rowcount
        mock_cursor.rowcount = 1
        
        response = client.get(
            "/api/connectors/oauth/callback/google_drive",
            params={"code": "auth_code", "redirect_uri": "http://cb", "state": "c123"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "success")
        
        # Verify DB update called
        mock_cursor.execute.assert_called()
        args = mock_cursor.execute.call_args[0]
        self.assertIn("UPDATE connectors", args[0])
        self.assertEqual(args[1][1], "c123") # connector_id
