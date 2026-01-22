from typing import List, Dict, Any, Optional
import os
import io
import logging
from datetime import datetime, timezone
import json

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.auth.transport.requests import Request

from .base_connector import BaseConnector

logger = logging.getLogger(__name__)

class GoogleDriveConnector(BaseConnector):
    """
    Connector for Google Drive using Drive API v3.
    """
    
    SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
    
    def __init__(self, connector_id: str, config: Dict[str, Any]):
        super().__init__(connector_id, config)
        self.service = None
        
    def authenticate(self) -> bool:
        """
        Authenticate with Google Drive using stored OAuth credentials.
        """
        try:
            creds_data = self.config.get("oauth_credentials")
            if not creds_data:
                logger.error(f"No credentials found for connector {self.connector_id}")
                return False
                
            # If creds are a JSON string, parse them
            if isinstance(creds_data, str):
                creds_data = json.loads(creds_data)
                
            creds = Credentials.from_authorized_user_info(creds_data, self.SCOPES)
            
            # Refresh if expired
            if creds and creds.expired and creds.refresh_token:
                logger.info(f"Refreshing access token for connector {self.connector_id}")
                creds.refresh(Request())
                
                # TODO: Update stored credentials in DB with new token
                # This would typically happen via a callback or by updating the config object 
                # which gets persisted later.
                
            self.service = build('drive', 'v3', credentials=creds)
            logger.info(f"Successfully authenticated with Google Drive (Connector: {self.connector_id})")
            return True
            
        except Exception as e:
            logger.error(f"Authentication failed for connector {self.connector_id}: {e}")
            return False

    def list_files(self, folder_id: str, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        List files in a Google Drive folder.
        """
        if not self.service:
            if not self.authenticate():
                return []

        files = []
        page_token = None
        
        # Build query
        # - Inside the specific folder
        # - Not trashed
        query = f"'{folder_id}' in parents and trashed = false"
        
        # - Modified since
        if since:
            # Format: YYYY-MM-DDTHH:MM:SS
            # Ensure UTC
            if since.tzinfo is None:
                since = since.replace(tzinfo=timezone.utc)
            time_str = since.isoformat().replace("+00:00", "Z") # generic ISO handle
            query += f" and modifiedTime > '{time_str}'"
            
        # - MimeType filter (skip folders in the list if we only want files, 
        #   but maybe we want to recurse later? For now, let's just get files)
        #   Actually, let's filter purely by the extension filter in the base class later
        #   But we can exclude Google native docs if we can't export them easily, 
        #   or handle export logic. for now, standard files.
        query += " and mimeType != 'application/vnd.google-apps.folder'"

        try:
            while True:
                response = self.service.files().list(
                    q=query,
                    spaces='drive',
                    fields='nextPageToken, files(id, name, modifiedTime, size, md5Checksum, mimeType)',
                    pageToken=page_token,
                    pageSize=100
                ).execute()
                
                for file in response.get('files', []):
                    # Normalize metadata
                    files.append({
                        "id": file.get("id"),
                        "name": file.get("name"),
                        "modified_time": file.get("modifiedTime"), # ISO string
                        "size": int(file.get("size", 0)),
                        "hash": file.get("md5Checksum"),
                        "mime_type": file.get("mimeType"),
                        "connector_id": self.connector_id,
                        "source": "google_drive"
                    })
                    
                page_token = response.get('nextPageToken', None)
                if page_token is None:
                    break
                    
            logger.info(f"Found {len(files)} files in folder {folder_id}")
            return files
            
        except Exception as e:
            logger.error(f"Error listing files for connector {self.connector_id}: {e}")
            return []

    def download_file(self, file_id: str, destination_path: str) -> bool:
        """
        Download a file from Google Drive.
        """
        if not self.service:
            if not self.authenticate():
                return False
                
        try:
            request = self.service.files().get_media(fileId=file_id)
            fh = io.FileIO(destination_path, 'wb')
            downloader = MediaIoBaseDownload(fh, request)
            
            done = False
            while done is False:
                status, done = downloader.next_chunk()
                # logger.debug(f"Download {int(status.progress() * 100)}%.")
                
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
        if not self.service:
            if not self.authenticate():
                return {}
                
        try:
            file = self.service.files().get(
                fileId=file_id,
                fields='id, name, modifiedTime, size, md5Checksum, mimeType'
            ).execute()
            
            return {
                "id": file.get("id"),
                "name": file.get("name"),
                "modified_time": file.get("modifiedTime"),
                "size": int(file.get("size", 0)),
                "hash": file.get("md5Checksum"),
                "mime_type": file.get("mimeType")
            }
        except Exception as e:
            logger.error(f"Error getting metadata for {file_id}: {e}")
            return {}

    def watch_folder(self, folder_id: str, callback_url: str) -> bool:
        """
        Set up a push notification channel for a folder.
        Note: This requires a domain verification and public HTTPS URL.
        """
        if not self.service:
            if not self.authenticate():
                return False
                
        try:
            body = {
                "id": f"channel-{self.connector_id}-{folder_id}-{int(datetime.now().timestamp())}",
                "type": "web_hook",
                "address": callback_url
            }
            
            self.service.files().watch(
                fileId=folder_id,
                body=body
            ).execute()
            
            logger.info(f"Successfully set up watch on folder {folder_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error watching folder {folder_id}: {e}")
            return False
