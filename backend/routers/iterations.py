"""遗留迭代表（只读）。

新迭代工作走年度网格 annual_iterations + iteration_requirements，
迭代管理页早已切换到 annualIterationApi。这里仅保留 GET 兜底旧数据，
写接口已下线——历史上它们对所有登录用户开放，属于过松且无人调用的攻击面。
"""
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import models
import schemas
from database import get_db

router = APIRouter(prefix="/api/iterations", tags=["iterations"])


@router.get("", response_model=List[schemas.IterationOut])
def list_items(db: Session = Depends(get_db)):
    return db.query(models.Iteration).order_by(models.Iteration.id.desc()).all()
