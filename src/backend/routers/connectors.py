from fastapi import APIRouter, HTTPException, Request, BackgroundTasks
from typing import List, Optional
import uuid
import json
import logging
import psycopg2
from datetime import datetime
import os
# from google_auth_oauthlib.flow import Flow # Uncomment when ready to integrate real flow

from src.schemas.connector import ConnectorCreate, ConnectorUpdate, ConnectorResponse
from src.chatbot.connectors.connector_manager import ConnectorManager
# from src.backend.tasks import sync_connector_task # Individual sync task if we had one, or trigger the general one

router = APIRouter(prefix="/api/connectors", tags=["connectors"])
logger = logging.getLogger(__name__)

# DB Helper (Quick and dirty for MVP, should use a proper dependency)
def get_db_connection():
    return psycopg2.connect(
        host="shared-db",
        database=os.getenv("POSTGRES_DB", "postgres"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "postgres")
    )

@router.get("/", response_model=List[ConnectorResponse])
def list_connectors():
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name, provider, folders_to_sync, file_filters, sync_strategy, sync_interval, enabled, created_at, last_sync FROM connectors")
            rows = cur.fetchall()
            connectors = []
            for row in rows:
                connectors.append({
                    "id": row[0],
                    "name": row[1],
                    "provider": row[2],
                    "folders_to_sync": json.loads(row[3]) if row[3] else [],
                    "file_filters": json.loads(row[4]) if row[4] else {},
                    "sync_strategy": row[5],
                    "sync_interval": row[6],
                    "enabled": row[7],
                    "created_at": row[8],
                    "last_sync": row[9]
                })
            return connectors
    finally:
        conn.close()

@router.post("/", response_model=ConnectorResponse)
def create_connector(connector: ConnectorCreate):
    conn = get_db_connection()
    new_id = str(uuid.uuid4())
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO connectors 
                (id, name, provider, folders_to_sync, file_filters, sync_strategy, sync_interval, enabled, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, TRUE, CURRENT_TIMESTAMP)
                RETURNING created_at
                """,
                (
                    new_id, 
                    connector.name, 
                    connector.provider, 
                    json.dumps(connector.folders_to_sync), 
                    json.dumps(connector.file_filters),
                    connector.sync_strategy,
                    connector.sync_interval
                )
            )
            created_at = cur.fetchone()[0]
            conn.commit()
            
            return {
                **connector.dict(),
                "id": new_id,
                "enabled": True,
                "created_at": created_at,
                "last_sync": None
            }
    except Exception as e:
        conn.rollback()
        logger.error(f"Error creating connector: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@router.delete("/{connector_id}")
def delete_connector(connector_id: str):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM connectors WHERE id = %s", (connector_id,))
            if cur.rowcount == 0:
                raise HTTPException(status_code=404, detail="Connector not found")
            conn.commit()
            return {"status": "deleted"}
    finally:
        conn.close()

@router.get("/oauth/authorize/{provider}")
def authorize_connector(provider: str, redirect_uri: str, connector_id: str):
    """
    Start OAuth flow. Returns the authorization URL.
    """
    if provider == "google_drive":
        # Placeholder for real OAuth flow generation
        # flow = Flow.from_client_secrets_file(...)
        # auth_url, _ = flow.authorization_url(...)
        
        # For POC, we might need manual token input or a mock URL
        # Assuming we have client secrets loaded from env/volume
        
        client_id = os.getenv("GOOGLE_CLIENT_ID")
        if not client_id:
             # Fallback for dev if no env var
             logger.warning("GOOGLE_CLIENT_ID not set, using placeholder")
             client_id = "placeholder_client_id"
             
        scope = "https://www.googleapis.com/auth/drive.readonly"
        # We pass connector_id in the 'state' param
        auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code&scope={scope}&access_type=offline&prompt=consent&state={connector_id}"
        
        return {"authorization_url": auth_url}
    
    elif provider == "onedrive":
        client_id = os.getenv("MICROSOFT_CLIENT_ID")
        if not client_id:
            logger.warning("MICROSOFT_CLIENT_ID not set, using placeholder")
            client_id = "placeholder_client_id"
        
        scope = "Files.Read.All offline_access"
        # Microsoft uses different OAuth endpoint
        auth_url = f"https://login.microsoftonline.com/common/oauth2/v2.0/authorize?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code&scope={scope}&state={connector_id}"
        
        return {"authorization_url": auth_url}
    
    raise HTTPException(status_code=400, detail="Unsupported provider")

@router.get("/oauth/callback/{provider}")
def oauth_callback(provider: str, code: str, redirect_uri: str, state: str):
    """
    Exchange code for tokens and save to connector.
    """
    # State is the connector_id
    connector_id = state
    
    # This involves making a request to Google to get tokens
    # Then updating the 'oauth_credentials' field in the DB for the given connector_id
    
    # Mock implementation for now unless we want full flow
    # In a real impl, we'd use flow.fetch_token(code=code)
    
    logger.info(f"Received OAuth code for {provider} connector {connector_id}")
    
    # Simulate saving token
    mock_creds = {
        "token": "mock_access_token_" + code[:5],
        "refresh_token": "mock_refresh_token",
        "token_uri": "https://oauth2.googleapis.com/token",
        "client_id": os.getenv("GOOGLE_CLIENT_ID"),
        "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
        "scopes": ["https://www.googleapis.com/auth/drive.readonly"]
    }
    
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE connectors SET oauth_credentials = %s WHERE id = %s",
                (json.dumps(mock_creds), connector_id)
            )
            if cur.rowcount == 0:
                 raise HTTPException(status_code=404, detail="Connector found for state")
            conn.commit()
        return {"status": "success", "message": "Authenticated successfully. You can close this window."}
    
    elif provider == "onedrive":
        # Exchange code for tokens using MSAL
        connector_id = state
        
        logger.info(f"Received OAuth code for OneDrive connector {connector_id}")
        
        # For now, mock implementation (real implementation would use MSAL)
        mock_creds = {
            "access_token": "mock_access_token_" + code[:5],
            "refresh_token": "mock_refresh_token",
            "token_type": "Bearer",
            "client_id": os.getenv("MICROSOFT_CLIENT_ID"),
            "client_secret": os.getenv("MICROSOFT_CLIENT_SECRET"),
            "scope": ["Files.Read.All"]
        }
        
        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE connectors SET oauth_credentials = %s WHERE id = %s",
                    (json.dumps(mock_creds), connector_id)
                )
                if cur.rowcount == 0:
                    raise HTTPException(status_code=404, detail="Connector not found for state")
                conn.commit()
            return {"status": "success", "message": "Authenticated successfully. You can close this window."}
        finally:
            conn.close()
    finally:
        conn.close()

@router.post("/{connector_id}/sync")
def trigger_sync(connector_id: str, background_tasks: BackgroundTasks):
    """
    Manually trigger a sync for a connector.
    """
    # In a real app, we'd check if it's already running
    # and call the specific sync logic
    
    # Trigger the global sync task or a specific one?
    # Let's trigger the global one for simplicity or we can split it.
    from src.backend.tasks import sync_all_connectors_task
    sync_all_connectors_task.delay()
    
    return {"status": "queued", "message": "Sync started"}
