from datetime import datetime

from app.database import SessionLocal
from app.models.site import Site
from app.models.entity import Entity
from app.services.platform_detection import detect_platform
from app.services.ingestion import crawl_site, to_content_document
from app.services.normalization import upsert_entities_for_site
from app.workers.celery_app import celery_app
from app.workers.llms_tasks import generate_llms_file_task
from pathlib import Path
from app.services.indexnow import send_indexnow
from app.api.squarespace import (
    SiteAssetsRegistry,
    SquarespaceIntegrationConfig,
    refresh_assets_from_folder,
)
from fastapi import HTTPException, BackgroundTasks
import logging
import os
from app.services.faq_generator import generate_faq_schema_sync
import json
from app.services.gcs import upload_text

from dotenv import load_dotenv
load_dotenv(override=True)
import logging
logger = logging.getLogger("automation")

REGISTRY = SiteAssetsRegistry()

CONFIG = None  # lazy init

def get_api_base() -> str:
    api_base = os.getenv("API_BASE")
    if not api_base:
        raise HTTPException(status_code=500, detail="API_BASE environment variable is not configured")
    return api_base

def get_config() -> SquarespaceIntegrationConfig:
    """
    Lazy initialization of CONFIG, ensures env is read dynamically.
    """
    global CONFIG
    if CONFIG is None:
        try:
            CONFIG = SquarespaceIntegrationConfig(
                backend_base_url=get_api_base(),
                assets_root=Path("generated"),
                indexnow_key=None,
                indexnow_key_location=None
            )
            refresh_assets_from_folder(CONFIG, REGISTRY)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to initialize CONFIG: {str(e)}")
    return CONFIG

# def get_api_base() -> str:
    
#     api_base = os.getenv("API_BASE")
#     if not api_base:
#         raise HTTPException(status_code=500, detail="API_BASE environment variable is not configured")
#     return api_base

# CONFIG = SquarespaceIntegrationConfig(
#     backend_base_url=get_api_base(),
#     assets_root=Path("generated"),
#     indexnow_key=None,
#     indexnow_key_location=None
# )




@celery_app.task(bind=True, max_retries=3)
def sync_site_task(self, site_id: str) -> str:
    with SessionLocal() as db:
        site = db.query(Site).filter(Site.id == site_id).first()
        if not site:
            return f"Site {site_id} not found"

        site.sync_status = "processing"
        site.pages_processed = 0
        site.schemas_generated = 0
        db.commit()

        try:
            # Detect platform
            base_url = site.domain if site.domain.startswith("http") else f"https://{site.domain}"
            site.detected_platform = detect_platform(base_url)
            db.commit()

            # Crawl site
            items = crawl_site(site)
            site.pages_processed = len(items)
            db.commit()
            print("Items returned from crawler:", items)
            print("Items count:", len(items))

            # Clear old entities and insert new ones
            db.query(Entity).filter(Entity.site_id == site_id).delete(synchronize_session=False)
            db.commit()
            upsert_entities_for_site(db, site_id, items)

            logger.info(f"Generating FAQ schemas for {site_id}...")
            for item in items:
                # Skip pages with no useful content
                if not item.full_content or len(item.full_content) < 100:
                    continue
                if any(skip in (item.canonical_url or "") for skip in ["/cart", "/search", "/account"]):
                    continue

                full_url = f"{base_url.rstrip('/')}{item.canonical_url}"

                faq_schema = generate_faq_schema_sync(
                    page_name=item.name,
                    page_content=item.full_content,
                    page_url=full_url
                )

                if faq_schema:
                    slug = item.entity_id or "home"
                    # faq_folder = os.path.join("generated", site_id, "jsonld", "faqs")
                    # os.makedirs(faq_folder, exist_ok=True)
                    # faq_path = os.path.join(faq_folder, f"{slug}.jsonld")
                    # with open(faq_path, "w", encoding="utf-8") as f:
                    #     json.dump(faq_schema, f, indent=2, ensure_ascii=False)
                    # logger.info(f"FAQ schema saved for {item.canonical_url}")
                    gcs_path = f"{site_id}/jsonld/faqs/{slug}.jsonld"
                    upload_text(gcs_path, json.dumps(faq_schema, indent=2, ensure_ascii=False))
                    logger.info(f"FAQ schema uploaded to GCS for {item.canonical_url}")

            site.schemas_generated = db.query(Entity).filter(Entity.site_id == site_id).count()
            db.commit()

            # Build ContentDocument and trigger LLMs file generation
            doc = to_content_document(site, items)
            generate_llms_file_task.delay(doc.dict())

            # Trigger separate IndexNow + asset refresh task
            from app.workers.indexnow_tasks import trigger_indexnow_task
            trigger_indexnow_task.delay(site_id, [item.canonical_url for item in items if hasattr(item, "canonical_url")])

            site.last_synced_at = datetime.utcnow()
            site.sync_status = "ready"
            db.commit()

            return f"Site {site_id} synchronized"

        except Exception as e:
            site = db.query(Site).filter(Site.id == site_id).first()
            if site:
                site.sync_status = "failed"
                site.error_message = str(e)
                db.commit()
            raise e