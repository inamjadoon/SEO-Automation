# from __future__ import annotations

# import json
# import logging
# import time
# from dataclasses import dataclass, field
# from pathlib import Path
# from typing import Dict, Optional, List

# import requests

# from app.models.site import Site
# from app.database import SessionLocal

# logger = logging.getLogger("squarespace_integration")


# @dataclass
# class SiteAssets:
#     site_id: str
#     domain: str
#     jsonld_base_path: Path
#     llms_path: Optional[Path]
#     last_updated: float

#     has_snippet_generated: bool = False
#     snippet_installed: bool = False
#     last_snippet_fetch_ok: bool = False


# @dataclass
# class SquarespaceIntegrationConfig:
#     backend_base_url: str
#     assets_root: Path
#     indexnow_key: Optional[str] = None
#     indexnow_key_location: Optional[str] = None


# @dataclass
# class SiteAssetsRegistry:

#     sites: Dict[str, SiteAssets] = field(default_factory=dict)

#     def upsert(self, assets: SiteAssets):
#         self.sites[assets.site_id] = assets

#     def get(self, site_id: str) -> Optional[SiteAssets]:
#         return self.sites.get(site_id)

#     def all_sites(self) -> List[SiteAssets]:
#         return list(self.sites.values())

#     def mark_snippet_installed(self, site_id: str):
#         if site_id in self.sites:
#             self.sites[site_id].snippet_installed = True
#             logger.info("Snippet installed: %s", site_id)

#     def mark_fetch_ok(self, site_id: str, ok: bool):
#         if site_id in self.sites:
#             self.sites[site_id].last_snippet_fetch_ok = ok
#             logger.info("Snippet fetch status %s = %s", site_id, ok)



# def refresh_assets_from_folder(
#     cfg: SquarespaceIntegrationConfig,
#     registry: SiteAssetsRegistry
# ):
#     """
#     Loads generated assets from disk and updates registry
#     """

#     root = cfg.assets_root

#     if not root.exists():
#         logger.warning("Assets root does not exist: %s", root)
#         return

#     for site_dir in root.iterdir():

#         if not site_dir.is_dir():
#             continue

#         site_id = site_dir.name

#         llms_path = site_dir / "llms.txt"
#         llms_path = llms_path if llms_path.exists() else None

#         mtime = site_dir.stat().st_mtime

#         existing = registry.get(site_id)

#         if existing and existing.last_updated >= mtime:
#             continue

#         domain = resolve_domain(site_id)

#         assets = SiteAssets(
#             site_id=site_id,
#             domain=domain,
#             jsonld_base_path=site_dir,
#             llms_path=llms_path,
#             last_updated=mtime,
#             has_snippet_generated=existing.has_snippet_generated if existing else False,
#             snippet_installed=existing.snippet_installed if existing else False,
#             last_snippet_fetch_ok=existing.last_snippet_fetch_ok if existing else False,
#         )

#         registry.upsert(assets)

#         logger.info("Assets refreshed for site: %s", site_id)


# def resolve_domain(site_id: str) -> str:
#     """
#     Fetch domain from DB
#     """

#     try:

#         with SessionLocal() as db:

#             site = db.query(Site).filter(Site.id == site_id).first()

#             if site and site.domain:

#                 if site.domain.startswith("http"):
#                     return site.domain.rstrip("/")

#                 return f"https://{site.domain}".rstrip("/")

#     except Exception:
#         logger.warning("Domain lookup failed for site %s", site_id)

#     return f"https://{site_id}"


# def submit_indexnow(cfg: SquarespaceIntegrationConfig, urls: List[str]):

#     """
#     Submit URLs to IndexNow
#     """

#     if not urls:
#         return

#     payload = {
#         "host": urls[0].split("/")[2],
#         "key": cfg.indexnow_key,
#         "key_location": cfg.indexnow_key_location,
#         "urlList": urls
#     }

#     try:

#         r = requests.post(
#             "https://api.indexnow.org/indexnow",
#             json=payload,
#             timeout=10
#         )

#         if r.status_code == 200:
#             logger.info("IndexNow submission success (%d URLs)", len(urls))
#         else:
#             logger.warning("IndexNow failed: %s", r.text)

#     except Exception as e:
#         logger.error("IndexNow error: %s", e)




# def generate_squarespace_snippet(
#     cfg: SquarespaceIntegrationConfig,
#     site_id: str,
#     registry: SiteAssetsRegistry,
#     indexnow_key: Optional[str] = None,
#     indexnow_key_location: Optional[str] = None
# ) -> str:

#     assets = registry.get(site_id)

#     if not assets:
#         logger.warning("Assets missing for site %s", site_id)

