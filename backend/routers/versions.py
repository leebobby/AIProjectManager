from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

import models
import schemas
from auth import get_current_user
from database import get_db
from op_log import log_op

router = APIRouter(prefix="/api/versions", tags=["versions"])


@router.get("", response_model=List[schemas.VersionOut])
def list_items(db: Session = Depends(get_db)):
    return db.query(models.Version).order_by(models.Version.released_at.desc()).all()


@router.post("", response_model=schemas.VersionOut)
def create_item(
    payload: schemas.VersionCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    item = models.Version(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    log_op(db, action="新增", target="版本", target_id=item.id,
           detail=f"version_no={item.version_no}",
           user=current_user, request=request)
    return item


@router.put("/{item_id}", response_model=schemas.VersionOut)
def update_item(
    item_id: int,
    payload: schemas.VersionUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    item = db.query(models.Version).filter(models.Version.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    for k, v in payload.model_dump().items():
        setattr(item, k, v)
    db.commit()
    db.refresh(item)
    log_op(db, action="修改", target="版本", target_id=item.id,
           detail=f"version_no={item.version_no}",
           user=current_user, request=request)
    return item


@router.delete("/{item_id}")
def delete_item(
    item_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    item = db.query(models.Version).filter(models.Version.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    snapshot = f"version_no={item.version_no}"
    db.delete(item)
    db.commit()
    log_op(db, action="删除", target="版本", target_id=item_id,
           detail=snapshot, user=current_user, request=request)
    return {"ok": True}
