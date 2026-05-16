"""迭代下的需求条目 CRUD。

权限：登录用户均可读写（与客户面状态非管理员字段一致）。
新增/删除某条需求需要登录即可；如果未来需要收紧，再加 require_admin。
"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

import models
import schemas
from database import get_db

router = APIRouter(prefix="/api/iteration-requirements", tags=["iteration-requirements"])


@router.get("", response_model=List[schemas.IterationRequirementOut])
def list_by_iteration(
    iteration_id: int = Query(..., description="迭代 ID"),
    db: Session = Depends(get_db),
):
    items = (
        db.query(models.IterationRequirement)
        .filter(models.IterationRequirement.iteration_id == iteration_id)
        .order_by(models.IterationRequirement.seq.asc(), models.IterationRequirement.id.asc())
        .all()
    )
    return items


@router.post("", response_model=schemas.IterationRequirementOut)
def create_item(payload: schemas.IterationRequirementCreate, db: Session = Depends(get_db)):
    parent = (
        db.query(models.AnnualIteration)
        .filter(models.AnnualIteration.id == payload.iteration_id)
        .first()
    )
    if not parent:
        raise HTTPException(status_code=404, detail="所属迭代不存在")
    # 序号自动取当前最大值+1（如果调用方没传或传 0）
    data = payload.model_dump()
    if not data.get("seq"):
        max_seq = (
            db.query(models.IterationRequirement)
            .filter(models.IterationRequirement.iteration_id == payload.iteration_id)
            .count()
        )
        data["seq"] = max_seq + 1
    item = models.IterationRequirement(**data)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.put("/{item_id}", response_model=schemas.IterationRequirementOut)
def update_item(item_id: int, payload: schemas.IterationRequirementUpdate, db: Session = Depends(get_db)):
    item = (
        db.query(models.IterationRequirement)
        .filter(models.IterationRequirement.id == item_id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(item, k, v)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{item_id}")
def delete_item(item_id: int, db: Session = Depends(get_db)):
    item = (
        db.query(models.IterationRequirement)
        .filter(models.IterationRequirement.id == item_id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(item)
    db.commit()
    return {"ok": True}
