from app.workers.celery_app import celery_app
from app.services.llms_service import generate_llms_text, save_llms_file
from app.schemas.content_document import ContentDocument


@celery_app.task
def generate_llms_file_task(document_dict: dict):
    doc = ContentDocument(**document_dict)

    text = generate_llms_text(doc)
    path = save_llms_file(doc.store_id, text)

    return {"status": "completed", "path": path}
