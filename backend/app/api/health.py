from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    """Railway uses this endpoint to verify the service is running."""
    return {"status": "ok", "service": "NGO Resource Platform"}


@router.get("/health/db")
async def db_health_check(db: AsyncSession = Depends(get_db)):
    """Verifies database + PostGIS extension are both working."""
    result = await db.execute(text("SELECT PostGIS_Version()"))
    postgis_version = result.scalar()
    return {
        "status": "ok",
        "database": "connected",
        "postgis": postgis_version,
    }
