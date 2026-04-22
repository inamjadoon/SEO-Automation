from pydantic import BaseModel
from typing import List, Dict, Optional, Any


class PageMetadata(BaseModel):
    price: Optional[str] = None
    currency: Optional[str] = None
    brand: Optional[str] = None
    category: Optional[str] = None
    author: Optional[str] = None
    published: Optional[str] = None


class Page(BaseModel):
    url: str
    type: str              # product | article | page | category
    title: str
    content: str
    metadata: Dict[str, Any] = {}


class ContentDocument(BaseModel):
    site_id: str  
    source: str            # shopify | wordpress | custom
    store_id: str
    base_url: str
    pages: List[Page]
