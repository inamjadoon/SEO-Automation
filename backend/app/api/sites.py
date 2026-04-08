from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.site import Site
from app.schemas.site import SiteCreate, SiteResponse
from app.models.entity import Entity
from app.schemas.content_document import Page


router = APIRouter(prefix="/sites", tags=["Sites"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/", response_model=SiteResponse)
def create_site(payload: SiteCreate, db: Session = Depends(get_db)):
    existing = db.query(Site).filter(Site.id == payload.id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Site with this id already exists")

    existing_domain = db.query(Site).filter(Site.domain == str(payload.domain)).first()
    if existing_domain:
        raise HTTPException(status_code=400, detail="Site with this domain already exists")

    site = Site(
        id=payload.id,
        domain=str(payload.domain),
        api_credentials=payload.api_credentials,
        detected_platform="unknown",
        sync_status="never",
    )
    db.add(site)
    db.commit()
    db.refresh(site)
    return site


@router.get("/", response_model=List[SiteResponse])
def list_sites(db: Session = Depends(get_db)):
    return db.query(Site).all()


@router.get("/{site_id}", response_model=SiteResponse)
def get_site(site_id: str, db: Session = Depends(get_db)):
    site = db.query(Site).filter(Site.id == site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    return site


@router.delete("/{site_id}")
def delete_site(site_id: str, db: Session = Depends(get_db)):
    site = db.query(Site).filter(Site.id == site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")

    # Delete entities
    db.query(Entity).filter(Entity.site_id == site_id).delete(synchronize_session=False)

    # Delete site
    db.delete(site)
    db.commit()
    return {"detail": "Site and all related pages/entities deleted"}

