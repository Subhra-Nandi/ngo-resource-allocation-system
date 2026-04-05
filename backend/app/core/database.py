from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

# Strip any query parameters from the URL and add SSL via connect_args instead
# This avoids asyncpg rejecting ?sslmode= or ?ssl= in the connection string
def _make_url(url: str) -> str:
    """Remove SSL query params from URL — we pass SSL via connect_args instead."""
    if "?" in url:
        url = url.split("?")[0]
    return url

engine = create_async_engine(
    _make_url(settings.DATABASE_URL),
    echo=settings.APP_ENV == "development",
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    connect_args={"ssl": "require"},  # Neon requires SSL — passed directly to asyncpg
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()