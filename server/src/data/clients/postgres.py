import contextlib
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from src.config.settings import settings

# Globally shared, long-lived engine for FastAPI request handling (single long-lived event loop)
engine = create_async_engine(
    settings.DATABASE_URL,
    isolation_level="AUTOCOMMIT",
    echo=True
)

# Reference for request-scoped database session creation (FastAPI dependency injection)
request_scoped_sessionmaker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False # prevents objects from being unusable after commit
)

# Backwards compatibility alias for existing routes and test suites
async_session_local = request_scoped_sessionmaker

@contextlib.asynccontextmanager
async def get_background_scoped_db_context() -> AsyncGenerator[async_sessionmaker[AsyncSession], None]:
    """Provides a self-contained, transient DB engine and session maker for background executions.

    Strictly intended for Celery tasks or standalone background runner processes that operate
    under short-lived, transient asyncio event loops to prevent event loop contamination.
    """
    transient_engine = create_async_engine(
        settings.DATABASE_URL,
        isolation_level="AUTOCOMMIT",
        echo=True
    )
    transient_session_local = async_sessionmaker(
        bind=transient_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    try:
        yield transient_session_local
    finally:
        await transient_engine.dispose()


class Base(DeclarativeBase):
    pass

