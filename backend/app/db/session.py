from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings

settings = get_settings()

# SQLAlchemy async engine — the only path to the database.
#
# statement_cache_size=0 is required when connecting through a transaction-mode
# connection pooler (Neon's PgBouncer endpoint): pooled connections are handed
# back after every transaction, so asyncpg's per-connection prepared statement
# cache goes stale. ssl="require" is asyncpg's native form of libpq's sslmode,
# which config.py strips from the URL.
#
# pool_recycle keeps the pool ahead of Neon's scale-to-zero: the compute
# suspends after ~5 minutes idle, leaving dead sockets behind. pool_pre_ping
# catches those, recycling avoids paying for the probe in the first place.
engine = create_async_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_recycle=300,
    pool_size=5,
    max_overflow=10,
    connect_args={"statement_cache_size": 0, "ssl": "require"},
)

async_session = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session