#     api_base = cfg.backend_base_url.rstrip("/")
#     site_id_js = json.dumps(site_id)

    
    
#     snippet = f"""
#     <script>
#     (function() {{

#     var API_BASE = {json.dumps(api_base)};
#     var SITE_ID = {site_id_js};
#     const INDEXNOW_KEY_URL = "{indexnow_key_location}";
#     const INDEXNOW_KEY = "{indexnow_key}";

#     if(INDEXNOW_KEY){{
#         const meta = document.createElement("meta");
#         meta.name = "indexnow-key";
#         meta.content = INDEXNOW_KEY;
#         document.head.appendChild(meta);
#     }}

#     if(INDEXNOW_KEY_URL){{
#         const link = document.createElement("link");
#         link.rel = "indexnow-key";
#         link.href = INDEXNOW_KEY_URL;
#         document.head.appendChild(link);
#     }}

#     function currentPath() {{
#         var path = window.location.pathname || "/";
#         if (path !== "/" && path.endsWith("/")) path = path.slice(0, -1);
#         return path.toLowerCase();
#     }}

#     function injectJsonLd(data) {{
#         if (!data) return;
#         if (document.querySelector('script[data-ai-schema="true"]')) return;

#         var script = document.createElement("script");
#         script.type = "application/ld+json";
#         script.setAttribute("data-ai-schema", "true");
#         script.text = JSON.stringify(data);
#         document.head.appendChild(script);
#     }}

#     function ensureLlmsLink() {{
#         if (document.querySelector('link[data-llms-provider="backend"]')) return;

#         var link = document.createElement("link");
#         link.rel = "alternate";
#         link.type = "text/plain";
#         link.setAttribute("data-llms-provider", "backend");
#         link.href = API_BASE + "/llms/" + encodeURIComponent(SITE_ID);
#         document.head.appendChild(link);
#     }}

#     function logUsage(success) {{
#         try {{
#         fetch(
#             API_BASE + "/squarespace/sites/" + encodeURIComponent(SITE_ID) + "/snippet-usage",
#             {{
#             method: "POST",
#             headers: {{ "Content-Type": "application/json" }},
#             body: JSON.stringify({{
#                 success: !!success,
#                 path: currentPath()
#             }})
#             }}
#         );
#         }} catch (e) {{}}
#     }}

#     function fetchJsonLd() {{
#         var path = encodeURIComponent(currentPath());
#         var url = API_BASE + "/sites/" + encodeURIComponent(SITE_ID) + "/jsonld?path=" + path;
#         var cacheKey = "jsonld:" + SITE_ID + ":" + path;

#         var cached = sessionStorage.getItem(cacheKey);
#         if (cached) {{
#         try {{
#             injectJsonLd(JSON.parse(cached));
#             ensureLlmsLink();
#             logUsage(true);
#             return;
#         }} catch (e) {{}}
#         }}

#         fetch(url, {{
#         method: "GET",
#         headers: {{ "ngrok-skip-browser-warning": "true" }}
#         }})
#         .then(function(res) {{
#             if (!res.ok) throw new Error("No JSON-LD for this page");
#             return res.json();
#         }})
#         .then(function(data) {{
#             sessionStorage.setItem(cacheKey, JSON.stringify(data));
#             injectJsonLd(data);
#             ensureLlmsLink();
#             logUsage(true);
#         }})
#         .catch(function(err) {{
#             if (window.console && console.debug) {{
#             console.debug(
#                 "JSON-LD fetch skipped:",
#                 err && err.message ? err.message : err
#             );
#             }}
#             ensureLlmsLink();
#             logUsage(false);
#         }});
#     }}

#     if (document.readyState === "loading") {{
#         document.addEventListener("DOMContentLoaded", fetchJsonLd);
#     }} else {{
#         fetchJsonLd();
#     }}

#     window.addEventListener("popstate", fetchJsonLd);

#     }})();
#     </script>
#     """


#     if assets:
#         assets.has_snippet_generated = True

#     return snippet



# try:
#     from fastapi import APIRouter, Body
# except:
#     APIRouter = None


# def build_logging_router(registry: SiteAssetsRegistry):

#     if APIRouter is None:
#         return None

#     router = APIRouter(prefix="/sites", tags=["Squarespace"])

#     @router.post("/{site_id}/snippet-usage")
#     def snippet_usage(site_id: str, payload: dict = Body(...)):

#         ok = bool(payload.get("success"))

#         registry.mark_fetch_ok(site_id, ok)

#         return {"status": "ok"}

#     return router

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional, List

import requests

from app.models.site import Site
from app.database import SessionLocal

logger = logging.getLogger("squarespace_integration")

