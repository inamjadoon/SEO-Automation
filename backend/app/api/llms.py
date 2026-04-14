# import os

# from fastapi import APIRouter, HTTPException
# from fastapi.responses import PlainTextResponse
# from app.schemas.content_document import ContentDocument
# from app.workers.llms_tasks import generate_llms_file_task

# router = APIRouter()


# @router.post("/generate-llms")
# def generate_llms(doc: ContentDocument):
#     task = generate_llms_file_task.delay(doc.dict())
#     return {"message": "LLMS generation started", "task_id": task.id}


# @router.get("/{site_id}", response_class=PlainTextResponse)
# def get_llms_for_site(site_id: str):
#     """
#     Serve the generated llms.txt file for a given site.
#     """
#     file_path = os.path.join("generated", site_id, "llms.txt")
#     if not os.path.exists(file_path):
#         raise HTTPException(status_code=404, detail="llms.txt not found for this site")

#     with open(file_path, "r", encoding="utf-8") as f:
#         content = f.read()

#     return PlainTextResponse(content=content)

from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse
from app.schemas.content_document import ContentDocument
from app.workers.llms_tasks import generate_llms_file_task
from app.services.gcs import download_text, file_exists  # CHANGED

router = APIRouter()

@router.post("/generate-llms")
def generate_llms(doc: ContentDocument):
    task = generate_llms_file_task.delay(doc.dict())
    return {"message": "LLMS generation started", "task_id": task.id}

@router.get("/{site_id}", response_class=PlainTextResponse)
def get_llms_for_site(site_id: str):
    # BEFORE: os.path.join("generated", site_id, "llms.txt")
    # AFTER:  derived gcs_path — same convention as save_llms_file
    gcs_path = f"{site_id}/llms.txt"
    if not file_exists(gcs_path):
        raise HTTPException(status_code=404, detail="llms.txt not found for this site")
    return PlainTextResponse(download_text(gcs_path))