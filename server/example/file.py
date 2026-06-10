from sqlalchemy import Column, Integer, MetaData, String, Table, create_engine

from src.config.settings import settings

engine = create_engine(url=settings.DATABASE_URL)

meta = MetaData()

my_table = Table(
    "my_table",
    meta,
    Column("id", Integer, primary_key=True),
    Column("name", String(45))
)

meta.create_all(engine)