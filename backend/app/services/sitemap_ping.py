# import httpx
# import asyncio
# import logging

# logger = logging.getLogger("automation")

# async def ping_sitemap(domain: str):
#     sitemap_url = f"https://{domain}/sitemap.xml"
#     endpoints = [
#         f"https://www.google.com/ping?sitemap={sitemap_url}",
#         f"https://www.bing.com/ping?sitemap={sitemap_url}",
#     ]
#     async with httpx.AsyncClient() as client:
#         for endpoint in endpoints:
#             try:
#                 res = await client.get(endpoint, timeout=10)
#                 logger.info(f"Sitemap ping -> {endpoint} : {res.status_code}")
#             except Exception as e:
#                 logger.warning(f"Sitemap ping failed for {endpoint}: {e}")

# def ping_sitemap_sync(domain: str):
#     """Use this in Celery tasks (sync context)"""
#     asyncio.run(ping_sitemap(domain))

import httpx
import asyncio
import logging
import os
from dotenv import load_dotenv
load_dotenv(override=True)
logger = logging.getLogger("automation")

async def ping_sitemap(domain: str, urls: list = []):  # ← ADD urls parameter
    site_url = f"https://{domain}"
    api_key = os.getenv("BING_WEBMASTER_KEY")
    
    logger.warning(f"Bing API key: {api_key[:8]}...")
    logger.warning(f"Bing siteUrl: {site_url}")
    logger.warning(f"Bing urls count: {len(urls)}")
    logger.warning(f"Bing first url: {urls[0] if urls else 'NO URLS'}")
    
    if not api_key:
        logger.warning(f"BING_WEBMASTER_KEY not set — skipping Bing submission for {domain}")
        return
    
    async with httpx.AsyncClient() as client:
        try:
            res = await client.post(
                f"https://ssl.bing.com/webmaster/api.svc/json/SubmitUrlbatch?apikey={api_key}",
                headers={
                    "Content-Type": "application/json"
                },
                json={
                    "siteUrl": site_url,
                    "urlList": urls  # ← uses passed urls now
                },
                timeout=10
            )
            logger.info(f"Bing submission -> {domain} : {res.status_code}: {res.text}")
        except Exception as e:
            logger.warning(f"Bing submission failed for {domain}: {e}")

def ping_sitemap_sync(domain: str, urls: list = []):
    """Use this in Celery tasks"""
    asyncio.run(ping_sitemap(domain, urls))