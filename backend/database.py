from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./app.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)


@event.listens_for(engine, "connect")
def _enable_sqlite_fk(dbapi_connection, _record):
    """SQLite 默认不强制外键，必须每条连接显式开启。

    不开的话 models 里所有 ondelete=CASCADE/SET NULL 只是写进 DDL 不生效，
    级联只能靠 ORM relationship 兜底，裸 SQL 删除会留下悬空外键。
    （Alembic 用的是自建 engine，本监听器不影响其 batch 迁移。）
    """
    cur = dbapi_connection.cursor()
    cur.execute("PRAGMA foreign_keys=ON")
    cur.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
