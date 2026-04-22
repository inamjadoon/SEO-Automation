"""Ingestion service: crawl a site, normalize pages to internal entities,
produce data for JSON-LD generation and llms.txt.

This is intentionally simple and backend-focused (no CLI).
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import List, Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from app.models.site import Site
from app.schemas.content_document import ContentDocument, Page
from app.utils import normalize_path

DEFAULT_MAX_PAGES = int(os.getenv("CRAWLER_MAX_PAGES", "150"))

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; SiteCrawler/1.0; +https://example.com/bot)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def _session() -> requests.Session:
    s = requests.Session()
    s.headers.update(DEFAULT_HEADERS)
    retries = Retry(total=2, backoff_factor=0.5, status_forcelist=[502, 503, 504])
    s.mount("https://", HTTPAdapter(max_retries=retries))
    s.mount("http://", HTTPAdapter(max_retries=retries))
    return s


def _same_domain(url: str, base_url: str) -> bool:
    """
    Return True if two URLs belong to the same registrable host.
    Treat www.example.com and example.com as the same.
    """
    try:
        u = urlparse(url)
        b = urlparse(base_url)
        u_host = (u.netloc or b.netloc).lower().lstrip("www.")
        b_host = (b.netloc or "").lower().lstrip("www.")
        return bool(u_host) and u_host == b_host
    except Exception:
        return False


def _fetch(url: str) -> Optional[str]:
    s = _session()
    try:
        resp = s.get(url, timeout=15)
        if resp.status_code >= 400:
            return None
        return resp.text
    except Exception:
        return None


@dataclass
class NormalizedItem:
    entity_type: str  # product | article | webpage
    entity_id: str
    name: str
    description: str
    canonical_url: str  # path (e.g. "/about")
    image: Optional[str] = None
    price: Optional[str] = None
    currency: Optional[str] = None
    sku: Optional[str] = None
    brand: Optional[str] = None
    author: Optional[str] = None
    date_published: Optional[str] = None
    full_content: Optional[str] = None


def _slug_from_url(url: str) -> str:
    parsed = urlparse(url)
    slug = parsed.path.rstrip("/").split("/")[-1] or "home"
    return slug


def _extract_jsonld_blocks(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    data: list[dict] = []
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            raw = script.string or script.text
            if not raw:
                continue
            block = json.loads(raw)
        except Exception:
            continue

        if isinstance(block, list):
            data.extend([b for b in block if isinstance(b, dict)])
        elif isinstance(block, dict):
            if "@graph" in block and isinstance(block["@graph"], list):
                data.extend([b for b in block["@graph"] if isinstance(b, dict)])
            else:
                data.append(block)
    return data


def _jsonld_types(obj: dict) -> list[str]:
    t = obj.get("@type")
    if isinstance(t, list):
        return [x.lower() for x in t if isinstance(x, str)]
    if isinstance(t, str):
        return [t.lower()]
    return []


def _looks_like_price_page(html: str) -> bool:
    soup = BeautifulSoup(html, "html.parser")
    price_el = soup.select_one('[itemprop="price"], .price, .product-price, .product__price, [data-price]')
    if price_el:
        return True
    text = soup.get_text(" ", strip=True)
    return bool(re.search(r"(\$|€|£)\s*\d+[\d,.]*", text))


# def _extract_generic_page(url: str, html: str) -> NormalizedItem:
#     soup = BeautifulSoup(html, "html.parser")
#     title_tag = soup.find("title")
#     title = (title_tag.text or "").strip() if title_tag else url

#     desc = ""
#     meta_desc = soup.find("meta", attrs={"name": "description"})
#     if meta_desc and meta_desc.get("content"):
#         desc = meta_desc["content"].strip()
#     if not desc:
#         first_p = soup.find("p")
#         if first_p:
#             desc = first_p.get_text(strip=True)[:512]

#     og_image = soup.find("meta", property="og:image")
#     image = og_image["content"].strip() if og_image and og_image.get("content") else None

#     parsed = urlparse(url)
#     return NormalizedItem(
#         entity_type="webpage",
#         entity_id=_slug_from_url(url),
#         name=title,
#         description=desc or title,
#         canonical_url=parsed.path or "/",
#         image=image,
#     )
def _extract_generic_page(url: str, html: str) -> NormalizedItem:
    soup = BeautifulSoup(html, "html.parser")
    parsed = urlparse(url)
    canonical_url = normalize_path(parsed.path or "/")

    # Title
    title_tag = soup.find("title")
    title = (title_tag.text or "").strip() if title_tag else url

    # Description
    desc = ""
    meta_desc = soup.find("meta", attrs={"name": "description"})
    if meta_desc and meta_desc.get("content"):
        desc = meta_desc["content"].strip()
    if not desc:
        first_p = soup.find("p")
        if first_p:
            desc = first_p.get_text(strip=True)[:512]

    # Image
    og_image = soup.find("meta", property="og:image")
    image = og_image["content"].strip() if og_image and og_image.get("content") else None

    # Site / Organization name
    meta_site_name = soup.find("meta", property="og:site_name")
    site_name = meta_site_name["content"].strip() if meta_site_name and meta_site_name.get("content") else urlparse(url).netloc

    # Author
    meta_author = soup.find("meta", attrs={"name": "author"})
    author = meta_author["content"].strip() if meta_author and meta_author.get("content") else None

    parsed = urlparse(url)
    site_name = meta_site_name["content"].strip() if meta_site_name and meta_site_name.get("content") else parsed.netloc

    for tag in soup.find_all(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    full_content = soup.get_text(separator=" ", strip=True)[:3000]

    return NormalizedItem(
        entity_type="webpage",
        entity_id=_slug_from_url(url),
        name=title,
        description=desc or title,
        canonical_url=canonical_url,
        image=image,
        author=author,
        brand=site_name,
        full_content=full_content  # store site/org name here for JSON-LD
    )

def _normalize_product_from_jsonld(obj: dict, url: str) -> NormalizedItem:
    name = obj.get("name") or url
    description = obj.get("description") or ""
    image = obj.get("image")
    parsed = urlparse(url)
    canonical_url = normalize_path(parsed.path or "/")
    if isinstance(image, list):
        image = image[0] if image else None

    sku = obj.get("sku")
    brand = obj.get("brand")
    if isinstance(brand, dict):
        brand = brand.get("name") or brand.get("@id")

    offers = obj.get("offers") or {}
    if isinstance(offers, list):
        offers = offers[0] if offers else {}
    price = offers.get("price")
    currency = offers.get("priceCurrency")

    parsed = urlparse(url)
    return NormalizedItem(
        entity_type="product",
        entity_id=_slug_from_url(url),
        name=name,
        description=description or name,
        canonical_url=canonical_url,
        image=image,
        price=str(price) if price is not None else None,
        currency=currency,
        sku=sku,
        brand=brand,
    )


def _normalize_article_from_jsonld(obj: dict, url: str) -> NormalizedItem:
    name = obj.get("headline") or obj.get("name") or url
    description = obj.get("description") or ""
    image = obj.get("image")
    parsed = urlparse(url)
    canonical_url = normalize_path(parsed.path or "/")
    if isinstance(image, list):
        image = image[0] if image else None

    author = obj.get("author")
    if isinstance(author, dict):
        author = author.get("name") or author.get("@id")
    date_published = obj.get("datePublished")

    parsed = urlparse(url)
    return NormalizedItem(
        entity_type="article",
        entity_id=_slug_from_url(url),
        name=name,
        description=description or name,
        canonical_url=canonical_url,
        image=image,
        author=author,
        date_published=date_published,
    )


def _classify_and_normalize(url: str, html: str) -> NormalizedItem:
    """Decide entity type using JSON-LD + simple URL heuristics."""
    jsonld_blocks = _extract_jsonld_blocks(html)
    canonical_path = normalize_path(urlparse(url).path or url)

    def _is_product_url(p: str) -> bool:
        return any(seg in p for seg in ["/product", "/products/", "/shop/", "/store/"])

    def _is_article_url(p: str) -> bool:
        return any(seg in p for seg in ["/blog", "/news", "/post", "/category/"])

    # Product from JSON-LD + URL pattern
    if _is_product_url(canonical_path):
        for obj in jsonld_blocks:
            if "product" in _jsonld_types(obj):
                return _normalize_product_from_jsonld(obj, url)
        if _looks_like_price_page(html):
            return _normalize_product_from_jsonld({}, url)

    # Article/blog from JSON-LD + URL pattern
    if _is_article_url(canonical_path):
        for obj in jsonld_blocks:
            if any(t in {"article", "blogposting", "newsarticle", "blog"} for t in _jsonld_types(obj)):
                return _normalize_article_from_jsonld(obj, url)

    # Fallback: generic page
    return _extract_generic_page(url, html)


def _extract_internal_links(html: str, page_url: str, root_url: str) -> List[str]:
    """Collect same-domain links from page."""
    soup = BeautifulSoup(html, "html.parser")
    links: List[str] = []
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if not href or href.startswith("#"):
            continue
        if any(href.startswith(prefix) for prefix in ("mailto:", "tel:", "javascript:", "data:")):
            continue
        absolute = urljoin(page_url, href)
        if not _same_domain(absolute, root_url):
            continue
        links.append(absolute)
    return links


def crawl_site(site: Site, max_pages: int = DEFAULT_MAX_PAGES) -> List[NormalizedItem]:
    """Naive BFS crawl limited to max_pages within one domain."""
    start_url = site.domain if site.domain.startswith("http") else f"https://{site.domain}"

    seen: set[str] = set()
    queue: List[str] = [start_url]
    items: List[NormalizedItem] = []

    while queue and len(items) < max_pages:
        url = queue.pop(0)
        if url in seen:
            continue
        seen.add(url)

        html = _fetch(url)
        if not html:
            continue

        item = _classify_and_normalize(url, html)
        items.append(item)

        for link in _extract_internal_links(html, url, start_url):
            if link not in seen and link not in queue:
                queue.append(link)

    return items


def to_content_document(site: Site, items: List[NormalizedItem]) -> ContentDocument:
    """Convert NormalizedItem list into ContentDocument for llms.txt."""
    base_url = site.domain if site.domain.startswith("http") else f"https://{site.domain}"
    pages: list[Page] = []
    for item in items:
        page_type = "product" if item.entity_type == "product" else "article" if item.entity_type == "article" else "page"
        metadata = {}
        if item.price is not None:
            metadata["price"] = item.price
        if item.currency is not None:
            metadata["currency"] = item.currency
        if item.sku is not None:
            metadata["sku"] = item.sku
        if item.brand is not None:
            metadata["brand"] = item.brand
        if item.image is not None:
            metadata["image"] = item.image
        if item.author is not None:
            metadata["author"] = item.author
        if item.date_published is not None:
            metadata["published"] = item.date_published

        pages.append(
            Page(
                url=item.canonical_url,
                type=page_type,
                title=item.name,
                content=item.description,
                metadata=metadata,
            )
        )

    return ContentDocument(
        site_id=site.id,
        source="custom",
        store_id=site.id,
        base_url=base_url,
        pages=pages,
    )

