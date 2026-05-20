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
    version = Column(Integer, nullable=False, default=0, comment="乐观锁版本号")
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
    owner_group = Column(String(64), default="", comment="PL组")
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

    version = Column(Integer, nullable=False, default=0, comment="乐观锁版本号")
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
    major_versions = relationship(
        "MajorVersion",
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="MajorVersion.sort_order",
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
    version = Column(Integer, nullable=False, default=0, comment="乐观锁版本号")

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


class MajorVersion(Base):
    """大版本：归属于某个里程碑项目，包含若干迭代版本。"""
    __tablename__ = "major_versions"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("roadmap_projects.id", ondelete="SET NULL"), nullable=True, index=True)
    version_no = Column(String(64), nullable=False, comment="大版本号")
    title = Column(String(256), default="", comment="标题")
    description = Column(Text, default="", comment="版本说明")
    range_start = Column(DateTime, nullable=True, comment="版本范围开始")
    range_end = Column(DateTime, nullable=True, comment="版本范围结束")
    actual_release_date = Column(DateTime, nullable=True, comment="实际发布时间")
    sort_order = Column(Integer, default=0, comment="排序")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    project = relationship("RoadmapProject", back_populates="major_versions")
    iteration_versions = relationship(
        "IterationVersion",
        back_populates="major_version",
        cascade="all, delete-orphan",
        order_by="IterationVersion.sort_order",
    )


class IterationVersion(Base):
    """迭代版本：隶属于大版本，预计每周一个。"""
    __tablename__ = "iteration_versions"

    id = Column(Integer, primary_key=True, index=True)
    major_version_id = Column(Integer, ForeignKey("major_versions.id", ondelete="CASCADE"), nullable=False, index=True)
    version_no = Column(String(64), nullable=False, comment="迭代版本号")
    title = Column(String(256), default="", comment="标题")
    planned_date = Column(DateTime, nullable=True, comment="预计发布日期")
    sort_order = Column(Integer, default=0, comment="排序")
    created_at = Column(DateTime, default=datetime.utcnow)

    major_version = relationship("MajorVersion", back_populates="iteration_versions")


class StakeholderProjectContact(Base):
    """项目组沟通地图条目（两列表格）"""
    __tablename__ = "stakeholder_project_contacts"

    id = Column(Integer, primary_key=True, index=True)
    sort_order = Column(Integer, default=0, comment="排序")
    col1 = Column(String(256), default="", comment="列1（角色）")
    col2 = Column(String(256), default="", comment="列2（姓名/工号）")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class StakeholderBattlefield(Base):
    """战场沟通矩阵条目（六列表格）"""
    __tablename__ = "stakeholder_battlefields"

    id = Column(Integer, primary_key=True, index=True)
    sort_order = Column(Integer, default=0, comment="排序")
    battlefield = Column(String(128), default="", comment="战场")
    region = Column(String(128), default="", comment="地域")
    service = Column(String(256), default="", comment="服务")
    contact1 = Column(Text, default="", comment="联系方式（服务）")
    apps = Column(String(256), default="", comment="APPS")
    contact2 = Column(Text, default="", comment="联系方式（APPS）")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ProjectFormationImage(Base):
    """项目阵型图：全局单张图片/SVG，存 id=1 这一行。"""
    __tablename__ = "project_formation_image"

    id = Column(Integer, primary_key=True, index=True)
    image_path = Column(String(512), default="", comment="服务器相对路径")
    image_name = Column(String(256), default="", comment="原文件名")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ProjectFormationMember(Base):
    """项目阵型 人员名单：投入人员 + 挂靠情况。"""
    __tablename__ = "project_formation_members"

    id = Column(Integer, primary_key=True, index=True)
    sort_order = Column(Integer, default=0)
    name = Column(String(64), nullable=False, comment="姓名")
    emp_no = Column(String(64), default="", comment="工号")
    pl_group = Column(String(64), default="", comment="PL组")
    role = Column(String(64), default="", comment="角色 / 岗位")
    special_attach = Column(String(128), default="", comment="挂靠专项 / 攻关")
    allocation = Column(String(32), default="", comment="投入比例 (如 0.5 / 30% / 全职)")
    remark = Column(Text, default="", comment="备注")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


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


class HandbookCategory(Base):
    """项目一本通：自定义分类（流程/规范/PPT模板/...）"""
    __tablename__ = "handbook_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(64), nullable=False, comment="分类名称")
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    items = relationship(
        "HandbookItem",
        back_populates="category",
        cascade="all, delete-orphan",
        order_by="HandbookItem.sort_order",
    )


