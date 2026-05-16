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

    current_stage: Optional[str] = None
    field_version: Optional[str] = None
    attention_level: Optional[int] = None
    issue_url: Optional[str] = None
    customer_status: Optional[str] = None
    recent_focus: Optional[str] = None
    key_issues: Optional[str] = None


class CustomerStatusOut(CustomerStatusBase):
    id: int
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

    model_config = ConfigDict(from_attributes=True)


# ===== Roadmap =====
class RoadmapPhaseBase(BaseModel):
    name: str
    color: Optional[str] = "#409EFF"
    start_month: int
    end_month: int
    goal: Optional[str] = ""
    core_products: Optional[str] = ""
    scenarios: Optional[str] = ""
    sort_order: Optional[int] = 0


class RoadmapPhaseCreate(RoadmapPhaseBase):
    project_id: int


class RoadmapPhaseUpdate(BaseModel):
    name: Optional[str] = None
    color: Optional[str] = None
    start_month: Optional[int] = None
    end_month: Optional[int] = None
    goal: Optional[str] = None
    core_products: Optional[str] = None
    scenarios: Optional[str] = None
    sort_order: Optional[int] = None


class RoadmapPhaseOut(RoadmapPhaseBase):
    id: int
    project_id: int

    model_config = ConfigDict(from_attributes=True)


class RoadmapMilestoneBase(BaseModel):
    month: int
    title: Optional[str] = ""
    description: Optional[str] = ""
    sort_order: Optional[int] = 0


class RoadmapMilestoneCreate(RoadmapMilestoneBase):
    project_id: int


class RoadmapMilestoneUpdate(BaseModel):
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
