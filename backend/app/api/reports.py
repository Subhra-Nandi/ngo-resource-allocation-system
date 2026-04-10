import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user_report import ReportStatus, UserReport
from app.schemas.report import ReportAccepted, ReportStatusResponse, ReportSubmit, MatchedNgo
from app.services.ingestion import process_text_report

router = APIRouter(prefix="/requests", tags=["requests"])

STATUS_MESSAGES = {
    "pending":    "Your request is being processed.",
    "validating": "Verifying your request with AI.",
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
    report_id = str(report.id)
    await db.commit()

    if data.description:
        background_tasks.add_task(process_text_report, report_id, data.description)

    return ReportAccepted(
        request_id=report.id,
        status=ReportStatus.PENDING,
        message="Request received. AI processing started.",
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

    matched_ngo = None

    # If matched, fetch NGO details
    if report.status == ReportStatus.MATCHED and report.matched_ngo_id:
        from app.models.ngo_resource import NgoResource, NgoUser
        ngo_result = await db.execute(
            select(NgoUser, NgoResource)
            .join(NgoResource, NgoResource.ngo_id == NgoUser.id)
            .where(
                NgoUser.id == report.matched_ngo_id,
                NgoResource.id == report.matched_resource_id,
            )
        )
        row = ngo_result.first()
        if row:
            ngo, resource = row
            matched_ngo = MatchedNgo(
                ngo_name=ngo.ngo_name,
                depot_address=resource.depot_address,
                contact_phone=ngo.contact_phone,
                resource_name=resource.name,
                quantity_available=resource.quantity,
                eta_minutes=report.eta_minutes or 0,
                distance_km=report.distance_km or 0.0,
            )

    return ReportStatusResponse(
        request_id=report.id,
        status=report.status,
        message=STATUS_MESSAGES.get(report.status, "Processing."),
        matched_ngo=matched_ngo,
        created_at=report.created_at,
    )


@router.get("/debug/latest")
async def debug_latest(db: AsyncSession = Depends(get_db)):
    from sqlalchemy import desc
    result = await db.execute(
        select(UserReport).order_by(desc(UserReport.created_at)).limit(5)
    )
    reports = result.scalars().all()
    return [
        {
            "id": str(r.id),
            "status": r.status,
            "need_type": r.need_type,
            "severity": r.severity,
            "description": r.description,
            "ai_confidence": r.ai_confidence,
            "ai_flag_reason": r.ai_flag_reason,
            "matched_ngo_id": str(r.matched_ngo_id) if r.matched_ngo_id else None,
            "eta_minutes": r.eta_minutes,
            "distance_km": r.distance_km,
        }
        for r in reports
    ]