GCS_BUCKET_NAME = "ai-seo-files"
GCS_PUBLIC_BASE = f"https://storage.googleapis.com/{GCS_BUCKET_NAME}"


@dataclass
class SiteAssets:
    site_id: str
    domain: str
    jsonld_base_path: Path
    # Previously a local Path — now a public GCS URL or None if not yet uploaded
    llms_gcs_url: Optional[str]
    last_updated: float

    has_snippet_generated: bool = False
    snippet_installed: bool = False
    last_snippet_fetch_ok: bool = False


@dataclass
class SquarespaceIntegrationConfig:
    backend_base_url: str
    assets_root: Path
    indexnow_key: Optional[str] = None
    indexnow_key_location: Optional[str] = None


@dataclass
class SiteAssetsRegistry:

    sites: Dict[str, SiteAssets] = field(default_factory=dict)

    def upsert(self, assets: SiteAssets):
        self.sites[assets.site_id] = assets

    def get(self, site_id: str) -> Optional[SiteAssets]:
        return self.sites.get(site_id)

    def all_sites(self) -> List[SiteAssets]:
        return list(self.sites.values())

    def mark_snippet_installed(self, site_id: str):
        if site_id in self.sites:
            self.sites[site_id].snippet_installed = True
            logger.info("Snippet installed: %s", site_id)

    def mark_fetch_ok(self, site_id: str, ok: bool):
        if site_id in self.sites:
            self.sites[site_id].last_snippet_fetch_ok = ok
            logger.info("Snippet fetch status %s = %s", site_id, ok)


def gcs_llms_url(site_id: str) -> str:
    """
    Build the public GCS URL for a site's llms.txt file.
    Requires the file to be publicly readable in the bucket.
    """
    return f"{GCS_PUBLIC_BASE}/{site_id}/llms.txt"


def refresh_assets_from_folder(
    cfg: SquarespaceIntegrationConfig,
    registry: SiteAssetsRegistry
):
    """
    Loads generated assets from disk and updates registry.
    llms.txt is no longer stored on disk — its URL is derived from GCS.
    """

    root = cfg.assets_root

    if not root.exists():
        logger.warning("Assets root does not exist: %s", root)
        return

    for site_dir in root.iterdir():

        if not site_dir.is_dir():
            continue

        site_id = site_dir.name

        # llms.txt now lives in GCS — build the URL directly instead of
        # looking for a local file.
        llms_url = gcs_llms_url(site_id)

        mtime = site_dir.stat().st_mtime

        existing = registry.get(site_id)

        if existing and existing.last_updated >= mtime:
            continue

        domain = resolve_domain(site_id)

        assets = SiteAssets(
            site_id=site_id,
            domain=domain,
            jsonld_base_path=site_dir,
            llms_gcs_url=llms_url,
            last_updated=mtime,
            has_snippet_generated=existing.has_snippet_generated if existing else False,
            snippet_installed=existing.snippet_installed if existing else False,
            last_snippet_fetch_ok=existing.last_snippet_fetch_ok if existing else False,
        )

        registry.upsert(assets)

        logger.info("Assets refreshed for site: %s", site_id)


def resolve_domain(site_id: str) -> str:
    """
    Fetch domain from DB
    """

    try:

        with SessionLocal() as db:

            site = db.query(Site).filter(Site.id == site_id).first()

            if site and site.domain:

                if site.domain.startswith("http"):
                    return site.domain.rstrip("/")

                return f"https://{site.domain}".rstrip("/")

    except Exception:
        logger.warning("Domain lookup failed for site %s", site_id)

    return f"https://{site_id}"


def submit_indexnow(cfg: SquarespaceIntegrationConfig, urls: List[str]):

    """
    Submit URLs to IndexNow
    """

    if not urls:
        return

    payload = {
        "host": urls[0].split("/")[2],
        "key": cfg.indexnow_key,
        "key_location": cfg.indexnow_key_location,
        "urlList": urls
    }

    try:

        r = requests.post(
            "https://api.indexnow.org/indexnow",
            json=payload,
            timeout=10
        )

        if r.status_code == 200:
            logger.info("IndexNow submission success (%d URLs)", len(urls))
        else:
            logger.warning("IndexNow failed: %s", r.text)

    except Exception as e:
        logger.error("IndexNow error: %s", e)


