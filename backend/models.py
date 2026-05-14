from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text

from database import Base


class CustomerStatus(Base):
    __tablename__ = "customer_status"

    id = Column(Integer, primary_key=True, index=True)
    machine_id = Column(String(64), nullable=False, comment="机台编号")
    battlefield = Column(String(128), nullable=False, comment="战场")
    current_stage = Column(String(128), nullable=False, comment="当前阶段")
    field_version = Column(String(128), default="", comment="现场版本")
    attention_level = Column(Integer, default=0, comment="近期关注度: 0 未评估 / 1-5 星")
    customer_status = Column(String(256), nullable=False, comment="客户面进展")
    recent_focus = Column(Text, default="", comment="近期重点事务")
    key_issues = Column(Text, default="", comment="关键问题")
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
    __tablename__ = "iterations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(128), nullable=False, comment="迭代名称")
    goal = Column(Text, default="", comment="迭代目标")
    start_date = Column(DateTime, nullable=True, comment="开始时间")
    end_date = Column(DateTime, nullable=True, comment="结束时间")
    status = Column(String(32), default="planning", comment="状态: planning/in_progress/done")
    owner = Column(String(64), default="", comment="负责人")


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
