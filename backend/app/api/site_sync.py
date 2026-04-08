from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.site import Site
from app.workers.site_sync_tasks import sync_site_task


router = APIRouter(prefix="/sites", tags=["Sites Sync"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/{site_id}/sync")
def trigger_sync(site_id: str, db: Session = Depends(get_db)):
    site = db.query(Site).filter(Site.id == site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")

    task = sync_site_task.delay(site_id)
    site.sync_status = "pending"
    db.commit()

    return {"message": "Sync started", "task_id": task.id}

