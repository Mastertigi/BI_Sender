"""Engine, fábrica de sessões e dependência get_db do SQLAlchemy."""
from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings

# pool_pre_ping evita usar conexões mortas (importante em workers de longa duração).
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    future=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    """Base declarativa para todos os modelos."""


def get_db() -> Generator[Session, None, None]:
    """Dependência FastAPI: abre sessão por request e sempre fecha."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
