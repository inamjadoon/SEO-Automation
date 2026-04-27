# from app.workers.celery_app import celery_app
# from app.services.llms_service import generate_llms_text, save_llms_file
# from app.schemas.content_document import ContentDocument


# @celery_app.task
# def generate_llms_file_task(document_dict: dict):
#     doc = ContentDocument(**document_dict)

#     text = generate_llms_text(doc)
#     path = save_llms_file(doc.site_id, text)

#     return {"status": "completed", "path": path}

import logging
from app.workers.celery_app import celery_app
from app.services.llms_service import generate_llms_text, save_llms_file
from app.schemas.content_document import ContentDocument

logger = logging.getLogger("llms_task")


@celery_app.task(bind=True, max_retries=3, default_retry_delay=10)
def generate_llms_file_task(self, document_dict: dict):
    site_id = document_dict.get("site_id", "unknown")
    try:
        doc = ContentDocument(**document_dict)
        text = generate_llms_text(doc)
        public_url = save_llms_file(doc.site_id, text)
        logger.info("llms.txt done for site %s → %s", site_id, public_url)
        return {"status": "completed", "url": public_url}
    except Exception as exc:
        logger.exception("llms.txt upload failed for site %s: %s", site_id, exc)
        raise self.retry(exc=exc)