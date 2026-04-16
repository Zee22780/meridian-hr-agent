from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from supabase import Client, create_client

from app.config import get_settings

settings = get_settings()

# SQLAlchemy async engine (used by ORM / all DB queries)
engine = create_async_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)

async_session = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session


# Supabase client (used for direct Supabase API calls: storage, auth, realtime)
def get_supabase_client() -> Client:
    return create_client(settings.supabase_url, settings.supabase_service_role_key)


supabase: Client = get_supabase_client()
