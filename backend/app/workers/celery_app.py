import os
import ssl
from dotenv import load_dotenv
from celery import Celery
load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery("ai_content_system")

celery_app.conf.broker_url = REDIS_URL
celery_app.conf.result_backend = REDIS_URL

# Required for Upstash rediss:// SSL connection
celery_app.conf.broker_use_ssl = {
    'ssl_cert_reqs': ssl.CERT_NONE
}
celery_app.conf.redis_backend_use_ssl = {
    'ssl_cert_reqs': ssl.CERT_NONE
}

celery_app.autodiscover_tasks(["app.workers"])

import app.workers.tasks
import app.workers.llms_tasks
import app.workers.site_sync_tasks
import app.workers.indexnow_tasks