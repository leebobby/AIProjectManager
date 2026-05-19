from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

import models
import schemas
from auth import hash_password, require_admin
from database import get_db
from op_log import log_op

router = APIRouter(
    prefix="/api/users",
    tags=["users"],
    dependencies=[Depends(require_admin)],
)


@router.get("", response_model=List[schemas.UserOut])
def list_users(db: Session = Depends(get_db)):
    return db.query(models.User).order_by(models.User.id.asc()).all()


@router.post("", response_model=schemas.UserOut)
def create_user(
    payload: schemas.UserCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(require_admin),
):
    if db.query(models.User).filter(models.User.username == payload.username).first():
        raise HTTPException(status_code=400, detail="用户名已存在")
    if payload.role not in ("admin", "normal"):
        raise HTTPException(status_code=400, detail="role 只能是 admin 或 normal")
    user = models.User(
        username=payload.username,
        full_name=payload.full_name or "",
        password_hash=hash_password(payload.password),
        role=payload.role or "normal",
        auth_provider="local",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    log_op(db, action="新增", target="用户", target_id=user.id,
           detail=f"username={user.username} role={user.role}",
           user=current_admin, request=request)
    return user


@router.put("/{user_id}", response_model=schemas.UserOut)
def update_user(
    user_id: int,
    payload: schemas.UserUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(require_admin),
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    changed = []
    if payload.full_name is not None and payload.full_name != user.full_name:
        user.full_name = payload.full_name
        changed.append("full_name")
    if payload.role is not None:
        if payload.role not in ("admin", "normal"):
            raise HTTPException(status_code=400, detail="role 只能是 admin 或 normal")
        if user.id == current_admin.id and payload.role != "admin":
            raise HTTPException(status_code=400, detail="不能修改自己的管理员角色")
        if user.role != payload.role:
            user.role = payload.role
            changed.append(f"role->{payload.role}")
    if payload.is_active is not None:
        if user.id == current_admin.id and not payload.is_active:
            raise HTTPException(status_code=400, detail="不能禁用自己")
        if user.is_active != payload.is_active:
            user.is_active = payload.is_active
            changed.append(f"is_active->{payload.is_active}")
    if payload.password:
        user.password_hash = hash_password(payload.password)
        changed.append("password")

    db.commit()
    db.refresh(user)
    log_op(db, action="修改", target="用户", target_id=user.id,
           detail=f"username={user.username} fields={','.join(changed) or '无变化'}",
           user=current_admin, request=request)
    return user


@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(require_admin),
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if user.id == current_admin.id:
        raise HTTPException(status_code=400, detail="不能删除自己")
    snapshot = f"username={user.username}"
    db.delete(user)
    db.commit()
    log_op(db, action="删除", target="用户", target_id=user_id,
           detail=snapshot, user=current_admin, request=request)
    return {"ok": True}
