"""Database connection, session management, and Base for PS-02 CRM."""

import logging
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from backend.services.shared.config import settings

logger = logging.getLogger("database")

# Base Declarative Model
Base = declarative_base()

def get_engine():
    db_url = settings.get_effective_db_url()
    connect_args = {}
    if db_url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}
    else:
        # PostgreSQL pool settings
        return create_engine(
            db_url,
            pool_size=10,
            max_overflow=20,
            pool_recycle=1800,
            pool_pre_ping=True,
        )
    return create_engine(db_url, connect_args=connect_args)

engine = get_engine()

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db() -> Generator[Session, None, None]:
    """FastAPI Dependency for database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initializes schema tables if they do not already exist."""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables verified/initialized successfully.")
    except Exception as e:
        logger.warning(f"Database initialization warning (tables may already exist or need migrations): {e}")
