from datetime import datetime
from sqlalchemy import Column, String, DateTime, JSON
from sqlalchemy.orm import relationship
from app.database import Base


class Site(Base):
    __tablename__ = "sites"

    id = Column(String, primary_key=True, index=True)  # e.g. UUID or slug
    domain = Column(String, unique=True, nullable=False, index=True)
    detected_platform = Column(String, nullable=False, default="unknown")
    api_credentials = Column(JSON, nullable=True)  # platform-specific tokens, keys, etc.

    indexnow_key = Column(String, nullable=True)
    indexnow_key_location = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_synced_at = Column(DateTime, nullable=True)
    sync_status = Column(String, default="never")  # never | pending | running | success | failed

    entities = relationship(
        "Entity",
        back_populates="site",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    