class HandbookItem(Base):
    __tablename__ = "handbook_items"

    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("handbook_categories.id", ondelete="CASCADE"),
                         nullable=False, index=True)
    title = Column(String(256), nullable=False, comment="标题")
    kind = Column(String(16), default="link", comment="link / file")
    url = Column(String(1024), default="", comment="外链 URL (kind=link)")
    file_path = Column(String(512), default="", comment="服务器相对路径 (kind=file)")
    file_name = Column(String(256), default="", comment="原始文件名 (kind=file)")
    file_size = Column(Integer, default=0, comment="文件大小 字节")
    description = Column(Text, default="")
    owner = Column(String(64), default="")
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    category = relationship("HandbookCategory", back_populates="items")


class Special(Base):
    """专项 / 攻关：每条 = 一项工作（左侧二级菜单 + 一个详情页）"""
    __tablename__ = "specials"

    id = Column(Integer, primary_key=True, index=True)
    # slug 历史字段，保留兼容；新数据不再依赖。
    slug = Column(String(64), default="", index=True, comment="历史字段，不再使用")
    kind = Column(String(16), default="special", comment="special=专项 / assault=攻关")
    name = Column(String(128), nullable=False, comment="名称")
    owner = Column(String(64), default="", comment="责任人")
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    email_to = Column(String(512), default="", comment="周报默认主送，逗号分隔")
    email_cc = Column(String(512), default="", comment="周报默认抄送，逗号分隔")
    email_subject_tpl = Column(String(256), default="", comment="周报默认主题模板")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    content = relationship(
        "SpecialContent", uselist=False, back_populates="special",
        cascade="all, delete-orphan",
    )
    tasks = relationship(
        "SpecialTask", back_populates="special",
        cascade="all, delete-orphan", order_by="SpecialTask.sort_order",
    )
    risks = relationship(
        "SpecialRisk", back_populates="special",
        cascade="all, delete-orphan", order_by="SpecialRisk.sort_order",
    )


class SpecialContent(Base):
    """单个专项的"页面富字段"，1:1 与 specials。"""
    __tablename__ = "special_contents"

    id = Column(Integer, primary_key=True, index=True)
    special_id = Column(Integer, ForeignKey("specials.id", ondelete="CASCADE"),
                        unique=True, nullable=False, index=True)
    goal = Column(Text, default="", comment="专项目标")
    progress_summary = Column(Text, default="", comment="一句话进展&求助")
    panorama_image_path = Column(String(512), default="", comment="专项全景图：服务器相对路径")
    panorama_image_name = Column(String(256), default="")
    # 里程碑：[{name,date,status}]
    milestones_json = Column(Text, default="[]")
    # 阵型：{"headers":[...], "rows":[[cell, cell, ...], ...]}
    formation_json = Column(Text, default='{"headers":[],"rows":[]}')
    # 事务区域附加的若干"自由表格"：[{title, headers, rows}, ...]
    extra_grids_json = Column(Text, default="[]")
    version = Column(Integer, nullable=False, default=0, comment="乐观锁")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    special = relationship("Special", back_populates="content")


class SpecialTask(Base):
    """专项/攻关 事务表的一行。"""
    __tablename__ = "special_tasks"
    id = Column(Integer, primary_key=True, index=True)
    special_id = Column(Integer, ForeignKey("specials.id", ondelete="CASCADE"),
                        nullable=False, index=True)
    seq = Column(Integer, default=0)
    content = Column(Text, default="", comment="事务内容")
    progress = Column(Text, default="", comment="当前进展")
    owner = Column(String(64), default="", comment="责任人")
    planned_close_date = Column(String(32), default="", comment="计划闭环时间")
    status = Column(String(16), default="open", comment="open / closed")
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    special = relationship("Special", back_populates="tasks")


class SpecialRisk(Base):
    """风险/问题表的一行（结构与事务同）。"""
    __tablename__ = "special_risks"
    id = Column(Integer, primary_key=True, index=True)
    special_id = Column(Integer, ForeignKey("specials.id", ondelete="CASCADE"),
                        nullable=False, index=True)
    seq = Column(Integer, default=0)
    content = Column(Text, default="", comment="问题内容")
    progress = Column(Text, default="", comment="当前进展")
    owner = Column(String(64), default="", comment="责任人")
    planned_close_date = Column(String(32), default="", comment="计划闭环时间")
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    special = relationship("Special", back_populates="risks")


class OperationLog(Base):
    """登录与关键业务写操作日志，供管理员审计。"""
    __tablename__ = "operation_logs"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    user_id = Column(Integer, nullable=True, index=True, comment="登录失败时可为空")
    username = Column(String(64), default="", index=True, comment="冗余存储,便于查询")
    action = Column(String(32), nullable=False, index=True, comment="登录/登出/登录失败/新增/修改/删除/...")
    target = Column(String(64), default="", index=True, comment="目标类型,如 用户/客户面状态/...")
    target_id = Column(String(64), default="", comment="目标主键,可为空")
    detail = Column(Text, default="", comment="补充说明 (摘要,不存敏感字段)")
    ip = Column(String(64), default="")
    user_agent = Column(String(256), default="")
