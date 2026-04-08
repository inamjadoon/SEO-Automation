from pydantic import BaseModel
from typing import Dict, Any, Optional


class EntityCreate(BaseModel):
    entity_type: str
    entity_id: str
    name: str
    attributes: Dict[str, Any]
    brand: Optional[str] = None
    author: Optional[str] = None


class EntityResponse(BaseModel):
    id: str
    entity_type: str
    entity_id: str
    name: str
    attributes: Dict[str, Any]
    jsonld_path: str | None = None
    status: str
