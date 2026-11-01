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
