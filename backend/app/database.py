from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import BACKEND_DIR, settings


class Base(DeclarativeBase):
    pass


database_url = settings.database_url
connect_args = {}

if database_url.startswith("sqlite:///"):
    relative_path = database_url.removeprefix("sqlite:///")
    db_path = (BACKEND_DIR / relative_path).resolve()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    database_url = f"sqlite:///{db_path.as_posix()}"
    connect_args = {"check_same_thread": False}

engine = create_engine(database_url, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def ensure_sqlite_compatibility() -> None:
    """Apply small additive migrations for existing local SQLite installations."""
    if not database_url.startswith("sqlite"):
        return
    from sqlalchemy import inspect, text

    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    with engine.begin() as connection:
        if "companion_memories" in tables:
            memory_columns = {column["name"] for column in inspector.get_columns("companion_memories")}
            if "embedding" not in memory_columns:
                connection.execute(text("ALTER TABLE companion_memories ADD COLUMN embedding JSON"))
        if "companions" in tables:
            companion_columns = {column["name"] for column in inspector.get_columns("companions")}
            if "personality_config" not in companion_columns:
                connection.execute(text("ALTER TABLE companions ADD COLUMN personality_config JSON NOT NULL DEFAULT '{}'")
