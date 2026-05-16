from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from database import Base


class CustomerStatus(Base):
    __tablename__ = "customer_status"

    id = Column(Integer, primary_key=True, index=True)
    machine_id = Column(String(64), nullable=False, comment="机台编号")
    battlefield = Column(String(128), nullable=False, comment="客户（原战场）")
    model = Column(String(128), default="", comment="型号")
    current_stage = Column(String(128), nullable=False, comment="当前阶段")
    field_version = Column(String(128), default="", comment="现场版本")
    attention_level = Column(Integer, default=0, comment="近期关注度: 0 未评估 / 1-5 星")
    customer_status = Column(String(256), nullable=False, comment="当前进展")
    recent_focus = Column(Text, default="", comment="近期现场关键诉求")
    key_issues = Column(Text, default="", comment="软件类风险和问题")
    issue_url = Column(String(512), default="", comment="问题单链接")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Version(Base):
    __tablename__ = "versions"

    id = Column(Integer, primary_key=True, index=True)
    version_no = Column(String(64), nullable=False, comment="版本号")
    title = Column(String(256), nullable=False, comment="标题")
    description = Column(Text, default="", comment="版本说明")
    release_url = Column(String(512), default="", comment="跳转链接")
    released_at = Column(DateTime, default=datetime.utcnow, comment="发布时间")


class Iteration(Base):
    """旧版迭代表 —— 保留兼容，新业务请用 AnnualIteration。"""
    __tablename__ = "iterations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(128), nullable=False, comment="迭代名称")
    goal = Column(Text, default="", comment="迭代目标")
    start_date = Column(DateTime, nullable=True, comment="开始时间")
    end_date = Column(DateTime, nullable=True, comment="结束时间")
    status = Column(String(32), default="planning", comment="状态")
    owner = Column(String(64), default="", comment="负责人")


class AnnualIteration(Base):
    """按年度规划的迭代：每年 12 个，每月一个。"""
    __tablename__ = "annual_iterations"
    __table_args__ = (UniqueConstraint("year", "month", name="uq_year_month"),)

    id = Column(Integer, primary_key=True, index=True)
    year = Column(Integer, nullable=False, index=True, comment="年份")
    month = Column(Integer, nullable=False, comment="月份 1-12")
    name = Column(String(128), default="", comment="迭代名称")
    owner = Column(String(64), default="", comment="负责人")
    status = Column(String(32), default="planning", comment="状态: planning/in_progress/done")
    goal = Column(Text, default="", comment="迭代目标/备注")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    requirements = relationship(
        "IterationRequirement",
        back_populates="iteration",
        cascade="all, delete-orphan",
        order_by="IterationRequirement.seq",
    )


class IterationRequirement(Base):
    """迭代下的需求条目，含 6 个交付进展子状态。"""
    __tablename__ = "iteration_requirements"

    id = Column(Integer, primary_key=True, index=True)
    iteration_id = Column(Integer, ForeignKey("annual_iterations.id", ondelete="CASCADE"), nullable=False, index=True)
    seq = Column(Integer, default=0, comment="序号（排序用）")
    req_no = Column(String(64), default="", comment="需求编号")
    req_url = Column(String(512), default="", comment="需求超链接")
    title = Column(String(256), default="", comment="需求标题")
    owner = Column(String(64), default="", comment="交付责任人")
    priority = Column(String(16), default="P2", comment="优先级 P0/P1/P2/P3")
    planned_version = Column(String(64), default="", comment="计划交付版本")

    # 6 个交付进展子项：状态枚举 "未开始/进行中/已完成/已延期/不涉及"
    progress_walkthrough = Column(String(16), default="未开始", comment="需求串讲")
    progress_reverse = Column(String(16), default="未开始", comment="反串讲")
    progress_stc = Column(String(16), default="未开始", comment="STC设计")
    progress_coding = Column(String(16), default="未开始", comment="编码")
    progress_bbit = Column(String(16), default="未开始", comment="BBIT")
    progress_clarify = Column(String(16), default="未开始", comment="转测澄清")

    remark = Column(Text, default="", comment="备注（是否存在变更等）")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    iteration = relationship("AnnualIteration", back_populates="requirements")


class RoadmapProject(Base):
    """首页项目里程碑：一个产品下可以挂多个项目。"""
    __tablename__ = "roadmap_projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(128), nullable=False, comment="项目名称")
    description = Column(String(256), default="", comment="副标题/简要描述")
    year = Column(Integer, nullable=True, comment="年份（可选，仅展示）")
    granularity = Column(String(16), default="quarter", comment="精度: quarter / month")
    sort_order = Column(Integer, default=0, comment="排序")
    is_active = Column(Boolean, default=True, comment="是否在首页展示")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    phases = relationship(
        "RoadmapPhase",
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="RoadmapPhase.sort_order",
    )
    milestones = relationship(
        "RoadmapMilestone",
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="(RoadmapMilestone.year, RoadmapMilestone.month, RoadmapMilestone.sort_order)",
    )


class RoadmapPhase(Base):
    """路线图上方阶段块：含锚点、彩色标题、目标/核心产品/应用场景文本。"""
    __tablename__ = "roadmap_phases"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("roadmap_projects.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(64), nullable=False, comment="阶段名称")
    color = Column(String(16), default="#409EFF", comment="阶段主色 #RRGGBB")
    start_year = Column(Integer, nullable=False, default=lambda: datetime.utcnow().year, comment="起始年份")
    start_month = Column(Integer, nullable=False, comment="起始月份 1-12")
    end_year = Column(Integer, nullable=False, default=lambda: datetime.utcnow().year, comment="结束年份")
    end_month = Column(Integer, nullable=False, comment="结束月份 1-12")
    goal = Column(Text, default="", comment="目标（多行）")
    core_products = Column(String(256), default="", comment="核心产品")
    scenarios = Column(Text, default="", comment="主要应用场景（多行）")
    sort_order = Column(Integer, default=0, comment="排序")

    project = relationship("RoadmapProject", back_populates="phases")


class RoadmapMilestone(Base):
    """时间轴下方月份卡片：产品名 + 描述。"""
    __tablename__ = "roadmap_milestones"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("roadmap_projects.id", ondelete="CASCADE"), nullable=False, index=True)
    year = Column(Integer, nullable=False, default=lambda: datetime.utcnow().year, comment="年份")
    month = Column(Integer, nullable=False, comment="月份 1-12")
    title = Column(String(128), default="", comment="产品/版本名（蓝框文字）")
    description = Column(Text, default="", comment="描述文字")
    sort_order = Column(Integer, default=0, comment="同月内排序")

    project = relationship("RoadmapProject", back_populates="milestones")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), unique=True, nullable=False, index=True, comment="登录名")
    full_name = Column(String(128), default="", comment="姓名")
    password_hash = Column(String(256), default="", comment="密码哈希(本地账户)")
    role = Column(String(16), default="normal", comment="admin / normal")
    auth_provider = Column(String(32), default="local", comment="local / company_sso (预留)")
    is_active = Column(Boolean, default=True, comment="是否启用")
    created_at = Column(DateTime, default=datetime.utcnow)
