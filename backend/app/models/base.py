import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

Base = declarative_base()
_db_path = Path(__file__).resolve().parent.parent.parent / "ailover.db"
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{_db_path.as_posix()}")
_connect_args = {"check_same_thread": False} if "sqlite" in DATABASE_URL else {}

engine = create_engine(DATABASE_URL, connect_args=_connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    from . import user, conversation  # noqa: F401
    Base.metadata.create_all(bind=engine)
