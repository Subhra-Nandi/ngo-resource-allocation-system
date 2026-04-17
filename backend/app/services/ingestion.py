import uuid
from sqlalchemy import update

from app.core.database import AsyncSessionLocal
from app.models.user_report import ReportStatus, UserReport
from app.agents.structuring import structure_report
from app.processors.text import normalize_text


async def process_text_report(report_id: str, raw_text: str):
    print(f"=== PROCESSING {report_id} ===")
    async with AsyncSessionLocal() as db:
        try:
            # Step 1 — normalize
            normalized = normalize_text(raw_text, source_type="text")
            clean = normalized["text"]
            print(f"Normalized: {clean[:80]}")

            # Step 2 — AI structure
            structured = structure_report(clean)
            print(f"Structured: {structured}")

            # Step 3 — save to DB
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
            print(f"Saved structured data for {report_id}")

            # Step 4 — run validation + matching
            from app.services.validation import run_validation_gates
            await run_validation_gates(report_id)

        except Exception as e:
         print(f"=== ERROR {report_id}: {e} ===")
         import traceback
         traceback.print_exc()
    # Don't flag immediately — set to pending so user isn't confused
         async with AsyncSessionLocal() as db2:
          await db2.execute(
             update(UserReport)
             .where(UserReport.id == uuid.UUID(report_id))
             .values(
                status=ReportStatus.FLAGGED,
                ai_flag_reason=f"Processing error: {str(e)[:200]}"
            )
        )
         await db2.commit()
async def process_audio_report(report_id: str, audio_bytes: bytes, filename: str):
    """Transcribe audio → normalize → structure → validate → match."""
    print(f"=== TRANSCRIBING AUDIO {report_id} ===")
    async with AsyncSessionLocal() as db:
        try:
            from app.processors.stt import transcribe_audio
            raw_text = transcribe_audio(audio_bytes, filename)
            print(f"Transcribed: {raw_text[:80]}")

            if not raw_text.strip():
                await db.execute(
                    update(UserReport)
                    .where(UserReport.id == uuid.UUID(report_id))
                    .values(
                        status=ReportStatus.FLAGGED,
                        ai_flag_reason="Could not transcribe audio"
                    )
                )
                await db.commit()
                return

            await db.execute(
                update(UserReport)
                .where(UserReport.id == uuid.UUID(report_id))
                .values(description=raw_text[:500])
            )
            await db.commit()

        except Exception as e:
            print(f"Audio transcription error: {e}")
            raw_text = ""

    if raw_text:
        await process_text_report(report_id, raw_text)


async def process_image_report(report_id: str, image_bytes: bytes):
    """OCR image → normalize → structure → validate → match."""
    print(f"=== OCR IMAGE {report_id} ===")
    async with AsyncSessionLocal() as db:
        try:
            from app.processors.ocr import extract_from_image
            raw_text = extract_from_image(image_bytes)
            print(f"OCR result: {raw_text[:80]}")

            if not raw_text.strip():
                await db.execute(
                    update(UserReport)
                    .where(UserReport.id == uuid.UUID(report_id))
                    .values(
                        status=ReportStatus.FLAGGED,
                        ai_flag_reason="Could not extract text from image"
                    )
                )
                await db.commit()
                return

            await db.execute(
                update(UserReport)
                .where(UserReport.id == uuid.UUID(report_id))
                .values(description=raw_text[:500])
            )
            await db.commit()

        except Exception as e:
            print(f"OCR error: {e}")
            raw_text = ""

    if raw_text:
        await process_text_report(report_id, raw_text)                