from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, HttpUrl
from app.database import SessionLocal
from app.models.site import Site
from app.api.site_sync import sync_site_task  
from app.api.squarespace import (
    SiteAssetsRegistry,
    SquarespaceIntegrationConfig,
    refresh_assets_from_folder,
    generate_squarespace_snippet
)
import logging
from fastapi.responses import HTMLResponse
from fastapi.responses import Response
from app.services.indexnow import generate_indexnow_key
import os


logger = logging.getLogger("automation")



router = APIRouter(prefix="/sites", tags=["Automation"])

# ---------- Request ----------
class SiteAutoRegisterRequest(BaseModel):
    site_id: str
    domain: HttpUrl

# ---------- Response ----------
class SiteAutoRegisterResponse(BaseModel):
    site_id: str
    snippet: str

# ---------- Registry & Config ----------
REGISTRY = SiteAssetsRegistry()
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(override=True)

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


@router.post("/auto-register", response_class=HTMLResponse)
def auto_register_site(payload: SiteAutoRegisterRequest, background_tasks: BackgroundTasks):
    
    site_id = payload.site_id
    domain = str(payload.domain).rstrip("/")

    # Create site in DB if it doesn't exist
    try:
        with SessionLocal() as db:
            site = db.query(Site).filter(Site.id == site_id).first()
            if not site:
                
                key = generate_indexnow_key()
                if not key:
                    raise HTTPException(status_code=500, detail="Failed to generate IndexNow key")

                key_location = f"{domain}/indexkey.txt"

                site = Site(
                            id=site_id,
                            domain=domain,
                            indexnow_key=key,
                            indexnow_key_location=key_location
                             )
                db.add(site)
                db.commit()
                db.refresh(site)
                logger.info(f"Site {site_id} created in DB")
            else:
                logger.info(f"Site {site_id} already exists")
    except Exception as e:
        logger.exception("Failed to create site")
        raise HTTPException(status_code=500, detail=f"DB error: {str(e)}")
    
    domain_clean = domain.replace("https://", "").replace("http://", "").rstrip("/")
   


    # Schedule site sync / crawling in background
    background_tasks.add_task(sync_site_task, site_id)
    
    
    logger.info(f"Site sync scheduled for {site_id} (runs in background)")

    # Refresh registry so Squarespace snippet can be generated
    config = get_config()
    refresh_assets_from_folder(config, REGISTRY)

    # Generate Squarespace snippet
    snippet = generate_squarespace_snippet(
                                            config,
                                            site_id,
                                            REGISTRY,
                                            indexnow_key=site.indexnow_key, 
                                            indexnow_key_location=site.indexnow_key_location)
    logger.debug("Generated snippet:\n%s", snippet)
    

    # return SiteAutoRegisterResponse(site_id=site_id, snippet=snippet)
    return HTMLResponse(content=snippet)



@router.get("/auto-register/{site_id}/snippet", response_class=HTMLResponse)
def get_clean_snippet(site_id: str):
    """
    Returns clean HTML <script> for copy-paste into Squarespace
    """
    with SessionLocal() as db:
        site = db.query(Site).filter(Site.id == site_id).first()

        if not site:
            raise HTTPException(status_code=404, detail="Site not found")

        if site.sync_status != "ready":
            raise HTTPException(
                status_code=202,
                detail=f"Site status: {site.sync_status}"
            )
    config = get_config()    
    refresh_assets_from_folder(config, REGISTRY)

    snippet = generate_squarespace_snippet(
                                            config,
                                            site_id,
                                            REGISTRY,
                                            indexnow_key=site.indexnow_key, 
                                            indexnow_key_location=site.indexnow_key_location)

    return HTMLResponse(content=snippet)


from app.workers.indexnow_tasks import trigger_indexnow_task
from app.services.ingestion import crawl_site  

@router.post("/test-indexnow", response_class=HTMLResponse)
def test_indexnow(site_id: str):
    from app.workers.indexnow_tasks import trigger_indexnow_task
    from app.services.ingestion import crawl_site
    from app.database import SessionLocal
    from app.models.site import Site

    with SessionLocal() as db:
        site = db.query(Site).filter(Site.id == site_id).first()
        if not site:
            raise HTTPException(status_code=404, detail="Site not found")

        # Crawl site to get URLs
        items = crawl_site(site)
        urls = list({
        item.canonical_url
        for item in items
        if hasattr(item, "canonical_url") and item.canonical_url
        })

        # Schedule IndexNow task (async)
        trigger_indexnow_task.delay(site_id, urls)

    return HTMLResponse(content=f"IndexNow task queued for {len(urls)} URLs")



