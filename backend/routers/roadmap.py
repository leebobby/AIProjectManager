"""项目里程碑（首页路线图）相关接口。

- GET 接口：任意登录用户可访问。
- POST/PUT/DELETE：需要管理员权限。
"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import models
import schemas
from auth import require_admin
from database import get_db

router = APIRouter(prefix="/api/roadmap", tags=["roadmap"])


# ===== 项目 =====
@router.get("/projects", response_model=List[schemas.RoadmapProjectDetailOut])
def list_projects(db: Session = Depends(get_db), include_inactive: bool = False):
    q = db.query(models.RoadmapProject)
    if not include_inactive:
        q = q.filter(models.RoadmapProject.is_active.is_(True))
    q = q.order_by(models.RoadmapProject.sort_order.asc(), models.RoadmapProject.id.asc())
    return q.all()


@router.get("/projects/{project_id}", response_model=schemas.RoadmapProjectDetailOut)
def get_project(project_id: int, db: Session = Depends(get_db)):
    item = db.query(models.RoadmapProject).filter(models.RoadmapProject.id == project_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="项目不存在")
    return item


@router.post(
    "/projects",
    response_model=schemas.RoadmapProjectDetailOut,
    dependencies=[Depends(require_admin)],
)
def create_project(payload: schemas.RoadmapProjectCreate, db: Session = Depends(get_db)):
    item = models.RoadmapProject(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.put(
    "/projects/{project_id}",
    response_model=schemas.RoadmapProjectDetailOut,
    dependencies=[Depends(require_admin)],
)
def update_project(
    project_id: int,
    payload: schemas.RoadmapProjectUpdate,
    db: Session = Depends(get_db),
):
    item = db.query(models.RoadmapProject).filter(models.RoadmapProject.id == project_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="项目不存在")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(item, k, v)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/projects/{project_id}", dependencies=[Depends(require_admin)])
def delete_project(project_id: int, db: Session = Depends(get_db)):
    item = db.query(models.RoadmapProject).filter(models.RoadmapProject.id == project_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="项目不存在")
    db.delete(item)
    db.commit()
    return {"ok": True}


# ===== 阶段 =====
def _validate_month_range(start_month: int, end_month: int):
    if not (1 <= start_month <= 12 and 1 <= end_month <= 12):
        raise HTTPException(status_code=400, detail="月份需在 1-12 之间")
    if end_month < start_month:
        raise HTTPException(status_code=400, detail="结束月份不能早于起始月份")


@router.post(
    "/phases",
    response_model=schemas.RoadmapPhaseOut,
    dependencies=[Depends(require_admin)],
)
def create_phase(payload: schemas.RoadmapPhaseCreate, db: Session = Depends(get_db)):
    project = db.query(models.RoadmapProject).filter(models.RoadmapProject.id == payload.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    _validate_month_range(payload.start_month, payload.end_month)
    item = models.RoadmapPhase(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.put(
    "/phases/{phase_id}",
    response_model=schemas.RoadmapPhaseOut,
    dependencies=[Depends(require_admin)],
)
def update_phase(
    phase_id: int,
    payload: schemas.RoadmapPhaseUpdate,
    db: Session = Depends(get_db),
):
    item = db.query(models.RoadmapPhase).filter(models.RoadmapPhase.id == phase_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="阶段不存在")
    data = payload.model_dump(exclude_unset=True)
    start = data.get("start_month", item.start_month)
    end = data.get("end_month", item.end_month)
    _validate_month_range(start, end)
    for k, v in data.items():
        setattr(item, k, v)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/phases/{phase_id}", dependencies=[Depends(require_admin)])
def delete_phase(phase_id: int, db: Session = Depends(get_db)):
    item = db.query(models.RoadmapPhase).filter(models.RoadmapPhase.id == phase_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="阶段不存在")
    db.delete(item)
    db.commit()
    return {"ok": True}


# ===== 里程碑 =====
def _validate_month(month: int):
    if not (1 <= month <= 12):
        raise HTTPException(status_code=400, detail="月份需在 1-12 之间")


@router.post(
    "/milestones",
    response_model=schemas.RoadmapMilestoneOut,
    dependencies=[Depends(require_admin)],
)
def create_milestone(payload: schemas.RoadmapMilestoneCreate, db: Session = Depends(get_db)):
    project = db.query(models.RoadmapProject).filter(models.RoadmapProject.id == payload.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    _validate_month(payload.month)
    item = models.RoadmapMilestone(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.put(
    "/milestones/{milestone_id}",
    response_model=schemas.RoadmapMilestoneOut,
    dependencies=[Depends(require_admin)],
)
def update_milestone(
    milestone_id: int,
    payload: schemas.RoadmapMilestoneUpdate,
    db: Session = Depends(get_db),
):
    item = db.query(models.RoadmapMilestone).filter(models.RoadmapMilestone.id == milestone_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="里程碑不存在")
    data = payload.model_dump(exclude_unset=True)
    if "month" in data:
        _validate_month(data["month"])
    for k, v in data.items():
        setattr(item, k, v)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/milestones/{milestone_id}", dependencies=[Depends(require_admin)])
def delete_milestone(milestone_id: int, db: Session = Depends(get_db)):
    item = db.query(models.RoadmapMilestone).filter(models.RoadmapMilestone.id == milestone_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="里程碑不存在")
    db.delete(item)
    db.commit()
    return {"ok": True}
