from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings


def _to_psycopg_url(database_url: str) -> str:
    """Force the psycopg3 driver regardless of the scheme Supabase hands out."""
    if database_url.startswith("postgresql+"):
        return database_url
    return database_url.replace("postgresql://", "postgresql+psycopg://", 1)


settings = get_settings()

engine = create_engine(_to_psycopg_url(settings.database_url), pool_pre_ping=True) if settings.database_url else None

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