from fastapi import APIRouter
from fastapi.responses import PlainTextResponse


# Existing routes here, e.g., /auto-register

@router.api_route(
    "/indexnow/{site_id}/{key}.txt",
    methods=["GET"],
    response_class=PlainTextResponse
)
def get_indexnow_key(site_id: str, key: str):
    """
    Serve the IndexNow key as plain text for search engine verification.
    """
    with SessionLocal() as db:
        site = db.query(Site).filter(Site.id == site_id).first()

        if not site or site.indexnow_key != key:
            raise HTTPException(status_code=404, detail="Invalid key")

    return key

# from fastapi import APIRouter, HTTPException, BackgroundTasks
# from pydantic import BaseModel, HttpUrl
# from app.database import SessionLocal
# from app.models.site import Site
# from app.api.site_sync import sync_site_task  
# from app.api.squarespace import (
#     SiteAssetsRegistry,
#     SquarespaceIntegrationConfig,
#     refresh_assets_from_folder,
#     generate_squarespace_snippet
# )
# import logging
# from fastapi.responses import HTMLResponse, PlainTextResponse
# from app.services.indexnow import generate_indexnow_key
# import os
# import httpx
# import asyncio
# from pathlib import Path
# from dotenv import load_dotenv

# load_dotenv(override=True)

# logger = logging.getLogger("automation")
# router = APIRouter(prefix="/sites", tags=["Automation"])

# REGISTRY = SiteAssetsRegistry()
# CONFIG = None
# CLOUDFLARE_API = "https://api.cloudflare.com/client/v4"

# # ---------- Request ----------
# class SiteAutoRegisterRequest(BaseModel):
#     site_id: str
#     domain: HttpUrl
#     cf_api_token: str
#     cf_zone_id: str
#     cf_account_id: str

# # ---------- Response ----------
# class SiteAutoRegisterResponse(BaseModel):
#     site_id: str
#     snippet: str

# def get_api_base() -> str:
#     api_base = os.getenv("API_BASE")
#     if not api_base:
#         raise HTTPException(status_code=500, detail="API_BASE not configured")
#     return api_base

# def get_config() -> SquarespaceIntegrationConfig:
#     global CONFIG
#     if CONFIG is None:
#         try:
#             CONFIG = SquarespaceIntegrationConfig(
#                 backend_base_url=get_api_base(),
#                 assets_root=Path("generated"),
#                 indexnow_key=None,
#                 indexnow_key_location=None
#             )
#             refresh_assets_from_folder(CONFIG, REGISTRY)
#         except Exception as e:
#             raise HTTPException(status_code=500, detail=f"Failed to initialize CONFIG: {str(e)}")
#     return CONFIG

# # ---------- Cloudflare Worker Script ----------
# # def get_worker_script(key: str) -> str:
# #     return f"""addEventListener('fetch', event => {{
# #     event.respondWith(handleRequest(event.request))
# # }})

# # async function handleRequest(request) {{
# #     const url = new URL(request.url)
# #     if (url.pathname === '/indexnow.txt') {{
# #         return new Response('{key}', {{
# #             headers: {{
# #                 'Content-Type': 'text/plain; charset=utf-8',
# #                 'Cache-Control': 'no-cache'
# #             }}
# #         }})
# #     }}
# #     return fetch(request)
# # }}"""
# def get_worker_script(key: str) -> str:
#     return f"""addEventListener('fetch', event => {{
#     event.respondWith(handleRequest(event.request))
# }})

# async function handleRequest(request) {{
#     const url = new URL(request.url)
#     const path = url.pathname.toLowerCase()
    
#     if (path === '/indexnow.txt' || path === '/indexnow') {{
#         return new Response('{key}', {{
#             status: 200,
#             headers: {{
#                 'Content-Type': 'text/plain; charset=utf-8',
#                 'Cache-Control': 'no-cache, no-store, must-revalidate',
#                 'Access-Control-Allow-Origin': '*',
#                 'X-Robots-Tag': 'noindex'
#             }}
#         }})
#     }}
#     return fetch(request)
# }}"""

# # ---------- Cloudflare Worker Deployment ----------
# async def deploy_cloudflare_worker(
#     account_id: str,
#     zone_id: str,
#     api_token: str,
#     domain: str,
#     key: str
# ):
#     worker_name = f"indexnow-{domain.replace('.', '-')}"
#     headers_auth = {"Authorization": f"Bearer {api_token}"}

#     async with httpx.AsyncClient(timeout=30) as client:

