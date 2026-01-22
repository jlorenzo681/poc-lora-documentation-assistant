from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class BaseConnector(ABC):
    """
    Abstract base class for cloud storage connectors.
    Defines the interface that all connectors must implement.
    """
    
    def __init__(self, connector_id: str, config: Dict[str, Any]):
        """
        Initialize the connector.
        
        Args:
            connector_id: Unique identifier for this connector instance
            config: Configuration dictionary containing credentials and settings
        """
        self.connector_id = connector_id
        self.config = config
        self.name = config.get("name", "Unnamed Connector")
        self.folders = config.get("folders_to_sync", [])
        self.filters = config.get("file_filters", {})
        self.access_token = None
        self.refresh_token = None
    
    @abstractmethod
    def authenticate(self) -> bool:
        """
        Authenticate with the cloud provider.
        Should handle OAuth flow or credential loading.
        
        Returns:
            bool: True if authentication successful
        """
        pass
    
    @abstractmethod
    def list_files(self, folder_id: str, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        List files in a specific folder, optionally since a specific time.
        
        Args:
            folder_id: ID of the folder to list
            since: Only list files modified after this time
            
        Returns:
            List of file metadata dictionaries
        """
        pass
    
    @abstractmethod
    def download_file(self, file_id: str, destination_path: str) -> bool:
        """
        Download a specific file to the local destination.
        
        Args:
            file_id: ID of the file to download
            destination_path: Local path to save the file
            
        Returns:
            bool: True if download successful
        """
        pass
    
    @abstractmethod
    def get_file_metadata(self, file_id: str) -> Dict[str, Any]:
        """
        Get metadata for a specific file.
        
        Args:
            file_id: ID of the file
            
        Returns:
            Dictionary containing file metadata (name, size, modified_time, hash)
        """
        pass
        
    @abstractmethod
    def watch_folder(self, folder_id: str, callback_url: str) -> bool:
        """
        Set up a webhook watch on a folder.
        
        Args:
            folder_id: ID of the folder to watch
            callback_url: Webhook URL to receive notifications
            
        Returns:
            bool: True if watch setup successful
        """
        pass

    def filter_file(self, file_metadata: Dict[str, Any]) -> bool:
        """
        Check if a file matches the configured filters.
        
        Args:
            file_metadata: File metadata dictionary
            
        Returns:
            bool: True if file should be processed
        """
        # Extension filter
        extensions = self.filters.get("extensions", [])
        if extensions:
            filename = file_metadata.get("name", "")
            if not any(filename.lower().endswith(ext.lower()) for ext in extensions):
                return False
                
        # Size filter
        max_size_mb = self.filters.get("max_size_mb")
        if max_size_mb:
            size_bytes = int(file_metadata.get("size", 0))
            if size_bytes > max_size_mb * 1024 * 1024:
                return False
                
        return True
