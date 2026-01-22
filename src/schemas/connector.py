from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

class ConnectorBase(BaseModel):
    name: str
    provider: str
    folders_to_sync: List[str] = []
    file_filters: Dict[str, Any] = {}
    sync_strategy: str = "polling" # polling, webhook
    sync_interval: int = 15 # minutes

class ConnectorCreate(ConnectorBase):
    pass

class ConnectorUpdate(BaseModel):
    name: Optional[str] = None
    folders_to_sync: Optional[List[str]] = None
    file_filters: Optional[Dict[str, Any]] = None
    sync_strategy: Optional[str] = None
    sync_interval: Optional[int] = None
    enabled: Optional[bool] = None

class ConnectorResponse(ConnectorBase):
    id: str
    enabled: bool
    created_at: datetime
    last_sync: Optional[datetime] = None
    
    class Config:
        from_attributes = True
