import uuid
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_ngo
from app.core.database import get_db
from app.models.ngo_resource import NgoUser

router = APIRouter(prefix="/feedback", tags=["feedback"])


class FeedbackCreate(BaseModel):
    report_id: uuid.UUID
    original_recommendation: str
    corrected_recommendation: str
    reason: str


@router.post("")
async def submit_feedback(
    data: FeedbackCreate,
    db: AsyncSession = Depends(get_db),
    current_ngo: NgoUser = Depends(get_current_ngo),
):
    """
    Human-in-the-loop feedback loop.
    When NGO overrides a recommendation, log it.
    In production this feeds back to improve the Decision Agent.
    """
    # For now log to console — Phase 5 adds a feedback table
    print(f"FEEDBACK from {current_ngo.ngo_name}:")
    print(f"  Report: {data.report_id}")
    print(f"  Original: {data.original_recommendation}")
    print(f"  Corrected: {data.corrected_recommendation}")
    print(f"  Reason: {data.reason}")

    return {
        "message": "Feedback recorded. Thank you.",
        "report_id": str(data.report_id),
    }