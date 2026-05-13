from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import models
import schemas
from database import get_db

router = APIRouter(prefix="/api/versions", tags=["versions"])


@router.get("", response_model=List[schemas.VersionOut])
def list_items(db: Session = Depends(get_db)):
    return db.query(models.Version).order_by(models.Version.released_at.desc()).all()


@router.post("", response_model=schemas.VersionOut)
def create_item(payload: schemas.VersionCreate, db: Session = Depends(get_db)):
    item = models.Version(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.put("/{item_id}", response_model=schemas.VersionOut)
def update_item(item_id: int, payload: schemas.VersionUpdate, db: Session = Depends(get_db)):
    item = db.query(models.Version).filter(models.Version.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    for k, v in payload.model_dump().items():
        setattr(item, k, v)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{item_id}")
def delete_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(models.Version).filter(models.Version.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(item)
    db.commit()
    return {"ok": True}
