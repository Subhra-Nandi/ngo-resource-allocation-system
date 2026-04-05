import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user_report import ReportStatus, UserReport
from app.schemas.report import ReportAccepted, ReportStatusResponse, ReportSubmit

router = APIRouter(prefix="/requests", tags=["requests"])

STATUS_MESSAGES = {
    "pending":    "Your request is being processed.",
    "validating": "Verifying your request and checking resources.",
    "matched":    "An NGO has been matched to your request.",
    "waitlist":   "Resources unavailable right now. You are on the waitlist.",
    "flagged":    "Your request needs manual review.",
    "dispatched": "Resources are on the way.",
    "completed":  "Request fulfilled.",
}


@router.post("/submit", status_code=202, response_model=ReportAccepted)
async def submit_request(
    data: ReportSubmit,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    gps_wkt = None
    if data.lat and data.lng:
        gps_wkt = f"SRID=4326;POINT({data.lng} {data.lat})"

    report = UserReport(
        source=data.source,
        user_gps=gps_wkt,
        location_name=data.location_name,
        need_type=data.need_type,
        description=data.description,
        severity=data.severity,
        affected_count=data.affected_count,
        status=ReportStatus.PENDING,
    )
    db.add(report)
    await db.flush()

    return ReportAccepted(
        request_id=report.id,
        status=ReportStatus.PENDING,
        message="Request received. Processing in progress.",
    )


@router.get("/{report_id}/status", response_model=ReportStatusResponse)
async def get_request_status(
    report_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(UserReport).where(UserReport.id == report_id)
    )
    report = result.scalar_one_or_none()

    if not report:
        raise HTTPException(status_code=404, detail="Request not found")

    return ReportStatusResponse(
        request_id=report.id,
        status=report.status,
        message=STATUS_MESSAGES.get(report.status, "Processing."),
        matched_ngo=None,
        created_at=report.created_at,
    )