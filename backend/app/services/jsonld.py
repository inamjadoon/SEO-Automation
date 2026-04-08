"""JSON-LD generation service.

Keeps the original generate_jsonld(entity_type, entity_id, name, attributes)
API but uses per-entity canonical URLs and the site's domain where possible.
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict
from urllib.parse import urlparse
from app.schemas import entity
from app.utils import get_entity_domain


BASE_DOMAIN = os.getenv("BASE_DOMAIN", "https://yourdefaultdomain.com")


def _full_url(entity) -> str:
    """Build a full URL for this entity using canonical_url and its domain."""
    url = getattr(entity, "canonical_url", "") or ""
    if url.startswith("http://") or url.startswith("https://"):
        return url
    domain = get_entity_domain(entity) or BASE_DOMAIN
    if not url.startswith("/"):
        url = "/" + url
    return domain.rstrip("/") + url


def _target_rel_path(entity_type: str, entity_id: str, canonical_url: str) -> str:
    """
    Compute the relative JSON-LD path inside a per-site folder.
    Mirrors the layout used by the refactor_generated script.
    """
    etype = (entity_type or "").lower()
    slug = entity_id or "item"
    path = (canonical_url or "/").strip() or "/"

    if path == "/":
        return "jsonld/homepage.jsonld"

    if etype == "product":
        return f"jsonld/products/{slug}.jsonld"
    if etype in {"article", "blog"}:
        return f"jsonld/articles/{slug}.jsonld"

    return f"jsonld/pages/{slug}.jsonld"


def _product_schema(entity) -> Dict[str, Any]:
    a = entity.attributes or {}
    offers_attr = a.get("offers") if isinstance(a.get("offers"), dict) else {}
    price = a.get("price") or (offers_attr.get("price") if offers_attr else None)
    currency = a.get("currency") or (offers_attr.get("priceCurrency") if offers_attr else None) or "USD"

    full_url = _full_url(entity)

    return {
        "@context": "https://schema.org",
        "@type": "Product",
        "@id": f"{full_url}#product",
        "name": entity.name,
        "description": a.get("description"),
        "image": a.get("image"),
        "url": full_url,
        "brand": {
            "@type": "Brand",
            "name": a.get("brand"),
        } if a.get("brand") else None,
        "sku": a.get("sku"),
        "offers": {
            "@type": "Offer",
            "price": price,
            "priceCurrency": currency,
            "availability": "https://schema.org/InStock",
            "url": full_url,
        } if price is not None else None,
        "category": a.get("category"),
    }


def _article_schema(entity) -> Dict[str, Any]:
    a = entity.attributes or {}
    full_url = _full_url(entity)

    return {
        "@context": "https://schema.org",
        "@type": "Article",
        "@id": f"{full_url}#article",
        "headline": entity.name,
        "description": a.get("description"),
        "author": a.get("author"),
        "datePublished": a.get("published"),
        "image": a.get("image"),
        "url": full_url,
    }


from urllib.parse import urlparse

def _webpage_schema(entity) -> dict:
    a = entity.attributes or {}

    full_url = _full_url(entity)
    domain = (get_entity_domain(entity) or BASE_DOMAIN).rstrip("/")

    parsed = urlparse(full_url)
    netloc = parsed.netloc
    organization_name = getattr(entity, "brand", None) or urlparse(full_url).netloc
    site_name = entity.name or urlparse(full_url).netloc

    # SAFE attribute extraction
    

    organization = {
        "@type": "Organization",
        "@id": f"{domain}#organization",
        "name": organization_name,
        "url": domain,
        "sameAs": a.get("sameAs", []),
    }

    website = {
        "@type": "WebSite",
        "@id": f"{domain}#website",
        "url": domain,
        "name": site_name,
        "publisher": {"@id": f"{domain}#organization"},
    }

    webpage = {
        "@type": "WebPage",
        "@id": f"{full_url}#webpage",
        "url": full_url,
        "name": entity.name,
        "description": a.get("description"),
        "inLanguage": a.get("language", "en"),
        "isPartOf": {"@id": f"{domain}#website"},
        "primaryImageOfPage": {
            "@type": "ImageObject",
            "url": a.get("image")
        } if a.get("image") else None,
        "author": {
            "@type": "Person",
            "name": a.get("author")
        } if getattr(entity, "author", None) else None,
    }

    def clean(node):
        cleaned = {}
        for k, v in node.items():
            if isinstance(v, dict):
                v = clean(v)
            if v not in (None, "", [], {}):
                cleaned[k] = v
        return cleaned

    nodes = [clean(organization), clean(website), clean(webpage)]

    return {
        "@context": "https://schema.org",
        "@graph": nodes
    }


def _generic_schema(entity) -> Dict[str, Any]:
    a = entity.attributes or {}
    full_url = _full_url(entity)

    return {
        "@context": "https://schema.org",
        "@type": entity.entity_type.capitalize(),
        "name": entity.name,
        "url": full_url,
        **a,
    }


SCHEMA_MAP = {
    "product": _product_schema,
    "article": _article_schema,
    "webpage": _webpage_schema,
}


def generate_jsonld(entity_type: str, entity_id: str, name: str, attributes: dict, canonical_url: str = None, brand=None, author=None) -> str:
    """Generate a JSON-LD file for an entity.

    This function keeps the original signature used by the workers, but it
    internally builds a richer JSON-LD graph using the entity's canonical_url
    and site domain where possible.
    """

    class _Entity:
        pass

    entity = _Entity()
    entity.entity_type = entity_type
    entity.entity_id = entity_id
    entity.name = name
    entity.attributes = attributes or {}
    # entity.canonical_url = canonical_url or attributes.get("canonical_url", f"/entities/{entity_type}/{entity_id}")
    entity.canonical_url = canonical_url or attributes.get(
        "canonical_url", f"/entities/{entity_type}/{entity_id}"
    )
    entity.brand = brand
    entity.author = author

    builder = SCHEMA_MAP.get(entity_type, _generic_schema)
    data = builder(entity)

    # Strip None values
    data = {k: v for k, v in data.items() if v is not None}

    # Decide file path:
    # - If attributes include a site_id, use per-site layout:
    #       generated/{site_id}/jsonld/...
    # - Otherwise, fall back to legacy layout: generated/{entity_type}/{id}.json
    site_id = attributes.get("site_id")
    if site_id:
        rel = _target_rel_path(entity_type, entity_id, entity.canonical_url)
        folder = os.path.join("generated", site_id, os.path.dirname(rel))
        filename = os.path.basename(rel)
        os.makedirs(folder, exist_ok=True)
        path = os.path.join(folder, filename)
    else:
        folder = os.path.join("generated", entity_type)
        os.makedirs(folder, exist_ok=True)
        path = os.path.join(folder, f"{entity_id}.json")

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return path

