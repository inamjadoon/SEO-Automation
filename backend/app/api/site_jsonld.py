# import json
# import os

# from fastapi import APIRouter, Depends, HTTPException, Query, Request
# from fastapi.responses import JSONResponse
# from sqlalchemy.orm import Session

# from app.database import SessionLocal
# from app.models.entity import Entity
# from app.models.site import Site
# from app.utils import normalize_path


# router = APIRouter(prefix="/sites", tags=["JSON-LD"])


# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()


# @router.get("/{site_id}/jsonld")
# def get_page_jsonld(
#     site_id: str,
#     # request: Request,
#     path: str = Query("/", description="Path portion of the URL, e.g. /products/sku-1"),
#     db: Session = Depends(get_db),
# ):
#     path = normalize_path(path)

#     """
#     Return pre-generated JSON-LD for a page of a connected site.
#     No scraping or generation is performed at request time.
#     """
#     entity = (
#         db.query(Entity)
#         .filter(
#             Entity.site_id == site_id,
#             Entity.canonical_url == path,
#         )
#         .first()
#     )
#     if not entity or not entity.jsonld_path:
#         raise HTTPException(status_code=404, detail="JSON-LD not found for this page")

#     if not os.path.exists(entity.jsonld_path):
#         raise HTTPException(status_code=404, detail="JSON-LD file missing on disk")

#     with open(entity.jsonld_path, "r", encoding="utf-8") as f:
#         data = json.load(f)

#     return JSONResponse(content=data)

import json
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.entity import Entity
from app.services.gcs import download_text, file_exists   # CHANGED
from app.utils import normalize_path

router = APIRouter(prefix="/sites", tags=["JSON-LD"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/{site_id}/jsonld")
def get_page_jsonld(
    site_id: str,
    path: str = Query("/"),
    db: Session = Depends(get_db),
):
    path = normalize_path(path)

    entity = (
        db.query(Entity)
        .filter(Entity.site_id == site_id, Entity.canonical_url == path)
        .first()
    )
    if not entity or not entity.jsonld_path:
        raise HTTPException(status_code=404, detail="JSON-LD not found for this page")

    # BEFORE: checked os.path.exists and opened local file
    # AFTER:  reads from GCS using the stored gcs_path
    if not file_exists(entity.jsonld_path):
        raise HTTPException(status_code=404, detail="JSON-LD file missing in storage")

    data = json.loads(download_text(entity.jsonld_path))
    return JSONResponse(content=data)