from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from src.config.settings import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    isolation_level="AUTOCOMMIT",
    echo=True
)

async_session_local = async_sessionmaker(
    bind=engine, 
    class_=AsyncSession, 
    expire_on_commit=False # prevents objects from being unusable after commit
)

Base = declarative_base()