from contextlib import contextmanager
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from .engine import engine

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)

@contextmanager
def get_session() -> Generator[Session,None,None]:
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()