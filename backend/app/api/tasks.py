import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_ngo
from app.core.database import get_db
from app.models.ngo_resource import NgoResource, NgoUser
from app.models.user_report import ReportStatus, UserReport

router = APIRouter(prefix="/ngo/tasks", tags=["ngo-tasks"])


@router.get("")
async def get_pending_tasks(
    db: AsyncSession = Depends(get_db),
    current_ngo: NgoUser = Depends(get_current_ngo),
):
    """
    Returns all requests matched to this NGO that are still pending dispatch.
    This is what the NGO dashboard shows as the task list.
    """
    result = await db.execute(
        select(UserReport, NgoResource)
        .join(NgoResource, NgoResource.id == UserReport.matched_resource_id)
        .where(
            UserReport.matched_ngo_id == current_ngo.id,
            UserReport.status.in_([
                ReportStatus.MATCHED,
                ReportStatus.DISPATCHED,
            ]),
        )
        .order_by(UserReport.severity.desc(), UserReport.created_at.asc())
    )
    rows = result.all()

    return [
        {
            "request_id": str(r.id),
            "status": r.status,
            "need_type": r.need_type,
            "description": r.description,
            "location_name": r.location_name,
            "severity": r.severity,
            "affected_count": r.affected_count,
            "eta_minutes": r.eta_minutes,
            "distance_km": r.distance_km,
            "resource_name": res.name,
            "resource_quantity": res.quantity,
            "created_at": str(r.created_at),
        }
        for r, res in rows
    ]


@router.post("/{report_id}/accept")
async def accept_task(
    report_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_ngo: NgoUser = Depends(get_current_ngo),
):
    """
    NGO accepts the task → status becomes dispatched → stock depleted.
    Uses row-level lock to prevent double-dispatch.
    """
    # Fetch report — verify it belongs to this NGO
    result = await db.execute(
        select(UserReport).where(
            UserReport.id == report_id,
            UserReport.matched_ngo_id == current_ngo.id,
            UserReport.status == ReportStatus.MATCHED,
        )
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Task not found or already accepted")

    # Lock + fetch resource row
    res_result = await db.execute(
        select(NgoResource)
        .where(NgoResource.id == report.matched_resource_id)
        .with_for_update()  # row-level lock — prevents double dispatch
    )
    resource = res_result.scalar_one_or_none()

    if not resource or resource.quantity <= 0:
        raise HTTPException(status_code=400, detail="Resource stock depleted")

    # Deduct 1 unit (or affected_count if you want)
    deduct = min(report.affected_count or 1, resource.quantity)
    resource.quantity -= deduct

    # Update report status
    await db.execute(
        update(UserReport)
        .where(UserReport.id == report_id)
        .values(status=ReportStatus.DISPATCHED)
    )
    await db.commit()

    return {
        "message": "Task accepted. Resources dispatched.",
        "report_id": str(report_id),
        "units_dispatched": deduct,
        "remaining_stock": resource.quantity,
    }


@router.post("/{report_id}/complete")
async def complete_task(
    report_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_ngo: NgoUser = Depends(get_current_ngo),
):
    """Mark a dispatched task as completed."""
    result = await db.execute(
        select(UserReport).where(
            UserReport.id == report_id,
            UserReport.matched_ngo_id == current_ngo.id,
            UserReport.status == ReportStatus.DISPATCHED,
        )
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Task not found or not dispatched")

    await db.execute(
        update(UserReport)
        .where(UserReport.id == report_id)
        .values(status=ReportStatus.COMPLETED)
    )
    await db.commit()
    return {"message": "Task marked as completed", "report_id": str(report_id)}


@router.post("/{report_id}/decline")
async def decline_task(
    report_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_ngo: NgoUser = Depends(get_current_ngo),
):
    """
    NGO declines — report goes back to waitlist.
    In production this would trigger re-matching to next nearest NGO.
    """
    result = await db.execute(
        select(UserReport).where(
            UserReport.id == report_id,
            UserReport.matched_ngo_id == current_ngo.id,
            UserReport.status == ReportStatus.MATCHED,
        )
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Task not found")

    await db.execute(
        update(UserReport)
        .where(UserReport.id == report_id)
        .values(
            status=ReportStatus.WAITLIST,
            matched_ngo_id=None,
            matched_resource_id=None,
            eta_minutes=None,
            distance_km=None,
        )
    )
    await db.commit()
    return {"message": "Task declined. Request moved to waitlist."}