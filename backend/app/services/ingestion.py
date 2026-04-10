import uuid
from sqlalchemy import update
from app.core.database import AsyncSessionLocal
from app.models.user_report import ReportStatus, UserReport
from app.agents.structuring import structure_report
from app.processors.text import normalize_text


async def process_text_report(report_id: str, raw_text: str):
    """
    Full pipeline:
    normalize → AI structure → save → trigger validation gates
    """
    print(f"=== PROCESSING REPORT {report_id} ===")
    async with AsyncSessionLocal() as db:
        try:
            # Step 1 — normalize
            normalized = normalize_text(raw_text, source_type="text")
            clean = normalized["text"]
            print(f"Normalized text: {clean[:80]}")

            # Step 2 — AI structure
            structured = structure_report(clean)
            print(f"Structured: {structured}")

            # Step 3 — save structured data
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
                    status=ReportStatus.PENDING,
                )
            )
            await db.commit()

            # Step 4 — run validation gates (Phase 3)
            from app.services.validation import run_validation_gates
            await run_validation_gates(report_id)

        except Exception as e:
            print(f"=== ERROR processing {report_id}: {e} ===")
            import traceback
            traceback.print_exc()
            async with AsyncSessionLocal() as db2:
                await db2.execute(
                    update(UserReport)
                    .where(UserReport.id == uuid.UUID(report_id))
                    .values(
                        status=ReportStatus.FLAGGED,
                        ai_flag_reason=str(e),
                    )
                )
                await db2.commit()