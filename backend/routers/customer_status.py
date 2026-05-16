"""客户面状态 CRUD + PPT 导出。

权限矩阵：
- 列表 GET：所有登录用户
- 新增 POST / 删除 DELETE：仅 admin
- 编辑 PUT：
    机台编号 / 客户(battlefield) / 型号(model) —— 创建后锁定，路由层拒绝任何修改
    current_stage / field_version / attention_level —— 仅 admin 可改
    customer_status / recent_focus / key_issues   —— 所有登录用户均可改
- 导出 PPT：仅 admin
"""
import io
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

import models
import schemas
from auth import get_current_user, require_admin
from database import get_db

router = APIRouter(prefix="/api/customer-status", tags=["customer-status"])

_ADMIN_ONLY_FIELDS = {"current_stage", "field_version", "attention_level"}
_USER_FIELDS = {"customer_status", "recent_focus", "key_issues"}


@router.get("", response_model=List[schemas.CustomerStatusOut])
def list_items(db: Session = Depends(get_db)):
    return db.query(models.CustomerStatus).order_by(models.CustomerStatus.id.desc()).all()


@router.post("", response_model=schemas.CustomerStatusOut)
def create_item(
    payload: schemas.CustomerStatusCreate,
    db: Session = Depends(get_db),
    _: models.User = Depends(require_admin),
):
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
def update_item(
    item_id: int,
    payload: schemas.CustomerStatusUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    item = db.query(models.CustomerStatus).filter(models.CustomerStatus.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    changes = payload.model_dump(exclude_unset=True)
    is_admin = current_user.role == "admin"
    for k, v in changes.items():
        if k in _ADMIN_ONLY_FIELDS and not is_admin:
            raise HTTPException(status_code=403, detail=f"字段「{k}」仅管理员可修改")
        if k not in _ADMIN_ONLY_FIELDS and k not in _USER_FIELDS:
            # schema 已经只保留可改字段，这里兜底防御
            raise HTTPException(status_code=400, detail=f"字段「{k}」不允许修改")
        setattr(item, k, v)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{item_id}")
def delete_item(
    item_id: int,
    db: Session = Depends(get_db),
    _: models.User = Depends(require_admin),
):
    item = db.query(models.CustomerStatus).filter(models.CustomerStatus.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(item)
    db.commit()
    return {"ok": True}


@router.get("/export.pptx")
def export_pptx(
    db: Session = Depends(get_db),
    _: models.User = Depends(require_admin),
):
    """导出当前所有客户面状态为 PPT（单页表格）。"""
    from pptx_utils import build_customer_status_pptx

    rows = db.query(models.CustomerStatus).order_by(models.CustomerStatus.id.asc()).all()
    stream = build_customer_status_pptx(rows)
    filename = f"customer-status-{datetime.now().strftime('%Y%m%d-%H%M%S')}.pptx"
    return StreamingResponse(
        stream,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
