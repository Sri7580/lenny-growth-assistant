from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from app.config import settings

# NullPool avoids reusing asyncpg connections across different event loop
# contexts. asyncpg connections are bound to the loop that created them;
# SQLAlchemy's default pooling can hand a cached connection to a coroutine
# running under a different loop (e.g. across pytest-asyncio test functions,
# or ASGI transport test clients), producing
# "cannot perform operation: another operation is in progress" errors.
# NullPool opens a fresh connection per checkout, trading a little
# performance for correctness — an acceptable cost at this app's scale.
engine = create_async_engine(settings.database_url, echo=False, future=True, poolclass=NullPool)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


async def init_db():
    """Create tables and pgvector extension if they don't exist. Dev-only convenience;
    a production setup would use Alembic migrations instead."""
    async with engine.begin() as conn:
        from sqlalchemy import text
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)