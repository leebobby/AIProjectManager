"""轻量自动迁移：检查并补齐缺失的列。

启动时调用一次，对老数据库平滑升级。仅支持 SQLite 的简单加列场景；
列重命名、类型变更等复杂迁移仍需借助 Alembic 或手动处理。
"""
from datetime import datetime

from sqlalchemy import inspect, text

from database import engine

_CUR_YEAR = datetime.utcnow().year

# (表名, 列名, SQLite 列定义)
_ADDITIONS = [
    (
        "customer_status",
        "attention_level",
        "INTEGER DEFAULT 0",
    ),
    (
        "customer_status",
        "field_version",
        "VARCHAR(128) DEFAULT ''",
    ),
    (
        "customer_status",
        "model",
        "VARCHAR(128) DEFAULT ''",
    ),
    (
        "customer_status",
        "issue_url",
        "VARCHAR(512) DEFAULT ''",
    ),
    (
        "iteration_requirements",
        "remark",
        "TEXT DEFAULT ''",
    ),
    # 路线图跨年支持：给已有的阶段/里程碑补年份列，默认当前年份。
    (
        "roadmap_phases",
        "start_year",
        f"INTEGER NOT NULL DEFAULT {_CUR_YEAR}",
    ),
    (
        "roadmap_phases",
        "end_year",
        f"INTEGER NOT NULL DEFAULT {_CUR_YEAR}",
    ),
    (
        "roadmap_milestones",
        "year",
        f"INTEGER NOT NULL DEFAULT {_CUR_YEAR}",
    ),
    # 乐观锁版本号
    ("customer_status", "version", "INTEGER NOT NULL DEFAULT 0"),
    ("iteration_requirements", "version", "INTEGER NOT NULL DEFAULT 0"),
    ("roadmap_phases", "version", "INTEGER NOT NULL DEFAULT 0"),
]


def ensure_schema():
    inspector = inspect(engine)
    with engine.begin() as conn:
        for table, column, definition in _ADDITIONS:
            if not inspector.has_table(table):
                continue  # 表都没有，留给 create_all 处理
            cols = {row[1] for row in conn.execute(text(f"PRAGMA table_info({table})"))}
            if column not in cols:
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {definition}"))
