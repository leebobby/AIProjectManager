"""轻量自动迁移：检查并补齐缺失的列。

启动时调用一次，对老数据库平滑升级。仅支持 SQLite 的简单加列场景；
列重命名、类型变更等复杂迁移仍需借助 Alembic 或手动处理。
"""
from sqlalchemy import inspect, text

from database import engine

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
