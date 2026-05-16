"""年度迭代 CRUD + 单迭代 PPT 导出。

- 列表按年份过滤；缺失的月份会被自动补齐为占位行（status=planning, name=空）。
- 元数据编辑（name/owner/status/goal）：仅 admin。
- 新增 / 删除：仅 admin。
"""
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import distinct
from sqlalchemy.orm import Session

import models
import schemas
from auth import get_current_user, require_admin
from database import get_db

router = APIRouter(prefix="/api/annual-iterations", tags=["annual-iterations"])


def _ensure_year(db: Session, year: int):
    """确保该年份的 12 个月迭代都存在；缺失则创建占位行。"""
    existing = {
        it.month for it in
        db.query(models.AnnualIteration).filter(models.AnnualIteration.year == year).all()
    }
    missing = [m for m in range(1, 13) if m not in existing]
    if missing:
        for m in missing:
            db.add(models.AnnualIteration(
                year=year,
                month=m,
                name=f"{year}年{m}月迭代",
                status="planning",
            ))
        db.commit()


@router.get("/years", response_model=List[int])
def list_years(db: Session = Depends(get_db)):
    """返回所有有数据的年份，含当前自然年。"""
    rows = db.query(distinct(models.AnnualIteration.year)).all()
    years = {r[0] for r in rows}
    years.add(datetime.now().year)
    return sorted(years, reverse=True)


@router.get("", response_model=List[schemas.AnnualIterationOut])
def list_by_year(
    year: int = Query(..., description="年份，如 2026"),
    db: Session = Depends(get_db),
):
    _ensure_year(db, year)
    items = (
        db.query(models.AnnualIteration)
        .filter(models.AnnualIteration.year == year)
        .order_by(models.AnnualIteration.month.asc())
        .all()
    )
    return items


@router.get("/{item_id}", response_model=schemas.AnnualIterationOut)
def get_one(item_id: int, db: Session = Depends(get_db)):
    item = db.query(models.AnnualIteration).filter(models.AnnualIteration.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    return item


@router.put("/{item_id}", response_model=schemas.AnnualIterationOut)
def update_item(
    item_id: int,
    payload: schemas.AnnualIterationUpdate,
    db: Session = Depends(get_db),
    _: models.User = Depends(require_admin),
):
    item = db.query(models.AnnualIteration).filter(models.AnnualIteration.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(item, k, v)
    db.commit()
    db.refresh(item)
    return item


@router.get("/{item_id}/export.pptx")
def export_pptx(
    item_id: int,
    db: Session = Depends(get_db),
    _: models.User = Depends(require_admin),
):
    from pptx_utils import build_iteration_pptx

    item = db.query(models.AnnualIteration).filter(models.AnnualIteration.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    reqs = (
        db.query(models.IterationRequirement)
        .filter(models.IterationRequirement.iteration_id == item_id)
        .order_by(models.IterationRequirement.seq.asc(), models.IterationRequirement.id.asc())
        .all()
    )
    stream = build_iteration_pptx(item, reqs)
    filename = f"iteration-{item.year}-{item.month:02d}-{datetime.now().strftime('%H%M%S')}.pptx"
    return StreamingResponse(
        stream,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
