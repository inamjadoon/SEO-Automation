from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, AnyHttpUrl


class SiteCreate(BaseModel):
    id: str
    domain: AnyHttpUrl
    api_credentials: Optional[Dict[str, Any]] = None


class SiteResponse(BaseModel):
    id: str
    domain: AnyHttpUrl
    detected_platform: str
    api_credentials: Optional[Dict[str, Any]] = None

    indexnow_key: Optional[str] = None
    indexnow_key_location: Optional[str] = None

    created_at: datetime
    updated_at: datetime
    last_synced_at: Optional[datetime] = None
    sync_status: str

class Config:
        from_attributes = True

