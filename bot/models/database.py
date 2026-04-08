import os
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


engine = None
async_session: async_sessionmaker[AsyncSession] | None = None


async def init_db(database_url: str):
    global engine, async_session

    db_dir = os.path.dirname(database_url.replace("sqlite+aiosqlite:///", ""))
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)

    engine = create_async_engine(database_url, echo=False)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    from bot.models.models import (  # noqa: F401
        User, Expense, Income, CashOperation, Equipment,
        Task, TaskComment, Salary, Utility, Invite, Setting,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session
