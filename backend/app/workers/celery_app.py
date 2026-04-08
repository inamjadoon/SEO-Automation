from celery import Celery


celery_app = Celery(
    "ai_content_system",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
)

celery_app.autodiscover_tasks(["app.workers"])

import app.workers.tasks
import app.workers.llms_tasks
import app.workers.site_sync_tasks
import app.workers.indexnow_tasks