import logging
import os
import psycopg2
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class FileChangeDetector:
    """
    Detects changes in files to determine if they need processing.
    Uses PostgreSQL to store file state.
    """
    
    def __init__(self):
        # We use the standard PG env vars that are set in the container
        self.db_host = "shared-db" # Service name in docker-compose
        self.db_name = os.getenv("POSTGRES_DB", "postgres")
        self.db_user = os.getenv("POSTGRES_USER", "postgres")
        self.db_password = os.getenv("POSTGRES_PASSWORD", "postgres")
        
    def _get_connection(self):
        return psycopg2.connect(
            host=self.db_host,
            database=self.db_name,
            user=self.db_user,
            password=self.db_password
        )

    def should_process_file(self, connector_id: str, file_metadata: Dict[str, Any]) -> bool:
        """
        Check if a file should be processed based on its metadata.
        Returns True if file is new or modified.
        """
        file_id = file_metadata.get("id")
        file_hash = file_metadata.get("hash")
        
        # If no hash provided by provider, we might rely on modified_time, 
        # but for now let's assume we need either hash or strict modified time.
        # Google Drive gives MD5.
        
        conn = None
        try:
            conn = self._get_connection()
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT hash, last_modified, processed 
                    FROM file_sync_state 
                    WHERE connector_id = %s AND file_id = %s
                    """,
                    (connector_id, file_id)
                )
                row = cur.fetchone()
                
                if not row:
                    # New file
                    return True
                
                stored_hash, stored_time, processed = row
                
                # If not successfully processed previously, retry
                if not processed:
                    return True
                
                # If hash changed
                if file_hash and stored_hash != file_hash:
                    return True
                    
                # If hash missing but logic relies on time (fallback)
                # ...
                
                return False
                
        except Exception as e:
            logger.error(f"Error checking file state for {file_id}: {e}")
            # Fail safe: process it if we can't check? Or skip?
            # Safer to process to avoid data loss, but might loop on errors.
            return True 
        finally:
            if conn:
                conn.close()

    def update_file_state(self, connector_id: str, file_metadata: Dict[str, Any], processed: bool = False):
        """
        Update the state of a file in the DB.
        """
        file_id = file_metadata.get("id")
        file_path = file_metadata.get("name") # Using name as relative path
        file_hash = file_metadata.get("hash")
        last_modified = file_metadata.get("modified_time")
        
        conn = None
        try:
            conn = self._get_connection()
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO file_sync_state 
                    (connector_id, file_id, file_path, last_modified, hash, processed)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (connector_id, file_id) 
                    DO UPDATE SET
                        file_path = EXCLUDED.file_path,
                        last_modified = EXCLUDED.last_modified,
                        hash = EXCLUDED.hash,
                        processed = EXCLUDED.processed
                    """,
                    (connector_id, file_id, file_path, last_modified, file_hash, processed)
                )
            conn.commit()
        except Exception as e:
            logger.error(f"Error updating file state for {file_id}: {e}")
            if conn:
                conn.rollback()
        finally:
            if conn:
                conn.close()
