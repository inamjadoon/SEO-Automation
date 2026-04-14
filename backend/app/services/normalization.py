from typing import List

from sqlalchemy.orm import Session

from app.models.entity import Entity
from app.models.site import Site
from app.schema_registry import ALLOWED_TYPES
from app.services.entity_service import validate_entity, get_jsonld_path
from app.services.ingestion import NormalizedItem


def _map_entity_type(normalized_type: str) -> str:
    if normalized_type == "product":
        return "product"
    if normalized_type in {"article", "blog"}:
        return "article"
    return "webpage"


def upsert_entities_for_site(
    db: Session,
    site_id: str,
    items: List[NormalizedItem],
) -> List[Entity]:
    """
    Transform normalized items into internal Entity rows linked to the given site.
    Triggers background JSON-LD generation via existing Celery task.
    """
    # Resolve site domain once so we can build absolute URLs in JSON-LD.
    site = db.query(Site).filter(Site.id == site_id).first()
    if site and site.domain:
        site_base = site.domain if site.domain.startswith("http") else f"https://{site.domain}"
        site_base = site_base.rstrip("/")
    else:
        site_base = None

    entities: list[Entity] = []
    for item in items:
        entity_type = _map_entity_type(item.entity_type)

        # Ensure the type is registered
        if entity_type not in ALLOWED_TYPES:
            continue

        composite_id = f"{site_id}:{entity_type}:{item.entity_id}"
        canonical_url = item.canonical_url

        # Build attributes by entity type for correct JSON-LD generation
        if entity_type == "product":
            attributes = {
                "description": item.description,
                "image": item.image,
                "sku": item.sku,
                "brand": item.brand,
                "offers": {
                    "price": item.price,
                    "priceCurrency": item.currency,
                },
                "canonical_url": canonical_url,
                "site_domain": site_base,
                "site_id": site_id,
            }
        elif entity_type == "article":
            attributes = {
                "description": item.description,
                "image": item.image,
                "canonical_url": canonical_url,
                "author": getattr(item, "author", None),
                "published": getattr(item, "date_published", None),
                "site_domain": site_base,
                "site_id": site_id,
            }
        else:
            attributes = {
                "description": item.description,
                "image": item.image,
                "canonical_url": canonical_url,
                "site_domain": site_base,
                "site_id": site_id,
            }

        payload = {
            "entity_type": entity_type,
            "entity_id": item.entity_id,
            "name": item.name,
            "attributes": attributes,
        }

        # Validate against schema registry
        validate_entity(payload)

        entity: Entity | None = (
            db.query(Entity)
            .filter(Entity.id == composite_id)
            .first()
        )
        if entity:
            entity.name = item.name
            entity.attributes = payload["attributes"]
            entity.canonical_url = canonical_url
            entity.site_id = site_id
            entity.status = "pending"
        else:
            # jsonld_path = get_jsonld_path(entity_type, item.entity_id)
            jsonld_path = get_jsonld_path(site_id, entity_type, item.entity_id)

            entity = Entity(
                id=composite_id,
                site_id=site_id,
                entity_id=item.entity_id,
                entity_type=entity_type,
                name=item.name,
                attributes=payload["attributes"],
                canonical_url=canonical_url,
                jsonld_path=jsonld_path,
                status="pending",
            )
            db.add(entity)

        db.commit()
        db.refresh(entity)
        entities.append(entity)

        # Import here to avoid circular import at module load time
        from app.workers.tasks import process_entity
        process_entity.delay(entity.id)

    return entities

