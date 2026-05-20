from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


# Pydantic v2 把 model_ 视为受保护命名空间，CustomerStatus 里有个 `model` 列，
# 这里全局放开，避免警告/冲突。
_BASE_CONFIG = ConfigDict(from_attributes=True, protected_namespaces=())


# ===== CustomerStatus =====
class CustomerStatusBase(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    machine_id: str
    battlefield: str
    model: Optional[str] = ""
    current_stage: str
    field_version: Optional[str] = ""
    attention_level: Optional[int] = 0
    customer_status: str
    recent_focus: Optional[str] = ""
    key_issues: Optional[str] = ""
    issue_url: Optional[str] = ""


class CustomerStatusCreate(CustomerStatusBase):
    pass


class CustomerStatusUpdate(BaseModel):
    """编辑允许的字段；机台编号/客户/型号 创建后锁定，由后端忽略。
    管理员字段：current_stage / field_version / attention_level / issue_url
    所有用户：customer_status / recent_focus / key_issues
    路由层按角色再做校验。
    """
    model_config = ConfigDict(protected_namespaces=())

    version: int
    current_stage: Optional[str] = None
    field_version: Optional[str] = None
    attention_level: Optional[int] = None
    issue_url: Optional[str] = None
    customer_status: Optional[str] = None
    recent_focus: Optional[str] = None
    key_issues: Optional[str] = None


class CustomerStatusOut(CustomerStatusBase):
    id: int
    version: int
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


# ===== Version =====
class VersionBase(BaseModel):
    version_no: str
    title: str
    description: Optional[str] = ""
    release_url: Optional[str] = ""
    released_at: Optional[datetime] = None


class VersionCreate(VersionBase):
    pass


class VersionUpdate(VersionBase):
    pass


class VersionOut(VersionBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


# ===== Iteration (legacy) =====
class IterationBase(BaseModel):
    name: str
    goal: Optional[str] = ""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: Optional[str] = "planning"
    owner: Optional[str] = ""


class IterationCreate(IterationBase):
    pass


class IterationUpdate(IterationBase):
    pass


class IterationOut(IterationBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


# ===== AnnualIteration =====
class AnnualIterationBase(BaseModel):
    year: int
    month: int
    name: Optional[str] = ""
    owner: Optional[str] = ""
    status: Optional[str] = "planning"
    goal: Optional[str] = ""


class AnnualIterationCreate(AnnualIterationBase):
    pass


class AnnualIterationUpdate(BaseModel):
    name: Optional[str] = None
    owner: Optional[str] = None
    status: Optional[str] = None
    goal: Optional[str] = None


class AnnualIterationOut(AnnualIterationBase):
    id: int
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ===== IterationRequirement =====
class IterationRequirementBase(BaseModel):
    seq: Optional[int] = 0
    req_no: Optional[str] = ""
    req_url: Optional[str] = ""
    title: Optional[str] = ""
    owner: Optional[str] = ""
    priority: Optional[str] = "P2"
    planned_version: Optional[str] = ""
    progress_walkthrough: Optional[str] = "未开始"
    progress_reverse: Optional[str] = "未开始"
    progress_stc: Optional[str] = "未开始"
    progress_coding: Optional[str] = "未开始"
    progress_bbit: Optional[str] = "未开始"
    progress_clarify: Optional[str] = "未开始"
    remark: Optional[str] = ""


class IterationRequirementCreate(IterationRequirementBase):
    iteration_id: int


class IterationRequirementUpdate(BaseModel):
    version: int
    seq: Optional[int] = None
    req_no: Optional[str] = None
    req_url: Optional[str] = None
    title: Optional[str] = None
    owner: Optional[str] = None
    priority: Optional[str] = None
    planned_version: Optional[str] = None
    progress_walkthrough: Optional[str] = None
    progress_reverse: Optional[str] = None
    progress_stc: Optional[str] = None
    progress_coding: Optional[str] = None
    progress_bbit: Optional[str] = None
    progress_clarify: Optional[str] = None
    remark: Optional[str] = None


class IterationRequirementOut(IterationRequirementBase):
    id: int
    iteration_id: int
    version: int

    model_config = ConfigDict(from_attributes=True)


# ===== Roadmap =====
class RoadmapPhaseBase(BaseModel):
    name: str
    color: Optional[str] = "#409EFF"
    start_year: int
    start_month: int
    end_year: int
    end_month: int
    goal: Optional[str] = ""
    core_products: Optional[str] = ""
    scenarios: Optional[str] = ""
    sort_order: Optional[int] = 0


class RoadmapPhaseCreate(RoadmapPhaseBase):
    project_id: int


class RoadmapPhaseUpdate(BaseModel):
    version: int
    name: Optional[str] = None
    color: Optional[str] = None
    start_year: Optional[int] = None
    start_month: Optional[int] = None
    end_year: Optional[int] = None
    end_month: Optional[int] = None
    goal: Optional[str] = None
    core_products: Optional[str] = None
    scenarios: Optional[str] = None
    sort_order: Optional[int] = None


class RoadmapPhaseOut(RoadmapPhaseBase):
    id: int
    project_id: int
    version: int

    model_config = ConfigDict(from_attributes=True)


class RoadmapMilestoneBase(BaseModel):
    year: int
    month: int
    title: Optional[str] = ""
    description: Optional[str] = ""
    sort_order: Optional[int] = 0


class RoadmapMilestoneCreate(RoadmapMilestoneBase):
    project_id: int


class RoadmapMilestoneUpdate(BaseModel):
    year: Optional[int] = None
    month: Optional[int] = None
    title: Optional[str] = None
    description: Optional[str] = None
    sort_order: Optional[int] = None


class RoadmapMilestoneOut(RoadmapMilestoneBase):
    id: int
    project_id: int

    model_config = ConfigDict(from_attributes=True)


class RoadmapProjectBase(BaseModel):
    name: str
    description: Optional[str] = ""
    year: Optional[int] = None
    granularity: Optional[str] = "quarter"
    sort_order: Optional[int] = 0
    is_active: Optional[bool] = True


class RoadmapProjectCreate(RoadmapProjectBase):
    pass


class RoadmapProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    year: Optional[int] = None
    granularity: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class RoadmapProjectOut(RoadmapProjectBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class RoadmapProjectDetailOut(RoadmapProjectOut):
    phases: List[RoadmapPhaseOut] = []
    milestones: List[RoadmapMilestoneOut] = []


# ===== MajorVersion / IterationVersion =====
class IterationVersionBase(BaseModel):
    version_no: str
    title: Optional[str] = ""
    planned_date: Optional[datetime] = None
    sort_order: Optional[int] = 0


class IterationVersionCreate(IterationVersionBase):
    major_version_id: int


class IterationVersionUpdate(BaseModel):
    version_no: Optional[str] = None
    title: Optional[str] = None
    planned_date: Optional[datetime] = None
    sort_order: Optional[int] = None


class IterationVersionOut(IterationVersionBase):
    id: int
    major_version_id: int

    model_config = ConfigDict(from_attributes=True)


class MajorVersionBase(BaseModel):
    version_no: str
    title: Optional[str] = ""
    description: Optional[str] = ""
    range_start: Optional[datetime] = None
    range_end: Optional[datetime] = None
    actual_release_date: Optional[datetime] = None
    sort_order: Optional[int] = 0


class MajorVersionCreate(MajorVersionBase):
    project_id: Optional[int] = None


class MajorVersionUpdate(BaseModel):
    version_no: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    range_start: Optional[datetime] = None
    range_end: Optional[datetime] = None
    actual_release_date: Optional[datetime] = None
    sort_order: Optional[int] = None


class MajorVersionOut(MajorVersionBase):
    id: int
    project_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class MajorVersionDetailOut(MajorVersionOut):
    iteration_versions: List[IterationVersionOut] = []


# ===== Stakeholder =====
class ProjectContactBase(BaseModel):
    col1: Optional[str] = ""
    col2: Optional[str] = ""


class ProjectContactCreate(ProjectContactBase):
    pass


class ProjectContactUpdate(ProjectContactBase):
    pass


class ProjectContactOut(ProjectContactBase):
    id: int
    sort_order: int = 0

    model_config = ConfigDict(from_attributes=True)


class BattlefieldBase(BaseModel):
    battlefield: Optional[str] = ""
    region: Optional[str] = ""
    service: Optional[str] = ""
    contact1: Optional[str] = ""
    apps: Optional[str] = ""
    contact2: Optional[str] = ""


class BattlefieldCreate(BattlefieldBase):
    pass


class BattlefieldUpdate(BattlefieldBase):
    pass


class BattlefieldOut(BattlefieldBase):
    id: int
    sort_order: int = 0

    model_config = ConfigDict(from_attributes=True)


# ===== Auth / User =====
class UserBase(BaseModel):
    username: str
    full_name: Optional[str] = ""


class UserCreate(UserBase):
    password: str
    role: Optional[str] = "normal"


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None


class UserOut(BaseModel):
    id: int
    username: str
    full_name: str
    role: str
    is_active: bool
    auth_provider: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LoginRequest(BaseModel):
    username: str
    password: str


class PasswordChangeRequest(BaseModel):
    old_password: str
    new_password: str


class RegisterRequest(BaseModel):
    username: str
    password: str
    full_name: Optional[str] = ""


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ===== OperationLog =====
class OperationLogOut(BaseModel):
    id: int
    created_at: datetime
    user_id: Optional[int] = None
    username: str
    action: str
    target: str
    target_id: str
    detail: str
    ip: str
    user_agent: str

    model_config = ConfigDict(from_attributes=True)


class OperationLogPage(BaseModel):
    total: int
    items: List[OperationLogOut]


# ===== Handbook =====
class HandbookCategoryBase(BaseModel):
    name: str
    sort_order: Optional[int] = 0


class HandbookCategoryCreate(HandbookCategoryBase):
    pass


class HandbookCategoryUpdate(BaseModel):
    name: Optional[str] = None
    sort_order: Optional[int] = None


class HandbookItemBase(BaseModel):
    title: str
    kind: str = "link"   # "link" or "file"
    url: Optional[str] = ""
    description: Optional[str] = ""
    owner: Optional[str] = ""
    sort_order: Optional[int] = 0


class HandbookItemCreate(HandbookItemBase):
    category_id: int


class HandbookItemUpdate(BaseModel):
    category_id: Optional[int] = None
    title: Optional[str] = None
    kind: Optional[str] = None
    url: Optional[str] = None
    description: Optional[str] = None
    owner: Optional[str] = None
    sort_order: Optional[int] = None


class HandbookItemOut(HandbookItemBase):
    id: int
    category_id: int
    file_path: str = ""
    file_name: str = ""
    file_size: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class HandbookCategoryOut(HandbookCategoryBase):
    id: int
    items: List[HandbookItemOut] = []

    model_config = ConfigDict(from_attributes=True)


# ===== Special =====
class SpecialBase(BaseModel):
    name: str
    kind: Optional[str] = "special"  # special / assault
    owner: Optional[str] = ""
    sort_order: Optional[int] = 0
    is_active: Optional[bool] = True
    email_to: Optional[str] = ""
    email_cc: Optional[str] = ""
    email_subject_tpl: Optional[str] = ""


class SpecialCreate(SpecialBase):
    pass


class SpecialUpdate(BaseModel):
    name: Optional[str] = None
    kind: Optional[str] = None
    owner: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None
    email_to: Optional[str] = None
    email_cc: Optional[str] = None
    email_subject_tpl: Optional[str] = None


class SpecialOut(SpecialBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class SpecialContentUpdate(BaseModel):
    version: int
    goal: Optional[str] = None
    progress_summary: Optional[str] = None
    milestones_json: Optional[str] = None
    formation_json: Optional[str] = None
    extra_grids_json: Optional[str] = None


class SpecialContentOut(BaseModel):
    id: int
    special_id: int
    goal: str = ""
    progress_summary: str = ""
    panorama_image_path: str = ""
    panorama_image_name: str = ""
    milestones_json: str = "[]"
    formation_json: str = '{"headers":[],"rows":[]}'
    extra_grids_json: str = "[]"
    version: int = 0
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class SpecialItemBase(BaseModel):
    seq: Optional[int] = 0
    content: Optional[str] = ""
    progress: Optional[str] = ""
    owner: Optional[str] = ""
    planned_close_date: Optional[str] = ""
    status: Optional[str] = "open"
    sort_order: Optional[int] = 0


class SpecialItemCreate(SpecialItemBase):
    special_id: int


class SpecialItemUpdate(SpecialItemBase):
    pass


class SpecialItemOut(SpecialItemBase):
    id: int
    special_id: int

    model_config = ConfigDict(from_attributes=True)


class SpecialDetailOut(SpecialOut):
    content: Optional[SpecialContentOut] = None
    tasks: List[SpecialItemOut] = []
    risks: List[SpecialItemOut] = []


class SpecialReportDraft(BaseModel):
    """周报草稿：纯文本，前端可编辑后复制/导出 mailto。"""
    subject: str
    to: str
    cc: str
    body: str
