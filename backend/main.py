from datetime import datetime

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

import models
from auth import get_current_user, hash_password
from database import Base, SessionLocal, engine
from migrate import ensure_schema
from routers import annual_iterations, iteration_requirements
from routers import auth as auth_router
from routers import config as config_router
from routers import customer_status, iterations, users, versions

# 先做轻量迁移（给老库加列），再 create_all 补齐缺失的表。
ensure_schema()
Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Project Manager")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 公开路由（登录/注册不需要 token）
app.include_router(auth_router.router)

# 业务路由：全部需要登录
authed = [Depends(get_current_user)]
app.include_router(customer_status.router, dependencies=authed)
app.include_router(versions.router, dependencies=authed)
app.include_router(iterations.router, dependencies=authed)
app.include_router(annual_iterations.router, dependencies=authed)
app.include_router(iteration_requirements.router, dependencies=authed)
app.include_router(config_router.router, dependencies=authed)

# 用户管理：路由内部已挂 require_admin
app.include_router(users.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}


def seed_initial_data():
    """首次启动注入：默认 admin 账户 + 少量业务示例数据。"""
    db = SessionLocal()
    try:
        if db.query(models.User).count() == 0:
            db.add(models.User(
                username="admin",
                full_name="超级管理员",
                password_hash=hash_password("admin123"),
                role="admin",
                auth_provider="local",
                is_active=True,
            ))

        if db.query(models.CustomerStatus).count() == 0:
            db.add_all([
                models.CustomerStatus(
                    machine_id="M-001",
                    battlefield="华东客户A",
                    model="X-100",
                    current_stage="T3 Release",
                    field_version="v2.1.3",
                    attention_level=2,
                    customer_status="客户验收顺利,本周计划增订 5 台",
                    recent_focus="良率提升至 98%",
                    key_issues="",
                ),
                models.CustomerStatus(
                    machine_id="M-002",
                    battlefield="华南客户B",
                    model="X-200",
                    current_stage="T1-T2",
                    field_version="v2.0.5-rc2",
                    attention_level=5,
                    customer_status="客户反馈偶发停机,正在协调驻场",
                    recent_focus="解决偶发停机问题",
                    key_issues="主控板偶发复位,正在定位",
                ),
            ])

        if db.query(models.Version).count() == 0:
            db.add(models.Version(
                version_no="v1.0.0",
                title="首发版本",
                description="项目管理系统首个可用版本",
                release_url="https://example.com/release/v1.0.0",
                released_at=datetime(2026, 5, 1),
            ))

        if db.query(models.Iteration).count() == 0:
            db.add(models.Iteration(
                name="Sprint-1 基础框架",
                goal="搭建前后端项目骨架,完成 4 个页面 + 用户管理",
                status="in_progress",
                owner="admin",
            ))

        # 当前年度 12 个迭代占位 + 1 个示例需求
        current_year = datetime.now().year
        has_year = (
            db.query(models.AnnualIteration)
            .filter(models.AnnualIteration.year == current_year)
            .count()
        )
        if has_year == 0:
            for m in range(1, 13):
                db.add(models.AnnualIteration(
                    year=current_year,
                    month=m,
                    name=f"{current_year}年{m}月迭代",
                    status="planning",
                ))
            db.flush()
            current_month_it = (
                db.query(models.AnnualIteration)
                .filter(
                    models.AnnualIteration.year == current_year,
                    models.AnnualIteration.month == datetime.now().month,
                )
                .first()
            )
            if current_month_it:
                current_month_it.status = "in_progress"
                current_month_it.owner = "admin"
                db.add(models.IterationRequirement(
                    iteration_id=current_month_it.id,
                    seq=1,
                    req_no="REQ-2026-001",
                    req_url="https://example.com/req/2026-001",
                    title="客户面状态页增加型号字段",
                    owner="admin",
                    priority="P1",
                    planned_version="v0.5.0",
                    progress_walkthrough="已完成",
                    progress_reverse="已完成",
                    progress_stc="进行中",
                    progress_coding="进行中",
                    progress_bbit="未开始",
                    progress_clarify="未开始",
                ))
        db.commit()
    finally:
        db.close()


seed_initial_data()
