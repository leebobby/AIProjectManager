"""成员出差管理（协作编辑域）。

谁、去哪个战场（关联客户主数据）、哪段时间、什么事由。状态按起止日期实时
推导（计划中/进行中/已完成/已取消），不入库。登录用户均可读写，带乐观锁。
新表由 create_all 自动建。
"""
from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

import models
import schemas
from auth import get_current_user
from database import get_db
from op_log import log_op

router = APIRouter(prefix="/api/business-trips", tags=["business-trips"])


# ─── helpers ─────────────────────────────────────────────────────────────────
def _user_map(db: Session) -> dict:
    """{user_id: (展示名, 所属 PL 组名)}。"""
    rows = (
        db.query(models.User.id, models.User.full_name, models.User.username,
                 models.ResourceGroup.name.label("group_name"))
        .outerjoin(models.ResourceGroup, models.User.group_id == models.ResourceGroup.id)
        .all()
    )
    return {r.id: ((r.full_name or r.username or ""), (r.group_name or "")) for r in rows}


def _cust_map(db: Session) -> dict:
    rows = db.query(models.Customer.id, models.Customer.code, models.Customer.display_name).all()
    return {r.id: (r.display_name or r.code) for r in rows}


def _status(obj: models.BusinessTrip) -> str:
    if obj.cancelled:
        return "已取消"
    today = date.today()
    s = obj.start_date.date() if obj.start_date else None
    e = obj.end_date.date() if obj.end_date else None
    if s and e:
        if today < s:
            return "计划中"
        if today > e:
            return "已完成"
        return "进行中"
    if s and not e:
        return "进行中" if today >= s else "计划中"
    if e and not s:
        return "已完成" if today > e else "进行中"
    return "计划中"


def _trip_out(obj: models.BusinessTrip, umap: dict, cmap: dict) -> schemas.BusinessTripOut:
    out = schemas.BusinessTripOut.model_validate(obj)
    name, group = umap.get(obj.user_id, (None, None))
    out.user_name = name
    out.user_group = group
    out.customer_name = cmap.get(obj.customer_id)
    out.status = _status(obj)
    return out


# ─── CRUD ────────────────────────────────────────────────────────────────────
@router.get("", response_model=List[schemas.BusinessTripOut])
def list_trips(
    user_id: Optional[int] = Query(None),
    customer_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(models.BusinessTrip)
    if user_id is not None:
        q = q.filter(models.BusinessTrip.user_id == user_id)
    if customer_id is not None:
        q = q.filter(models.BusinessTrip.customer_id == customer_id)
    # 起止日期靠后的排前面（SQLite 下 DESC 时 NULL 自然殿后），再按 id
    rows = q.order_by(models.BusinessTrip.start_date.desc(),
                      models.BusinessTrip.id.desc()).all()
    umap, cmap = _user_map(db), _cust_map(db)
    return [_trip_out(r, umap, cmap) for r in rows]


@router.get("/dashboard", response_model=schemas.BusinessTripDashboardOut)
def dashboard(db: Session = Depends(get_db)):
    """统一看板：当前在差 / 计划中 / 本月人次 + 各战场分布。"""
    rows = db.query(models.BusinessTrip).all()
    umap, cmap = _user_map(db), _cust_map(db)

    today = date.today()
    on_now = planned = this_month = 0
    by_cust: dict = {}  # name -> {current, planned, total}

    for r in rows:
        if r.cancelled:
            continue
        st = _status(r)
        cname = cmap.get(r.customer_id) or "未指定"
        slot = by_cust.setdefault(cname, {"current": 0, "planned": 0, "total": 0})
        slot["total"] += 1
        if st == "进行中":
            on_now += 1
            slot["current"] += 1
        elif st == "计划中":
            planned += 1
            slot["planned"] += 1
        # 本月人次：与当月有交集
        s = r.start_date.date() if r.start_date else None
        e = r.end_date.date() if r.end_date else None
        if s or e:
            ms = date(today.year, today.month, 1)
            me = date(today.year + (today.month // 12), (today.month % 12) + 1, 1)  # 下月 1 号
            lo = s or e
            hi = e or s
            if lo < me and hi >= ms:
                this_month += 1

    stats = [
        schemas.TripCustomerStat(customer_name=k, current=v["current"],
                                 planned=v["planned"], total=v["total"])
        for k, v in by_cust.items()
    ]
    stats.sort(key=lambda x: (-x.current, -x.total, x.customer_name))
    return schemas.BusinessTripDashboardOut(
        on_trip_now=on_now, planned=planned, this_month=this_month, by_customer=stats,
    )


@router.post("", response_model=schemas.BusinessTripOut)
def create_trip(
    payload: schemas.BusinessTripCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    obj = models.BusinessTrip(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    log_op(db, action="新增", target="成员出差", target_id=obj.id,
           detail=f"user_id={obj.user_id} customer_id={obj.customer_id}",
           user=current_user, request=request)
    return _trip_out(obj, _user_map(db), _cust_map(db))


@router.put("/{trip_id}", response_model=schemas.BusinessTripOut)
def update_trip(
    trip_id: int,
    payload: schemas.BusinessTripUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    obj = db.query(models.BusinessTrip).filter(models.BusinessTrip.id == trip_id).first()
    if not obj:
        raise HTTPException(404, "Not found")
    if obj.version != payload.version:
        raise HTTPException(409, "数据已被他人修改，请刷新后重试")
    changes = payload.model_dump(exclude_unset=True)
    changes.pop("version", None)
    for k, v in changes.items():
        setattr(obj, k, v)
    obj.version += 1
    db.commit()
    db.refresh(obj)
    log_op(db, action="修改", target="成员出差", target_id=obj.id,
           detail=f"fields={','.join(changes.keys()) or '无'}",
           user=current_user, request=request)
    return _trip_out(obj, _user_map(db), _cust_map(db))


@router.delete("/{trip_id}")
def delete_trip(
    trip_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    obj = db.query(models.BusinessTrip).filter(models.BusinessTrip.id == trip_id).first()
    if not obj:
        raise HTTPException(404, "Not found")
    db.delete(obj)
    db.commit()
    log_op(db, action="删除", target="成员出差", target_id=trip_id,
           detail="", user=current_user, request=request)
    return {"ok": True}
