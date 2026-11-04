import os
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings
from app.core.logging import logger

# Initialize SQLAlchemy Engine. On Vercel every request may run in a fresh serverless instance, so connections
# are not pooled there (the database's own pooler, e.g. Neon's "-pooler" URL, does that job).
if os.environ.get("VERCEL"):
    engine = create_engine(settings.get_database_url(), poolclass=NullPool)
else:
    engine = create_engine(
        settings.get_database_url(),
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
    )

# Session factory for DB operations
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides a transactional database session per request.
    Automatically closes the session after the request finishes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
