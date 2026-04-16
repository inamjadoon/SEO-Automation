from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.workers.tasks import process_entity
from app.database import SessionLocal
from app.models.entity import Entity
from app.schemas.entity import EntityCreate
from app.services import entity_service



router = APIRouter()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/entities/")
def create_entity(entity: EntityCreate):
    with SessionLocal() as db:
        # Create entity in DB with status = pending
        composite_id = f"{entity.entity_type}:{entity.entity_id}"
        e = db.query(Entity).filter(Entity.id == composite_id).first()
        if not e:
            from app.services.entity_service import create_or_update_entity
            e = create_or_update_entity(db, entity.dict())

    # Trigger async processing using the entity ID
    process_entity.delay(e.id)

    return {"message": "Entity accepted, processing started", "entity_id": e.id}



# GET endpoint
@router.get("/entities/")
def list_entities(db: Session = Depends(get_db)):
    entities = db.query(Entity).all()
    return [
        {
            "id": e.id,
            "entity_id": e.entity_id,
            "entity_type": e.entity_type,
            "name": e.name,
            "attributes": e.attributes,
            "jsonld_path": e.jsonld_path
        }
        for e in entities
    ]

# GET: retrieve a single entity by ID
@router.get("/entities/{entity_id}")
def get_entity(entity_id: str):
    with SessionLocal() as db:
        entity = db.query(Entity).filter(Entity.id == entity_id).first()
        if not entity:
            raise HTTPException(status_code=404, detail="Entity not found")
        return {
            "id": entity.id,
            "entity_id": entity.entity_id,
            "entity_type": entity.entity_type,
            "name": entity.name,
            "attributes": entity.attributes,
            "jsonld_path": entity.jsonld_path
        }
    

@router.put("/entities/{entity_id}")
def update_entity(entity_id: str, updated: EntityCreate):
    with SessionLocal() as db:
        entity = db.query(Entity).filter(Entity.id == entity_id).first()
        if not entity:
            raise HTTPException(status_code=404, detail="Entity not found")

        # Update fields and reset status
        entity.name = updated.name
        entity.attributes = updated.attributes
        entity.status = "pending"
        db.commit()
        db.refresh(entity)

    # Trigger async processing
    process_entity.delay(entity.id)

    return {"message": "Entity update triggered", "entity_id": entity.id}



@router.delete("/entities/{entity_id}")
def delete_entity_route(entity_id: str, db: Session = Depends(get_db)):
    success = entity_service.delete_entity(db, entity_id)
    if not success:
        raise HTTPException(status_code=404, detail="Entity not found")
    return {"detail": "Entity deleted successfully"}

