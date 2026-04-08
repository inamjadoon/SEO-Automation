# app/utils.py

import os
from urllib.parse import urlparse

BASE_DOMAIN = os.getenv("BASE_DOMAIN", "https://yourdefaultdomain.com")

def get_entity_domain(entity):
    """
    Returns the domain to use in JSON-LD.
    1. If canonical_url is already a full URL, use its domain.
    2. Otherwise, fallback to DEFAULT_BASE_DOMAIN from env.
    """
    # Prefer explicit site_domain on attributes when present
    attrs = getattr(entity, "attributes", {}) or {}
    site_domain = attrs.get("site_domain")
    if site_domain:
        return site_domain.rstrip("/")

    url = getattr(entity, "canonical_url", "")
    if url.startswith("http"):
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}"
    return BASE_DOMAIN

def normalize_path(path: str) -> str:
    """
    Normalize any URL or path into a canonical relative path.

    Rules:
    - If empty or None → "/"
    - Strip query parameters and fragments
    - Lowercase everything
    - Ensure leading slash
    - Remove trailing slash except root
    - Map common homepage aliases to "/"
    """
    if not path or path.strip() == "":
        return "/"

    # Remove query and fragment
    path = path.split("?")[0].split("#")[0].strip()

    # Handle full URLs
    if path.startswith("http"):
        path = urlparse(path).path or "/"

    # Ensure leading slash
    if not path.startswith("/"):
        path = "/" + path

    # Lowercase
    path = path.lower()

    # Normalize homepage aliases
    if path in ["/home", "/index", "/default", "/landing"]:
        return "/"

    # Remove trailing slash except root
    if path != "/" and path.endswith("/"):
        path = path[:-1]

    return path