import uuid
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.structuring import structure_report
from app.agents.validation import validate_need
from app.core.database import AsyncSessionLocal
from app.models.user_report import ReportStatus, UserReport
from app.processors.text import normalize_text


async def process_text_report(report_id: str, raw_text: str):
    """
    Full pipeline for text input:
    normalize → structure → validate → update DB status
    Called as a background task from the API layer.
    """
    async with AsyncSessionLocal() as db:
        try:
            # Step 1 — Update status to validating
            await db.execute(
                update(UserReport)
                .where(UserReport.id == uuid.UUID(report_id))
                .values(status=ReportStatus.VALIDATING)
            )
            await db.commit()

            # Step 2 — Normalize text
            normalized = normalize_text(raw_text, source_type="text")
            clean = normalized["text"]

            # Step 3 — AI structuring agent
            structured = structure_report(clean)

            # Step 4 — Validation gate 1 (is this genuine?)
            validation = validate_need(clean)

            if not validation["is_valid"] and validation["confidence"] > 0.8:
                # Clearly not a valid request
                await db.execute(
                    update(UserReport)
                    .where(UserReport.id == uuid.UUID(report_id))
                    .values(
                        status=ReportStatus.FLAGGED,
                        ai_confidence=validation["confidence"],
                        ai_flag_reason=validation["reason"],
                    )
                )
                await db.commit()
                return

            # Step 5 — Update report with structured data
            await db.execute(
                update(UserReport)
                .where(UserReport.id == uuid.UUID(report_id))
                .values(
                    need_type=structured.get("need_type"),
                    severity=structured.get("severity"),
                    affected_count=structured.get("affected_count"),
                    description=structured.get("description"),
                    location_name=structured.get("location_name"),
                    ai_confidence=structured.get("confidence"),
                    status=ReportStatus.PENDING,  # ready for GPS matching in Phase 4
                )
            )
            await db.commit()
            print(f"Report {report_id} processed successfully")

        except Exception as e:
            print(f"Error processing report {report_id}: {e}")
            await db.execute(
                update(UserReport)
                .where(UserReport.id == uuid.UUID(report_id))
                .values(status=ReportStatus.FLAGGED, ai_flag_reason=str(e))
            )
            await db.commit()