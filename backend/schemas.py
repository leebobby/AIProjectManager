from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


# ===== CustomerStatus =====
class CustomerStatusBase(BaseModel):
    machine_id: str
    battlefield: str
    current_stage: str
    attention_level: Optional[int] = 0
    customer_status: str
    recent_focus: Optional[str] = ""
    key_issues: Optional[str] = ""


class CustomerStatusCreate(CustomerStatusBase):
    pass


class CustomerStatusUpdate(BaseModel):
    """编辑时 machine_id / battlefield 不能修改，所以单独定义一个 schema。"""
    current_stage: Optional[str] = None
    attention_level: Optional[int] = None
    customer_status: Optional[str] = None
    recent_focus: Optional[str] = None
    key_issues: Optional[str] = None


class CustomerStatusOut(CustomerStatusBase):
    id: int
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


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


# ===== Iteration =====
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


class RegisterRequest(BaseModel):
    username: str
    password: str
    full_name: Optional[str] = ""


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
