from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

# Async engine — used by all API routes
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.APP_ENV == "development",  # logs SQL in dev
    pool_pre_ping=True,                       # checks connection health
    pool_size=10,
    max_overflow=20,
)

# Session factory — produces individual DB sessions
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # keeps objects usable after commit
    autoflush=False,
)


# Base class for all ORM models
class Base(DeclarativeBase):
    pass


# Dependency injected into every route that needs DB access
# Usage in routes:  async def my_route(db: AsyncSession = Depends(get_db))
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