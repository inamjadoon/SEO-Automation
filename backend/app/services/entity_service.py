
# import os
# from datetime import datetime
# from sqlalchemy.orm import Session
# from app.models.entity import Entity
# from app.schema_registry import ALLOWED_TYPES

# BASE_DOMAIN = os.getenv("BASE_DOMAIN", "https://yourdomain.com")


# def validate_entity(payload: dict):
#     entity_type = payload.get("entity_type")
#     if entity_type not in ALLOWED_TYPES:
#         raise ValueError("Invalid entity type")

#     for field in ALLOWED_TYPES[entity_type]["required_fields"]:
#         if field == "name" and not payload.get("name"):
#             raise ValueError("Missing required field: name")
#         elif field != "name" and not payload.get("attributes", {}).get(field):
#             raise ValueError(f"Missing required field: {field}")


# import os

# def get_jsonld_path(entity_type: str, entity_id: str) -> str:
#     folder = os.path.join("generated", entity_type)
#     os.makedirs(folder, exist_ok=True)
#     return os.path.join(folder, f"{entity_id}.json")


# def create_or_update_entity(db: Session, payload: dict):
#     validate_entity(payload)

#     entity_type = payload["entity_type"]
#     entity_id = payload["entity_id"]
#     name = payload["name"]
#     attributes = payload.get("attributes", {})

#     composite_id = f"{entity_type}:{entity_id}"

#     canonical_url = f"/entities/{entity_type}/{entity_id}"
#     jsonld_path = get_jsonld_path(entity_type, entity_id)

#     existing = db.query(Entity).filter(Entity.id == composite_id).first()
#     if existing:
        
#         if existing.jsonld_path and os.path.exists(existing.jsonld_path):
#             os.remove(existing.jsonld_path)

#         existing.name = name
#         existing.attributes = attributes
#         existing.status = "pending"
#         db.commit()
#         db.refresh(existing)
#         return existing

#     new_entity = Entity(
#         id=composite_id,
#         entity_id=entity_id,
#         entity_type=entity_type,
#         name=name,
#         attributes=attributes,
#         canonical_url=canonical_url,
#         jsonld_path=jsonld_path,
#         brand=attributes.get("brand"),
#         author=attributes.get("author"),
#         status="pending",
#     )
#     db.add(new_entity)
#     db.commit()
#     db.refresh(new_entity)

#     # trigger Celery task here to generate the JSON-LD file asynchronously
#     # generate_jsonld_task.delay(entity_type, entity_id, name, attributes)

#     return new_entity

# def delete_entity(db: Session, entity_id: str) -> bool:
#     entity = db.query(Entity).filter(Entity.id == entity_id).first()
#     if not entity:
#         return False

#     jsonld_path = entity.jsonld_path

#     try:
#         # Delete file first
#         if jsonld_path and os.path.exists(jsonld_path):
#             os.remove(jsonld_path)
#     except Exception as e:
#         # If file deletion fails, do NOT delete DB record
#         print(f"Error deleting file: {e}")
#         return False

#     # Now delete DB record
#     db.delete(entity)
#     db.commit()

#     return True

#entity_service.py
import os
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.entity import Entity
from app.schema_registry import ALLOWED_TYPES
from app.services.gcs import file_exists

BASE_DOMAIN = os.getenv("BASE_DOMAIN", "https://yourdomain.com")


def validate_entity(payload: dict):
    entity_type = payload.get("entity_type")
    if entity_type not in ALLOWED_TYPES:
        raise ValueError("Invalid entity type")
    for field in ALLOWED_TYPES[entity_type]["required_fields"]:
        if field == "name" and not payload.get("name"):
            raise ValueError("Missing required field: name")
        elif field != "name" and not payload.get("attributes", {}).get(field):
            raise ValueError(f"Missing required field: {field}")


def get_jsonld_path(site_id: str, entity_type: str, entity_id: str) -> str:
    """
    Returns the canonical GCS path for a JSON-LD file.
    Format: {site_id}/jsonld/{entity_type}/{entity_id}.jsonld
    This is stored in entities.jsonld_path and used by both
    the writer (process_entity task) and reader (jsonld_router).
    """
    return f"{site_id}/jsonld/{entity_type}/{entity_id}.jsonld"


def create_or_update_entity(db: Session, payload: dict, site_id: str):
    validate_entity(payload)

    entity_type = payload["entity_type"]
    entity_id = payload["entity_id"]
    name = payload["name"]
    attributes = payload.get("attributes", {})

    composite_id = f"{site_id}:{entity_type}:{entity_id}"
    canonical_url = f"/entities/{entity_type}/{entity_id}"
    jsonld_path = get_jsonld_path(site_id, entity_type, entity_id)

    existing = db.query(Entity).filter(Entity.id == composite_id).first()
    if existing:
        existing.name = name
        existing.attributes = attributes
        existing.status = "pending"
        existing.jsonld_path = jsonld_path  # update to GCS path
        db.commit()
        db.refresh(existing)
        return existing

    new_entity = Entity(
        id=composite_id,
        site_id=site_id,
        entity_id=entity_id,
        entity_type=entity_type,
        name=name,
        attributes=attributes,
        canonical_url=canonical_url,
        jsonld_path=jsonld_path,
        brand=attributes.get("brand"),
        author=attributes.get("author"),
        status="pending",
    )
    db.add(new_entity)
    db.commit()
    db.refresh(new_entity)
    return new_entity


def delete_entity(db: Session, entity_id: str) -> bool:
    entity = db.query(Entity).filter(Entity.id == entity_id).first()
    if not entity:
        return False
    # No disk file to delete — GCS files are cleaned up separately if needed
    db.delete(entity)
    db.commit()
    return True