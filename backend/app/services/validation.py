import uuid
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.validation import validate_need
from app.core.database import AsyncSessionLocal
from app.models.ngo_resource import NgoResource
from app.models.user_report import ReportStatus, UserReport


async def run_validation_gates(report_id: str):
    """
    Gate 1 — AI checks if request is genuine
    Gate 2 — DB checks if matching stock exists
    """
    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(
                select(UserReport).where(UserReport.id == uuid.UUID(report_id))
            )
            report = result.scalar_one_or_none()
            if not report:
                print(f"Report {report_id} not found")
                return

            # ── Gate 1: AI validation ────────────────────────────
            print(f"Gate 1: checking if request is genuine...")
            validation = validate_need(report.description or "")
            print(f"Gate 1 result: {validation}")

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
                print(f"Report {report_id} FLAGGED: {validation['reason']}")
                return

            # ── Gate 2: Stock check ──────────────────────────────
            print(f"Gate 2: checking stock for {report.need_type}...")
            if report.need_type:
                stock = await db.execute(
                    select(NgoResource).where(
                        NgoResource.category == report.need_type,
                        NgoResource.quantity > 0,
                    ).limit(1)
                )
                has_stock = stock.scalar_one_or_none() is not None
            else:
                has_stock = False

            print(f"Gate 2 result: has_stock={has_stock}")

            if not has_stock:
                await db.execute(
                    update(UserReport)
                    .where(UserReport.id == uuid.UUID(report_id))
                    .values(status=ReportStatus.WAITLIST)
                )
                await db.commit()
                print(f"Report {report_id} → WAITLIST (no stock)")
                return

            # Both gates passed → trigger GPS matching
            print(f"Both gates passed → starting GPS match...")
            from app.services.matching import find_and_match_ngo
            await find_and_match_ngo(report_id)

        except Exception as e:
            print(f"Validation error {report_id}: {e}")
            import traceback
            traceback.print_exc()
            await db.execute(
                update(UserReport)
                .where(UserReport.id == uuid.UUID(report_id))
                .values(status=ReportStatus.FLAGGED, ai_flag_reason=str(e))
            )
            await db.commit()