#         # Step 1 — Deploy Worker script
#         deploy_response = await client.put(
#             f"{CLOUDFLARE_API}/accounts/{account_id}/workers/scripts/{worker_name}",
#             headers={
#                 **headers_auth,
#                 "Content-Type": "application/javascript"
#             },
#             content=get_worker_script(key).encode()
#         )

#         logger.info(f"Worker deploy status: {deploy_response.status_code}")
#         logger.info(f"Worker deploy response: {deploy_response.text}")

#         if deploy_response.status_code not in [200, 201]:
#             raise HTTPException(
#                 status_code=500,
#                 detail=f"Worker deploy failed: {deploy_response.text}"
#             )
#         logger.info(f"Worker deployed: {worker_name}")

#         # Step 2 — Remove existing route if any
#         existing_routes_response = await client.get(
#             f"{CLOUDFLARE_API}/zones/{zone_id}/workers/routes",
#             headers=headers_auth
#         )

#         logger.info(f"Routes fetch status: {existing_routes_response.status_code}")
#         logger.info(f"Routes fetch response: {existing_routes_response.text}")

#         try:
#             routes_data = existing_routes_response.json()
#         except Exception as e:
#             logger.warning(f"Could not parse routes response: {e}")
#             routes_data = {}

#         if routes_data and isinstance(routes_data, dict):
#             for route in routes_data.get("result") or []:
#                 if "indexnow.txt" in route.get("pattern", ""):
#                     delete_response = await client.delete(
#                         f"{CLOUDFLARE_API}/zones/{zone_id}/workers/routes/{route['id']}",
#                         headers=headers_auth
#                     )
#                     logger.info(f"Deleted old route: {route['id']} — status: {delete_response.status_code}")

#         # Step 3 — Create new route
#         route_response = await client.post(
#             f"{CLOUDFLARE_API}/zones/{zone_id}/workers/routes",
#             headers={
#                 **headers_auth,
#                 "Content-Type": "application/json"
#             },
#             json={
#                 "pattern": f"{domain}/indexnow.txt",
#                 "script": worker_name
#             }
#         )

#         logger.info(f"Route create status: {route_response.status_code}")
#         logger.info(f"Route create response: {route_response.text}")

#         if route_response.status_code not in [200, 201]:
#             raise HTTPException(
#                 status_code=500,
#                 detail=f"Route creation failed: {route_response.text}"
#             )
#         logger.info(f"Route created for {domain}/indexnow.txt")

#     return worker_name
# # ---------- Poll Until Key Is Live ----------
# async def poll_key_live(domain: str, key: str, max_attempts: int = 20) -> bool:
    
#     for attempt in range(max_attempts):
#         try:
#             async with httpx.AsyncClient(follow_redirects=True, timeout=10) as client:
#                 response = await client.get(f"https://{domain}/indexnow.txt")
#                 if response.status_code == 200 and response.text.strip() == key:
#                     logger.info(f"Key verified live at {domain}/indexnow.txt")
#                     return True
#                 else:
#                     logger.warning(f"Poll attempt {attempt + 1}: got status {response.status_code}, body: {response.text[:100]}")
#         except Exception as e:
#             logger.warning(f"Poll attempt {attempt + 1} failed: {e}")
#         await asyncio.sleep(10)
#     return False

# # ---------- Full Cloudflare Setup + IndexNow Submit ----------
# async def setup_cloudflare_and_submit(
#     site_id: str,
#     domain: str,
#     key: str,
#     cf_api_token: str,
#     cf_zone_id: str,
#     cf_account_id: str
# ):
#     try:
#         # Clean domain
#         domain_clean = domain.replace("https://", "").replace("http://", "").replace("www.", "").rstrip("/")

#         # Deploy Worker
#         await deploy_cloudflare_worker(
#             account_id=cf_account_id,
#             zone_id=cf_zone_id,
#             api_token=cf_api_token,
#             domain=domain_clean,
#             key=key
#         )

#         # Poll until key is live
#         key_live = await poll_key_live(domain=domain_clean, key=key)

#         if not key_live:
#             logger.warning(f"Key not live yet for {domain_clean} — IndexNow skipped")
#             return

#         # Crawl site and fire IndexNow
#         from app.services.ingestion import crawl_site
#         from app.workers.indexnow_tasks import trigger_indexnow_task

#         with SessionLocal() as db:
#             site = db.query(Site).filter(Site.id == site_id).first()
#             if not site:
#                 logger.warning(f"Site {site_id} not found for IndexNow submission")
#                 return

#             items = crawl_site(site)
#             urls = list({
#                 item.canonical_url
#                 for item in items
#                 if hasattr(item, "canonical_url") and item.canonical_url
#             })

