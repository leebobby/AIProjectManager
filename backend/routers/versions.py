"""遗留版本表（只读）。

新版本工作走两层结构 major_versions + iteration_versions（见 major_versions.py），
版本管理页早已切换到 majorVersionApi。这里仅保留一个 GET 供项目简介页读取旧数据，
写接口已下线——历史上它们对所有登录用户开放，属于过松且无人调用的攻击面。
"""
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import models
import schemas
from database import get_db

router = APIRouter(prefix="/api/versions", tags=["versions"])


@router.get("", response_model=List[schemas.VersionOut])
def list_items(db: Session = Depends(get_db)):
    return db.query(models.Version).order_by(models.Version.released_at.desc()).all()
