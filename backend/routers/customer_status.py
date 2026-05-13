from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import models
import schemas
from database import get_db

router = APIRouter(prefix="/api/customer-status", tags=["customer-status"])


@router.get("", response_model=List[schemas.CustomerStatusOut])
def list_items(db: Session = Depends(get_db)):
    return db.query(models.CustomerStatus).order_by(models.CustomerStatus.id.desc()).all()


@router.post("", response_model=schemas.CustomerStatusOut)
def create_item(payload: schemas.CustomerStatusCreate, db: Session = Depends(get_db)):
    exists = (
        db.query(models.CustomerStatus)
        .filter(models.CustomerStatus.machine_id == payload.machine_id)
        .first()
    )
    if exists:
        raise HTTPException(status_code=400, detail="机台编号已存在")
    item = models.CustomerStatus(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.put("/{item_id}", response_model=schemas.CustomerStatusOut)
def update_item(item_id: int, payload: schemas.CustomerStatusUpdate, db: Session = Depends(get_db)):
    """编辑接口仅允许修改 4 个字段，machine_id / battlefield 在创建后锁定。"""
    item = db.query(models.CustomerStatus).filter(models.CustomerStatus.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(item, k, v)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{item_id}")
def delete_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(models.CustomerStatus).filter(models.CustomerStatus.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(item)
    db.commit()
    return {"ok": True}
