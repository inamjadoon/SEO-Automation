from sqlalchemy import Column, String, JSON, DateTime, ForeignKey
from datetime import datetime
from app.database import Base
from sqlalchemy.orm import relationship

class Entity(Base):
    __tablename__ = "entities"

    id = Column(String, primary_key=True, index=True)  # product:sku-001
    site_id = Column(String, ForeignKey("sites.id"), nullable=True, index=True)
    entity_id = Column(String, nullable=False)
    entity_type = Column(String, nullable=False)
    name = Column(String, nullable=False)
    attributes = Column(JSON, default={})
    canonical_url = Column(String, nullable=False)
    jsonld_path = Column(String, nullable=True)
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    brand = Column(String, nullable=True)
    author = Column(String, nullable=True)
    site = relationship("Site", back_populates="entities")
