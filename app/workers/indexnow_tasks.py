from datetime import datetime
from app.workers.celery_app import celery_app
from app.services.indexnow import send_indexnow
from app.services.squarespace_integration import SiteAssetsRegistry, SquarespaceIntegrationConfig, refresh_assets_from_folder
from app.database import SessionLocal
from app.models.site import Site
from pathlib import Path
from fastapi import HTTPException
import os
from app.services.sitemap_ping import ping_sitemap_sync
from urllib.parse import urljoin
from dotenv import load_dotenv
load_dotenv(override=True)



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

from urllib.parse import urljoin
@celery_app.task(bind=True, max_retries=3)
def trigger_indexnow_task(self, site_id: str, urls: list):
    with SessionLocal() as db:
        site = db.query(Site).filter(Site.id == site_id).first()
        if not site:
            print(f"No site found for IndexNow: site_id={site_id}")
            return
        if not urls:
            print(f"No URLs provided for IndexNow: site_id={site_id}")
            return

        try:
            # Refresh assets
            config = get_config()
            refresh_assets_from_folder(config, REGISTRY)

            # Normalize URLs correctly
            base_url = site.domain
            if not base_url.startswith("http"):
                base_url = f"https://{base_url}"  # Ensure protocol

            normalized_urls = []
            for url in urls:
                if not url:
                    continue
                # Only join if url is relative
                if url.startswith("http://") or url.startswith("https://"):
                    normalized_urls.append(url)
                else:
                    normalized_urls.append(urljoin(base_url, url))

            normalized_urls = list(set(normalized_urls))

            if not normalized_urls:
                print(f"No valid URLs for IndexNow after normalization for site: {site.domain}")
                return

            print(f"IndexNow payload for {site.domain}: {normalized_urls}")

            # Trigger IndexNow
            domain_clean = site.domain.replace("https://", "").replace("http://", "").rstrip("/")
            send_indexnow(domain=domain_clean, urls=normalized_urls, key=site.indexnow_key, key_location=site.indexnow_key_location)
            print(f"IndexNow triggered successfully for {site.domain}, {len(normalized_urls)} URLs")

            ping_sitemap_sync(domain_clean, normalized_urls)

            # Update last synced
            site.last_synced_at = datetime.utcnow()
            db.commit()

        except Exception as e:
            site.sync_status = "indexnow_failed"
            db.commit()
            print(f"IndexNow task failed for {site.domain}: {e}")
            raise e