def generate_squarespace_snippet(
    cfg: SquarespaceIntegrationConfig,
    site_id: str,
    registry: SiteAssetsRegistry,
    indexnow_key: Optional[str] = None,
    indexnow_key_location: Optional[str] = None
) -> str:

    assets = registry.get(site_id)

    if not assets:
        logger.warning("Assets missing for site %s", site_id)

    api_base = cfg.backend_base_url.rstrip("/")
    site_id_js = json.dumps(site_id)

    # Use the GCS URL for llms.txt if available, otherwise fall back to the
    # backend proxy endpoint (keeps things working even before the file is
    # uploaded to the bucket).
    llms_url = (
        assets.llms_gcs_url
        if assets and assets.llms_gcs_url
        else f"{api_base}/llms/{site_id}"
    )

    snippet = f"""
    <script>
    (function() {{

    var API_BASE = {json.dumps(api_base)};
    var SITE_ID = {site_id_js};
    // llms.txt is served directly from GCS — no backend hop needed.
    var LLMS_URL = {json.dumps(llms_url)};
    const INDEXNOW_KEY_URL = "{indexnow_key_location}";
    const INDEXNOW_KEY = "{indexnow_key}";

    if(INDEXNOW_KEY){{
        const meta = document.createElement("meta");
        meta.name = "indexnow-key";
        meta.content = INDEXNOW_KEY;
        document.head.appendChild(meta);
    }}

    if(INDEXNOW_KEY_URL){{
        const link = document.createElement("link");
        link.rel = "indexnow-key";
        link.href = INDEXNOW_KEY_URL;
        document.head.appendChild(link);
    }}

    function currentPath() {{
        var path = window.location.pathname || "/";
        if (path !== "/" && path.endsWith("/")) path = path.slice(0, -1);
        return path.toLowerCase();
    }}

    function injectJsonLd(data) {{
        if (!data) return;
        if (document.querySelector('script[data-ai-schema="true"]')) return;

        var script = document.createElement("script");
        script.type = "application/ld+json";
        script.setAttribute("data-ai-schema", "true");
        script.text = JSON.stringify(data);
        document.head.appendChild(script);
    }}

    function ensureLlmsLink() {{
        if (document.querySelector('link[data-llms-provider="backend"]')) return;

        var link = document.createElement("link");
        link.rel = "alternate";
        link.type = "text/plain";
        link.setAttribute("data-llms-provider", "backend");
        // Points directly to GCS — no backend proxy involved.
        link.href = LLMS_URL;
        document.head.appendChild(link);
    }}

    function logUsage(success) {{
        try {{
        fetch(
            API_BASE + "/squarespace/sites/" + encodeURIComponent(SITE_ID) + "/snippet-usage",
            {{
            method: "POST",
            headers: {{ "Content-Type": "application/json" }},
            body: JSON.stringify({{
                success: !!success,
                path: currentPath()
            }})
            }}
        );
        }} catch (e) {{}}
    }}

    function fetchJsonLd() {{
        var path = encodeURIComponent(currentPath());
        var url = API_BASE + "/sites/" + encodeURIComponent(SITE_ID) + "/jsonld?path=" + path;
        var cacheKey = "jsonld:" + SITE_ID + ":" + path;

        var cached = sessionStorage.getItem(cacheKey);
        if (cached) {{
        try {{
            injectJsonLd(JSON.parse(cached));
            ensureLlmsLink();
            logUsage(true);
            return;
        }} catch (e) {{}}
        }}

        fetch(url, {{
        method: "GET",
        headers: {{ "ngrok-skip-browser-warning": "true" }}
        }})
        .then(function(res) {{
            if (!res.ok) throw new Error("No JSON-LD for this page");
            return res.json();
        }})
        .then(function(data) {{
            sessionStorage.setItem(cacheKey, JSON.stringify(data));
            injectJsonLd(data);
            ensureLlmsLink();
            logUsage(true);
        }})
        .catch(function(err) {{
            if (window.console && console.debug) {{
            console.debug(
                "JSON-LD fetch skipped:",
                err && err.message ? err.message : err
            );
            }}
            ensureLlmsLink();
            logUsage(false);
        }});
    }}

    if (document.readyState === "loading") {{
        document.addEventListener("DOMContentLoaded", fetchJsonLd);
    }} else {{
        fetchJsonLd();
    }}

    window.addEventListener("popstate", fetchJsonLd);

    }})();
    </script>
    """

    if assets:
        assets.has_snippet_generated = True

    return snippet


try:
    from fastapi import APIRouter, Body
except:
    APIRouter = None


def build_logging_router(registry: SiteAssetsRegistry):

    if APIRouter is None:
        return None

    router = APIRouter(prefix="/sites", tags=["Squarespace"])

    @router.post("/{site_id}/snippet-usage")
    def snippet_usage(site_id: str, payload: dict = Body(...)):

        ok = bool(payload.get("success"))

        registry.mark_fetch_ok(site_id, ok)

        return {"status": "ok"}

    return router