#         if not urls:
#             logger.warning(f"No URLs found for {domain_clean}")
#             return

#         trigger_indexnow_task.delay(site_id, urls)
#         logger.info(f"IndexNow triggered for {domain_clean} with {len(urls)} URLs")

#     except Exception as e:
#         logger.exception(f"Cloudflare setup failed for {site_id}: {e}")

# # ---------- Routes ----------

# @router.post("/auto-register", response_class=HTMLResponse)
# async def auto_register_site(payload: SiteAutoRegisterRequest, background_tasks: BackgroundTasks):

#     site_id = payload.site_id
#     domain = str(payload.domain).rstrip("/")

#     # Create site in DB if not exists
#     try:
#         with SessionLocal() as db:
#             site = db.query(Site).filter(Site.id == site_id).first()
#             if not site:
#                 key = generate_indexnow_key()
#                 if not key:
#                     raise HTTPException(status_code=500, detail="Failed to generate IndexNow key")

#                 key_location = f"{domain}/indexnow.txt"

#                 site = Site(
#                     id=site_id,
#                     domain=domain,
#                     indexnow_key=key,
#                     indexnow_key_location=key_location
#                 )
#                 db.add(site)
#                 db.commit()
#                 db.refresh(site)
#                 logger.info(f"Site {site_id} created in DB with key: {key}")
#             else:
#                 logger.info(f"Site {site_id} already exists")
#                 key = site.indexnow_key

#     except Exception as e:
#         logger.exception("Failed to create site")
#         raise HTTPException(status_code=500, detail=f"DB error: {str(e)}")

#     # Schedule site sync
#     background_tasks.add_task(sync_site_task, site_id)

#     # Deploy Cloudflare Worker + submit IndexNow in background
#     background_tasks.add_task(
#         asyncio.run,
#         setup_cloudflare_and_submit(
#             site_id=site_id,
#             domain=domain,
#             key=key,
#             cf_api_token=payload.cf_api_token,
#             cf_zone_id=payload.cf_zone_id,
#             cf_account_id=payload.cf_account_id
#         )
#     )

#     # Generate snippet
#     config = get_config()
#     refresh_assets_from_folder(config, REGISTRY)

#     with SessionLocal() as db:
#         site = db.query(Site).filter(Site.id == site_id).first()

#     snippet = generate_squarespace_snippet(
#         config,
#         site_id,
#         REGISTRY,
#         indexnow_key=site.indexnow_key,
#         indexnow_key_location=site.indexnow_key_location
#     )

#     return HTMLResponse(content=snippet)


# @router.get("/auto-register/{site_id}/snippet", response_class=HTMLResponse)
# def get_clean_snippet(site_id: str):
#     with SessionLocal() as db:
#         site = db.query(Site).filter(Site.id == site_id).first()
#         if not site:
#             raise HTTPException(status_code=404, detail="Site not found")
#         if site.sync_status != "ready":
#             raise HTTPException(status_code=202, detail=f"Site status: {site.sync_status}")

#     config = get_config()
#     refresh_assets_from_folder(config, REGISTRY)

#     snippet = generate_squarespace_snippet(
#         config,
#         site_id,
#         REGISTRY,
#         indexnow_key=site.indexnow_key,
#         indexnow_key_location=site.indexnow_key_location
#     )
#     return HTMLResponse(content=snippet)


# @router.post("/test-indexnow", response_class=HTMLResponse)
# def test_indexnow(site_id: str):
#     from app.workers.indexnow_tasks import trigger_indexnow_task
#     from app.services.ingestion import crawl_site

#     with SessionLocal() as db:
#         site = db.query(Site).filter(Site.id == site_id).first()
#         if not site:
#             raise HTTPException(status_code=404, detail="Site not found")

#         items = crawl_site(site)
#         urls = list({
#             item.canonical_url
#             for item in items
#             if hasattr(item, "canonical_url") and item.canonical_url
#         })
#         trigger_indexnow_task.delay(site_id, urls)

#     return HTMLResponse(content=f"IndexNow task queued for {len(urls)} URLs")


# @router.api_route(
#     "/indexnow/{site_id}/{key}.txt",
#     methods=["GET"],
#     response_class=PlainTextResponse
# )
# def get_indexnow_key(site_id: str, key: str):
#     with SessionLocal() as db:
#         site = db.query(Site).filter(Site.id == site_id).first()
#         if not site or site.indexnow_key != key:
#             raise HTTPException(status_code=404, detail="Invalid key")
#     return key