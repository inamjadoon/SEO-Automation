
# app/workers/tasks.py
from app.workers.celery_app import celery_app
from app.database import SessionLocal
from app.models.entity import Entity
from app.services.jsonld import generate_jsonld
import os
@celery_app.task
def process_entity(entity_id: str):
    with SessionLocal() as db:
        entity = db.query(Entity).filter(Entity.id == entity_id).first()
        if not entity:
            return f"Entity {entity_id} not found"

        entity.status = "processing"
        db.commit()

        try:
            if entity.jsonld_path and os.path.exists(entity.jsonld_path):
                os.remove(entity.jsonld_path)
                
            jsonld_path = generate_jsonld(
            entity.entity_type,
            entity.entity_id,
            entity.name,
            entity.attributes,
            canonical_url=entity.canonical_url,
            brand=entity.brand,
            author=entity.author
            )

            entity.jsonld_path = jsonld_path
            entity.status = "completed"

        except Exception as e:
            entity.status = "failed"
            print(f"Error generating JSON-LD: {e}")

        db.commit()

    return f"Entity {entity_id} processed"