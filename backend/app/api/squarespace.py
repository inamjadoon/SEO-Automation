from __future__ import annotations

import os
from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.services.squarespace_integration import (
    SquarespaceIntegrationConfig,
    SiteAssetsRegistry,
    refresh_assets_from_folder,
    generate_squarespace_snippet,
    build_logging_router,
)
REGISTRY = SiteAssetsRegistry()

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

# def get_api_base() -> str:
    
#     api_base = os.getenv("API_BASE")
#     if not api_base:
#         raise HTTPException(status_code=500, detail="API_BASE environment variable is not configured")
#     return api_base

router = APIRouter(prefix="/squarespace", tags=["Squarespace"])

# _cfg = SquarespaceIntegrationConfig(
#     backend_base_url=get_api_base(),
#     assets_root=Path("generated"),
#     indexnow_key=str ,
#     indexnow_key_location=str
# )
_registry = SiteAssetsRegistry()



logging_router = build_logging_router(_registry)
if logging_router is not None:
    router.include_router(logging_router)

