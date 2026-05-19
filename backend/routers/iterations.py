from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

import models
import schemas
from auth import get_current_user
from database import get_db
from op_log import log_op

router = APIRouter(prefix="/api/iterations", tags=["iterations"])


@router.get("", response_model=List[schemas.IterationOut])
def list_items(db: Session = Depends(get_db)):
    return db.query(models.Iteration).order_by(models.Iteration.id.desc()).all()


@router.post("", response_model=schemas.IterationOut)
def create_item(
    payload: schemas.IterationCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    item = models.Iteration(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    log_op(db, action="新增", target="迭代", target_id=item.id,
           detail=f"name={item.name}", user=current_user, request=request)
    return item


@router.put("/{item_id}", response_model=schemas.IterationOut)
def update_item(
    item_id: int,
    payload: schemas.IterationUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    item = db.query(models.Iteration).filter(models.Iteration.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    for k, v in payload.model_dump().items():
        setattr(item, k, v)
    db.commit()
    db.refresh(item)
    log_op(db, action="修改", target="迭代", target_id=item.id,
           detail=f"name={item.name}", user=current_user, request=request)
    return item


@router.delete("/{item_id}")
def delete_item(
    item_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    item = db.query(models.Iteration).filter(models.Iteration.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    snapshot = f"name={item.name}"
    db.delete(item)
    db.commit()
    log_op(db, action="删除", target="迭代", target_id=item_id,
           detail=snapshot, user=current_user, request=request)
    return {"ok": True}
