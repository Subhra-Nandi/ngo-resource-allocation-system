import uuid
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.validation import validate_need
from app.core.database import AsyncSessionLocal
from app.models.ngo_resource import NgoResource
from app.models.user_report import ReportStatus, UserReport


async def run_validation_gates(report_id: str):
    """
    Two sequential validation gates:
    Gate 1 — Is the request genuine? (AI check)
    Gate 2 — Is the resource available? (DB check)
    Updates report status at each step.
    """
    async with AsyncSessionLocal() as db:
        try:
            # Fetch the report
            result = await db.execute(
                select(UserReport).where(UserReport.id == uuid.UUID(report_id))
            )
            report = result.scalar_one_or_none()

            if not report:
                print(f"Report {report_id} not found")
                return

            # ── Gate 1: AI need validation ──────────────────────────
            print(f"Gate 1: validating need for report {report_id}")
            validation = validate_need(report.description or "")

            if not validation["is_valid"] and validation["confidence"] > 0.8:
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
                print(f"Report {report_id} flagged: {validation['reason']}")
                return

            # ── Gate 2: Resource availability check ─────────────────
            print(f"Gate 2: checking resource availability for {report.need_type}")
            if report.need_type:
                res_result = await db.execute(
                    select(NgoResource).where(
                        NgoResource.category == report.need_type,
                        NgoResource.quantity > 0,
                    ).limit(1)
                )
                has_stock = res_result.scalar_one_or_none() is not None
            else:
                has_stock = False

            if not has_stock:
                await db.execute(
                    update(UserReport)
                    .where(UserReport.id == uuid.UUID(report_id))
                    .values(status=ReportStatus.WAITLIST)
                )
                await db.commit()
                print(f"Report {report_id} on waitlist — no stock for {report.need_type}")
                return

            # Both gates passed — ready for GPS matching
            await db.execute(
                update(UserReport)
                .where(UserReport.id == uuid.UUID(report_id))
                .values(status=ReportStatus.VALIDATING)
            )
            await db.commit()
            print(f"Report {report_id} passed both gates — ready for matching")

            # Trigger GPS matching (Phase 4)
            from app.services.matching import find_and_match_ngo
            await find_and_match_ngo(report_id, db)

        except Exception as e:
            print(f"Validation error for {report_id}: {e}")
            await db.execute(
                update(UserReport)
                .where(UserReport.id == uuid.UUID(report_id))
                .values(
                    status=ReportStatus.FLAGGED,
                    ai_flag_reason=str(e),
                )
            )
            await db.commit()