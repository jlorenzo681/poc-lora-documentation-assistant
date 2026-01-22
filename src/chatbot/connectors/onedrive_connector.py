from typing import List, Dict, Any, Optional
import os
import logging
from datetime import datetime, timezone, timedelta
import json
import requests

from msal import ConfidentialClientApplication
from .base_connector import BaseConnector

logger = logging.getLogger(__name__)

class OneDriveConnector(BaseConnector):
    """
    Connector for Microsoft OneDrive using Microsoft Graph API.
    """
    
    SCOPES = ['https://graph.microsoft.com/Files.Read.All']
    GRAPH_API_ENDPOINT = 'https://graph.microsoft.com/v1.0'
    
    def __init__(self, connector_id: str, config: Dict[str, Any]):
        super().__init__(connector_id, config)
        self.access_token = None
        
    def authenticate(self) -> bool:
        """
        Authenticate with Microsoft Graph using stored OAuth credentials.
        """
        try:
            creds_data = self.config.get("oauth_credentials")
            if not creds_data:
                logger.error(f"No credentials found for connector {self.connector_id}")
                return False
                
            # If creds are a JSON string, parse them
            if isinstance(creds_data, str):
                creds_data = json.loads(creds_data)
            
            # Extract tokens
            self.access_token = creds_data.get("access_token")
            refresh_token = creds_data.get("refresh_token")
            
            # Check if token is expired (simplified - in production check expiry time)
            # For now, we'll try to use the token and refresh if needed
            
            if not self.access_token and refresh_token:
                # Refresh token
                client_id = creds_data.get("client_id") or os.getenv("MICROSOFT_CLIENT_ID")
                client_secret = creds_data.get("client_secret") or os.getenv("MICROSOFT_CLIENT_SECRET")
                
                if not client_id or not client_secret:
                    logger.error("Missing Microsoft client credentials")
                    return False
                
                app = ConfidentialClientApplication(
                    client_id,
                    authority="https://login.microsoftonline.com/common",
                    client_credential=client_secret
                )
                
                result = app.acquire_token_by_refresh_token(refresh_token, scopes=self.SCOPES)
                
                if "access_token" in result:
                    self.access_token = result["access_token"]
                    # TODO: Update stored credentials in DB
                    logger.info(f"Refreshed access token for connector {self.connector_id}")
                else:
                    logger.error(f"Failed to refresh token: {result.get('error_description')}")
                    return False
            
            logger.info(f"Successfully authenticated with OneDrive (Connector: {self.connector_id})")
            return True
            
        except Exception as e:
            logger.error(f"Authentication failed for connector {self.connector_id}: {e}")
            return False

    def _get_headers(self) -> Dict[str, str]:
        """Get authorization headers for API requests."""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

    def list_files(self, folder_id: str, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        List files in a OneDrive folder using delta queries for efficient sync.
        """
        if not self.access_token:
            if not self.authenticate():
                return []

        files = []
        
        # Construct endpoint
        # For root: /me/drive/root/children
        # For specific folder: /me/drive/items/{folder_id}/children
        if folder_id == "root":
            endpoint = f"{self.GRAPH_API_ENDPOINT}/me/drive/root/children"
        else:
            endpoint = f"{self.GRAPH_API_ENDPOINT}/me/drive/items/{folder_id}/children"
        
        # Add delta query if we want incremental sync
        # For now, we'll use regular listing and filter by modifiedDateTime
        
        try:
            next_link = endpoint
            
            while next_link:
                response = requests.get(next_link, headers=self._get_headers())
                
                if response.status_code != 200:
                    logger.error(f"Error listing files: {response.status_code} - {response.text}")
                    break
                
                data = response.json()
                
                for item in data.get("value", []):
                    # Skip folders (we only want files)
                    if "folder" in item:
                        continue
                    
                    # Parse modified time
                    modified_time = item.get("lastModifiedDateTime")
                    
                    # Filter by since if provided
                    if since and modified_time:
                        item_time = datetime.fromisoformat(modified_time.replace('Z', '+00:00'))
                        if item_time <= since:
                            continue
                    
                    # Normalize metadata
                    files.append({
                        "id": item.get("id"),
                        "name": item.get("name"),
                        "modified_time": modified_time,
                        "size": int(item.get("size", 0)),
                        "hash": item.get("file", {}).get("hashes", {}).get("sha1Hash"),  # OneDrive uses SHA1
                        "mime_type": item.get("file", {}).get("mimeType"),
                        "connector_id": self.connector_id,
                        "source": "onedrive"
                    })
                
                # Check for pagination
                next_link = data.get("@odata.nextLink")
            
            logger.info(f"Found {len(files)} files in folder {folder_id}")
            return files
            
        except Exception as e:
            logger.error(f"Error listing files for connector {self.connector_id}: {e}")
            return []

    def download_file(self, file_id: str, destination_path: str) -> bool:
        """
        Download a file from OneDrive.
        """
        if not self.access_token:
            if not self.authenticate():
                return False
                
        try:
            # Get download URL
            endpoint = f"{self.GRAPH_API_ENDPOINT}/me/drive/items/{file_id}/content"
            
            response = requests.get(endpoint, headers=self._get_headers(), stream=True)
            
            if response.status_code != 200:
                logger.error(f"Error downloading file {file_id}: {response.status_code}")
                return False
            
            # Write to file
            with open(destination_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"Successfully downloaded file {file_id} to {destination_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error downloading file {file_id}: {e}")
            # Clean up partial download
            if os.path.exists(destination_path):
                os.remove(destination_path)
            return False

    def get_file_metadata(self, file_id: str) -> Dict[str, Any]:
        """Get single file metadata."""
        if not self.access_token:
            if not self.authenticate():
                return {}
                
        try:
            endpoint = f"{self.GRAPH_API_ENDPOINT}/me/drive/items/{file_id}"
            
            response = requests.get(endpoint, headers=self._get_headers())
            
            if response.status_code != 200:
                logger.error(f"Error getting metadata for {file_id}: {response.status_code}")
                return {}
            
            item = response.json()
            
            return {
                "id": item.get("id"),
                "name": item.get("name"),
                "modified_time": item.get("lastModifiedDateTime"),
                "size": int(item.get("size", 0)),
                "hash": item.get("file", {}).get("hashes", {}).get("sha1Hash"),
                "mime_type": item.get("file", {}).get("mimeType")
            }
        except Exception as e:
            logger.error(f"Error getting metadata for {file_id}: {e}")
            return {}

    def watch_folder(self, folder_id: str, callback_url: str) -> bool:
        """
        Set up a webhook subscription for a folder.
        Note: Requires a public HTTPS endpoint and proper validation.
        """
        if not self.access_token:
            if not self.authenticate():
                return False
                
        try:
            endpoint = f"{self.GRAPH_API_ENDPOINT}/subscriptions"
            
            # Construct resource path
            if folder_id == "root":
                resource = "/me/drive/root"
            else:
                resource = f"/me/drive/items/{folder_id}"
            
            subscription = {
                "changeType": "updated",
                "notificationUrl": callback_url,
                "resource": resource,
                "expirationDateTime": (datetime.now(timezone.utc).replace(microsecond=0) + 
                                      timedelta(days=3)).isoformat(),  # Max 3 days for OneDrive
                "clientState": self.connector_id  # For validation
            }
            
            response = requests.post(
                endpoint,
                headers=self._get_headers(),
                json=subscription
            )
            
            if response.status_code == 201:
                logger.info(f"Successfully set up watch on folder {folder_id}")
                return True
            else:
                logger.error(f"Error watching folder {folder_id}: {response.status_code} - {response.text}")
                return False
            
        except Exception as e:
            logger.error(f"Error watching folder {folder_id}: {e}")
            return False
