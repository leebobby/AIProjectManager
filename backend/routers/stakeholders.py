"""干系人管理：项目组沟通地图 + 战场沟通矩阵 CRUD。

权限：读取 — 所有登录用户；写入 — 仅 admin。
"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import models
import schemas
from auth import require_admin
from database import get_db

router = APIRouter(prefix="/api/stakeholders", tags=["stakeholders"])


# ── 项目组沟通地图 ──────────────────────────────────────────

@router.get("/project-contacts", response_model=List[schemas.ProjectContactOut])
def list_project_contacts(db: Session = Depends(get_db)):
    return (
        db.query(models.StakeholderProjectContact)
        .order_by(models.StakeholderProjectContact.sort_order,
                  models.StakeholderProjectContact.id)
        .all()
    )


@router.post("/project-contacts", response_model=schemas.ProjectContactOut)
def create_project_contact(
    payload: schemas.ProjectContactCreate,
    db: Session = Depends(get_db),
    _: models.User = Depends(require_admin),
):
    max_order = db.query(models.StakeholderProjectContact).count()
    item = models.StakeholderProjectContact(**payload.model_dump(), sort_order=max_order)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.put("/project-contacts/{item_id}", response_model=schemas.ProjectContactOut)
def update_project_contact(
    item_id: int,
    payload: schemas.ProjectContactUpdate,
    db: Session = Depends(get_db),
    _: models.User = Depends(require_admin),
):
    item = db.query(models.StakeholderProjectContact).filter(
        models.StakeholderProjectContact.id == item_id
    ).first()
    if not item:
        raise HTTPException(404, "Not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(item, k, v)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/project-contacts/{item_id}")
def delete_project_contact(
    item_id: int,
    db: Session = Depends(get_db),
    _: models.User = Depends(require_admin),
):
    item = db.query(models.StakeholderProjectContact).filter(
        models.StakeholderProjectContact.id == item_id
    ).first()
    if not item:
        raise HTTPException(404, "Not found")
    db.delete(item)
    db.commit()
    return {"ok": True}


# ── 战场沟通矩阵 ──────────────────────────────────────────

@router.get("/battlefields", response_model=List[schemas.BattlefieldOut])
def list_battlefields(db: Session = Depends(get_db)):
    return (
        db.query(models.StakeholderBattlefield)
        .order_by(models.StakeholderBattlefield.sort_order,
                  models.StakeholderBattlefield.id)
        .all()
    )


@router.post("/battlefields", response_model=schemas.BattlefieldOut)
def create_battlefield(
    payload: schemas.BattlefieldCreate,
    db: Session = Depends(get_db),
    _: models.User = Depends(require_admin),
):
    max_order = db.query(models.StakeholderBattlefield).count()
    item = models.StakeholderBattlefield(**payload.model_dump(), sort_order=max_order)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.put("/battlefields/{item_id}", response_model=schemas.BattlefieldOut)
def update_battlefield(
    item_id: int,
    payload: schemas.BattlefieldUpdate,
    db: Session = Depends(get_db),
    _: models.User = Depends(require_admin),
):
    item = db.query(models.StakeholderBattlefield).filter(
        models.StakeholderBattlefield.id == item_id
    ).first()
    if not item:
        raise HTTPException(404, "Not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(item, k, v)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/battlefields/{item_id}")
def delete_battlefield(
    item_id: int,
    db: Session = Depends(get_db),
    _: models.User = Depends(require_admin),
):
    item = db.query(models.StakeholderBattlefield).filter(
        models.StakeholderBattlefield.id == item_id
    ).first()
    if not item:
        raise HTTPException(404, "Not found")
    db.delete(item)
    db.commit()
    return {"ok": True}
