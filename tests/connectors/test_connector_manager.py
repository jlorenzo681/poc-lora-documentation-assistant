import unittest
from src.chatbot.connectors.connector_manager import ConnectorManager
from src.chatbot.connectors.google_drive_connector import GoogleDriveConnector

class TestConnectorManager(unittest.TestCase):
    
    def test_instantiate_google_drive(self):
        manager = ConnectorManager()
        config = {
            "id": "gdrive_1",
            "provider": "google_drive", 
            "name": "My Drive"
        }
        
        connector = manager._instantiate_connector(config)
        self.assertIsInstance(connector, GoogleDriveConnector)
        self.assertEqual(connector.connector_id, "gdrive_1")

    def test_instantiate_unknown(self):
        manager = ConnectorManager()
        config = {
            "id": "unknown_1",
            "provider": "unknown_provider"
        }
        
        connector = manager._instantiate_connector(config)
        self.assertIsNone(connector)
