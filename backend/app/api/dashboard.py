from fastapi import APIRouter, Depends
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_ngo
from app.core.database import get_db
from app.models.ngo_resource import NgoResource, NgoUser
from app.models.user_report import ReportStatus, UserReport

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary")
async def get_dashboard_summary(
    db: AsyncSession = Depends(get_db),
    current_ngo: NgoUser = Depends(get_current_ngo),
):
    """
    High-level numbers for the NGO dashboard header cards.
    """
    # Total pending tasks for this NGO
    pending = await db.execute(
        select(func.count()).select_from(UserReport).where(
            UserReport.matched_ngo_id == current_ngo.id,
            UserReport.status == ReportStatus.MATCHED,
        )
    )

    # Total dispatched today
    dispatched = await db.execute(
        select(func.count()).select_from(UserReport).where(
            UserReport.matched_ngo_id == current_ngo.id,
            UserReport.status == ReportStatus.DISPATCHED,
        )
    )

    # Total completed
    completed = await db.execute(
        select(func.count()).select_from(UserReport).where(
            UserReport.matched_ngo_id == current_ngo.id,
            UserReport.status == ReportStatus.COMPLETED,
        )
    )

    # Total stock across all resources
    stock = await db.execute(
        select(func.sum(NgoResource.quantity)).where(
            NgoResource.ngo_id == current_ngo.id
        )
    )

    return {
        "ngo_name": current_ngo.ngo_name,
        "pending_tasks": pending.scalar() or 0,
        "dispatched_tasks": dispatched.scalar() or 0,
        "completed_tasks": completed.scalar() or 0,
        "total_stock_units": stock.scalar() or 0,
    }


@router.get("/map-data")
async def get_map_data(
    db: AsyncSession = Depends(get_db),
    current_ngo: NgoUser = Depends(get_current_ngo),
):
    """
    All active requests with GPS coords for the Leaflet map.
    Returns severity-colored pins.
    """
    result = await db.execute(
        text("""
            SELECT
                ur.id,
                ur.need_type,
                ur.severity,
                ur.status,
                ur.affected_count,
                ur.location_name,
                ur.description,
                ur.eta_minutes,
                ST_X(ur.user_gps::geometry) as lng,
                ST_Y(ur.user_gps::geometry) as lat
            FROM user_reports ur
            WHERE ur.matched_ngo_id = :ngo_id
            AND ur.status IN ('matched', 'dispatched')
            AND ur.user_gps IS NOT NULL
            ORDER BY ur.severity DESC
        """),
        {"ngo_id": str(current_ngo.id)}
    )
    rows = result.fetchall()

    return [
        {
            "id": str(r.id),
            "lat": float(r.lat),
            "lng": float(r.lng),
            "need_type": r.need_type,
            "severity": r.severity,
            "status": r.status,
            "affected_count": r.affected_count,
            "location_name": r.location_name,
            "description": r.description,
            "eta_minutes": r.eta_minutes,
            # Color for frontend map pins
            "color": "#E24B4A" if r.severity >= 4 else "#EF9F27" if r.severity >= 3 else "#639922",
        }
        for r in rows
    ]


@router.get("/inventory")
async def get_inventory(
    db: AsyncSession = Depends(get_db),
    current_ngo: NgoUser = Depends(get_current_ngo),
):
    """
    Current stock levels for this NGO with low-stock warnings.
    """
    result = await db.execute(
        select(NgoResource).where(NgoResource.ngo_id == current_ngo.id)
    )
    resources = result.scalars().all()

    return [
        {
            "id": str(r.id),
            "category": r.category,
            "name": r.name,
            "quantity": r.quantity,
            "unit": r.unit,
            "depot_name": r.depot_name,
            "depot_address": r.depot_address,
            "expiry_date": str(r.expiry_date) if r.expiry_date else None,
            "low_stock": r.quantity < 20,  # warning flag for frontend
            "updated_at": str(r.updated_at),
        }
        for r in resources
    ]


@router.get("/requests/all")
async def get_all_requests(
    db: AsyncSession = Depends(get_db),
    current_ngo: NgoUser = Depends(get_current_ngo),
):
    """All requests in the system — for admin overview."""
    result = await db.execute(
        select(UserReport)
        .where(UserReport.status.in_([
            ReportStatus.PENDING,
            ReportStatus.WAITLIST,
            ReportStatus.MATCHED,
            ReportStatus.DISPATCHED,
        ]))
        .order_by(UserReport.severity.desc(), UserReport.created_at.asc())
        .limit(50)
    )
    reports = result.scalars().all()

    return [
        {
            "id": str(r.id),
            "status": r.status,
            "need_type": r.need_type,
            "severity": r.severity,
            "affected_count": r.affected_count,
            "location_name": r.location_name,
            "description": r.description,
            "eta_minutes": r.eta_minutes,
            "distance_km": r.distance_km,
            "created_at": str(r.created_at),
        }
        for r in reports
    ]