import os
from dotenv import load_dotenv
from celery import Celery
load_dotenv()


REDIS_URL = os.getenv("REDIS_URL")


celery_app = Celery(
    "ai_content_system",
    broker="REDIS_URL",
    backend="REDIS_URL"
)

celery_app.autodiscover_tasks(["app.workers"])

import app.workers.tasks
import app.workers.llms_tasks
import app.workers.site_sync_tasks
import app.workers.indexnow_tasks