from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import models
import schemas
from database import get_db

router = APIRouter(prefix="/api/iterations", tags=["iterations"])


@router.get("", response_model=List[schemas.IterationOut])
def list_items(db: Session = Depends(get_db)):
    return db.query(models.Iteration).order_by(models.Iteration.id.desc()).all()


@router.post("", response_model=schemas.IterationOut)
def create_item(payload: schemas.IterationCreate, db: Session = Depends(get_db)):
    item = models.Iteration(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.put("/{item_id}", response_model=schemas.IterationOut)
def update_item(item_id: int, payload: schemas.IterationUpdate, db: Session = Depends(get_db)):
    item = db.query(models.Iteration).filter(models.Iteration.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    for k, v in payload.model_dump().items():
        setattr(item, k, v)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{item_id}")
def delete_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(models.Iteration).filter(models.Iteration.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(item)
    db.commit()
    return {"ok": True}
