from src.data.clients.postgres import (
    Base,
    engine,
)

# Import all models so SQLAlchemy registers them


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(
            Base.metadata.create_all,
        )