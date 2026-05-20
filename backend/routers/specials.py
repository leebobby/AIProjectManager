"""专项管理：
- 专项元数据（slug/name/owner/sort_order/is_active）：admin 增删改
- 单专项的内容/事务/风险：任意登录用户可写（参照客户面状态进展字段惯例）
- 全景图：admin 上传，登录用户可下载
"""
import pathlib
import re
import uuid
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

import models
import schemas
from auth import get_current_user, require_admin
from database import get_db
from op_log import log_op

router = APIRouter(prefix="/api/specials", tags=["specials"])

UPLOAD_ROOT = pathlib.Path(__file__).resolve().parent.parent / "uploads" / "specials"
_SLUG_PAT = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}$")


def _ensure_dir(p: pathlib.Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def _get_or_404(db: Session, sid: int) -> models.Special:
    item = db.query(models.Special).filter(models.Special.id == sid).first()
    if not item:
        raise HTTPException(404, "专项不存在")
    return item


def _ensure_content(db: Session, special: models.Special) -> models.SpecialContent:
    if special.content:
        return special.content
    c = models.SpecialContent(special_id=special.id)
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


# ─── Specials list ─────────────────────────────────────────────────

@router.get("", response_model=List[schemas.SpecialOut])
def list_specials(
    include_inactive: bool = False,
    db: Session = Depends(get_db),
):
    q = db.query(models.Special)
    if not include_inactive:
        q = q.filter(models.Special.is_active.is_(True))
    return q.order_by(models.Special.sort_order, models.Special.id).all()


@router.post("", response_model=schemas.SpecialOut)
def create_special(
    payload: schemas.SpecialCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(require_admin),
):
    if not _SLUG_PAT.match(payload.slug):
        raise HTTPException(400, "slug 仅支持字母/数字/下划线/连字符，长度 1-64")
    if db.query(models.Special).filter(models.Special.slug == payload.slug).first():
        raise HTTPException(400, "slug 已存在")
    item = models.Special(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    # 创建对应的空 content
    db.add(models.SpecialContent(special_id=item.id))
    db.commit()
    log_op(db, action="新增", target="专项", target_id=item.id,
           detail=f"slug={item.slug} name={item.name}",
           user=current_admin, request=request)
    return item


@router.put("/{sid}", response_model=schemas.SpecialOut)
def update_special(
    sid: int,
    payload: schemas.SpecialUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(require_admin),
):
    item = _get_or_404(db, sid)
    data = payload.model_dump(exclude_unset=True)
    if "slug" in data:
        if not _SLUG_PAT.match(data["slug"]):
            raise HTTPException(400, "slug 仅支持字母/数字/下划线/连字符")
        if data["slug"] != item.slug:
            if db.query(models.Special).filter(models.Special.slug == data["slug"]).first():
                raise HTTPException(400, "slug 已存在")
    for k, v in data.items():
        setattr(item, k, v)
    db.commit()
    db.refresh(item)
    log_op(db, action="修改", target="专项", target_id=item.id,
           detail=f"slug={item.slug} fields={','.join(data.keys()) or '无'}",
           user=current_admin, request=request)
    return item


@router.delete("/{sid}")
def delete_special(
    sid: int,
    request: Request,
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(require_admin),
):
    item = _get_or_404(db, sid)
    snapshot = f"slug={item.slug} name={item.name}"
    # 清理全景图文件
    if item.content and item.content.panorama_image_path:
        try:
            p = (UPLOAD_ROOT.parent / item.content.panorama_image_path).resolve()
            if p.exists():
                p.unlink()
        except OSError:
            pass
    db.delete(item)
    db.commit()
    log_op(db, action="删除", target="专项", target_id=sid,
           detail=snapshot, user=current_admin, request=request)
    return {"ok": True}


# ─── 详情 ──────────────────────────────────────────────────────────

@router.get("/by-slug/{slug}", response_model=schemas.SpecialDetailOut)
def get_by_slug(slug: str, db: Session = Depends(get_db)):
    item = db.query(models.Special).filter(models.Special.slug == slug).first()
    if not item:
        raise HTTPException(404, "专项不存在")
    _ensure_content(db, item)
    return item


@router.get("/{sid}", response_model=schemas.SpecialDetailOut)
def get_one(sid: int, db: Session = Depends(get_db)):
    item = _get_or_404(db, sid)
    _ensure_content(db, item)
    return item


@router.put("/{sid}/content", response_model=schemas.SpecialContentOut)
def update_content(
    sid: int,
    payload: schemas.SpecialContentUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    special = _get_or_404(db, sid)
    content = _ensure_content(db, special)
    if content.version != payload.version:
        raise HTTPException(409, "数据已被他人修改，请刷新后重试")
    data = payload.model_dump(exclude_unset=True)
    data.pop("version", None)
    for k, v in data.items():
        setattr(content, k, v)
    content.version += 1
    db.commit()
    db.refresh(content)
    log_op(db, action="修改", target="专项内容", target_id=sid,
           detail=f"slug={special.slug} fields={','.join(data.keys()) or '无'}",
           user=current_user, request=request)
    return content


# ─── 全景图上传/下载 ────────────────────────────────────────────────

@router.post("/{sid}/panorama", response_model=schemas.SpecialContentOut)
def upload_panorama(
    sid: int,
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(require_admin),
):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(400, "仅支持图片文件")
    special = _get_or_404(db, sid)
    content = _ensure_content(db, special)

    # 写入新文件
    sub = UPLOAD_ROOT / str(sid)
    _ensure_dir(sub)
    orig_name = file.filename or "panorama.png"
    safe_ext = pathlib.Path(orig_name).suffix[:16] or ".png"
    stored = f"{uuid.uuid4().hex}{safe_ext}"
    full = sub / stored
    with open(full, "wb") as f:
        while True:
            chunk = file.file.read(64 * 1024)
            if not chunk:
                break
            f.write(chunk)

    # 删旧
    if content.panorama_image_path:
        try:
            old = (UPLOAD_ROOT.parent / content.panorama_image_path).resolve()
            if old.exists() and old != full.resolve():
                old.unlink()
        except OSError:
            pass

    content.panorama_image_path = f"specials/{sid}/{stored}"
    content.panorama_image_name = orig_name
    content.version += 1
    db.commit()
    db.refresh(content)
    log_op(db, action="修改", target="专项全景图", target_id=sid,
           detail=f"slug={special.slug} file={orig_name}",
           user=current_admin, request=request)
    return content


@router.get("/{sid}/panorama")
def get_panorama(sid: int, db: Session = Depends(get_db)):
    special = _get_or_404(db, sid)
    if not special.content or not special.content.panorama_image_path:
        raise HTTPException(404, "全景图未上传")
    p = (UPLOAD_ROOT.parent / special.content.panorama_image_path).resolve()
    if not p.exists():
        raise HTTPException(404, "全景图文件已丢失")
    return FileResponse(str(p))


# ─── 事务 / 风险 (合并实现) ─────────────────────────────────────────

def _item_model(kind: str):
    return models.SpecialTask if kind == "task" else models.SpecialRisk


def _action_target(kind: str) -> str:
    return "专项事务" if kind == "task" else "风险问题"


@router.get("/{sid}/tasks", response_model=List[schemas.SpecialItemOut])
def list_tasks(sid: int, db: Session = Depends(get_db)):
    _get_or_404(db, sid)
    return (
        db.query(models.SpecialTask)
        .filter(models.SpecialTask.special_id == sid)
        .order_by(models.SpecialTask.sort_order, models.SpecialTask.id)
        .all()
    )


@router.get("/{sid}/risks", response_model=List[schemas.SpecialItemOut])
def list_risks(sid: int, db: Session = Depends(get_db)):
    _get_or_404(db, sid)
    return (
        db.query(models.SpecialRisk)
        .filter(models.SpecialRisk.special_id == sid)
        .order_by(models.SpecialRisk.sort_order, models.SpecialRisk.id)
        .all()
    )


def _create_item(
    kind: str,
    sid: int,
    payload: schemas.SpecialItemBase,
    db: Session,
    user: models.User,
    request: Request,
):
    _get_or_404(db, sid)
    Model = _item_model(kind)
    data = payload.model_dump(exclude_unset=True)
    if not data.get("seq"):
        cnt = db.query(Model).filter(Model.special_id == sid).count()
        data["seq"] = cnt + 1
    if not data.get("sort_order"):
        data["sort_order"] = data["seq"]
    item = Model(special_id=sid, **data)
    db.add(item)
    db.commit()
    db.refresh(item)
    log_op(db, action="新增", target=_action_target(kind), target_id=item.id,
           detail=f"special_id={sid} content={(item.content or '')[:60]}",
           user=user, request=request)
    return item


def _update_item(
    kind: str,
    item_id: int,
    payload: schemas.SpecialItemUpdate,
    db: Session,
    user: models.User,
    request: Request,
):
    Model = _item_model(kind)
    item = db.query(Model).filter(Model.id == item_id).first()
    if not item:
        raise HTTPException(404, "条目不存在")
    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(item, k, v)
    db.commit()
    db.refresh(item)
    log_op(db, action="修改", target=_action_target(kind), target_id=item.id,
           detail=f"special_id={item.special_id} fields={','.join(data.keys()) or '无'}",
           user=user, request=request)
    return item


def _delete_item(
    kind: str,
    item_id: int,
    db: Session,
    user: models.User,
    request: Request,
):
    Model = _item_model(kind)
    item = db.query(Model).filter(Model.id == item_id).first()
    if not item:
        raise HTTPException(404, "条目不存在")
    snapshot = f"special_id={item.special_id} content={(item.content or '')[:60]}"
    db.delete(item)
    db.commit()
    log_op(db, action="删除", target=_action_target(kind), target_id=item_id,
           detail=snapshot, user=user, request=request)
    return {"ok": True}


@router.post("/{sid}/tasks", response_model=schemas.SpecialItemOut)
def create_task(
    sid: int,
    payload: schemas.SpecialItemBase,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return _create_item("task", sid, payload, db, current_user, request)


@router.put("/tasks/{item_id}", response_model=schemas.SpecialItemOut)
def update_task(
    item_id: int,
    payload: schemas.SpecialItemUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return _update_item("task", item_id, payload, db, current_user, request)


@router.delete("/tasks/{item_id}")
def delete_task(
    item_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return _delete_item("task", item_id, db, current_user, request)


@router.post("/{sid}/risks", response_model=schemas.SpecialItemOut)
def create_risk(
    sid: int,
    payload: schemas.SpecialItemBase,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return _create_item("risk", sid, payload, db, current_user, request)


@router.put("/risks/{item_id}", response_model=schemas.SpecialItemOut)
def update_risk(
    item_id: int,
    payload: schemas.SpecialItemUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return _update_item("risk", item_id, payload, db, current_user, request)


@router.delete("/risks/{item_id}")
def delete_risk(
    item_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return _delete_item("risk", item_id, db, current_user, request)
