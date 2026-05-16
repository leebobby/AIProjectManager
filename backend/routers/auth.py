from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import models
import schemas
from auth import create_access_token, get_current_user, hash_password, verify_password
from database import get_db

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=schemas.TokenResponse)
def login(payload: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == payload.username).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    if user.auth_provider != "local":
        raise HTTPException(status_code=400, detail="该账号需通过企业 SSO 登录")
    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    token = create_access_token({"sub": user.username, "role": user.role})
    return schemas.TokenResponse(access_token=token, user=user)


@router.post("/register", response_model=schemas.UserOut)
def register(payload: schemas.RegisterRequest, db: Session = Depends(get_db)):
    """自助注册：固定 normal 角色，账户默认启用。"""
    if db.query(models.User).filter(models.User.username == payload.username).first():
        raise HTTPException(status_code=400, detail="用户名已存在")
    user = models.User(
        username=payload.username,
        password_hash=hash_password(payload.password),
        full_name=payload.full_name or "",
        role="normal",
        auth_provider="local",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get("/me", response_model=schemas.UserOut)
def me(current_user: models.User = Depends(get_current_user)):
    return current_user


@router.post("/change-password")
def change_password(
    payload: schemas.PasswordChangeRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """当前登录用户修改自己的密码。"""
    if current_user.auth_provider != "local":
        raise HTTPException(status_code=400, detail="非本地账号无法在此修改密码")
    if not verify_password(payload.old_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="原密码不正确")
    if not payload.new_password or len(payload.new_password) < 6:
        raise HTTPException(status_code=400, detail="新密码至少 6 位")
    current_user.password_hash = hash_password(payload.new_password)
    db.commit()
    return {"ok": True}
