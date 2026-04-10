import uuid
from sqlalchemy import select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models.ngo_resource import NgoResource, NgoUser
from app.models.user_report import ReportStatus, UserReport


def _eta_minutes(distance_deg: float) -> int:
    km = distance_deg * 111.0
    return max(5, int((km / 40) * 60))


async def find_and_match_ngo(report_id: str):
    """
    PostGIS nearest NGO query.
    Finds closest depot with matching resource and quantity > 0.
    """
    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(
                select(UserReport).where(UserReport.id == uuid.UUID(report_id))
            )
            report = result.scalar_one_or_none()

            if not report:
                print(f"Report {report_id} not found for matching")
                return

            if report.user_gps is None:
                print(f"Report {report_id} has no GPS — waitlist")
                await db.execute(
                    update(UserReport)
                    .where(UserReport.id == uuid.UUID(report_id))
                    .values(status=ReportStatus.WAITLIST)
                )
                await db.commit()
                return

            # Extract lat/lng from WKB geometry using PostGIS
            coords = await db.execute(
                text("SELECT ST_X(user_gps::geometry), ST_Y(user_gps::geometry) FROM user_reports WHERE id = :id"),
                {"id": str(report_id)}
            )
            row = coords.fetchone()
            if not row:
                print(f"Could not extract GPS for {report_id}")
                return

            lng, lat = float(row[0]), float(row[1])
            print(f"User GPS: lat={lat}, lng={lng}")

            # PostGIS nearest query
            nearby = await db.execute(
                text("""
                    SELECT
                        nr.id as resource_id,
                        nr.ngo_id,
                        nr.name as resource_name,
                        nr.quantity,
                        nu.ngo_name,
                        nu.contact_phone,
                        nr.depot_address,
                        ST_Distance(
                            nr.depot_location::geography,
                            ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography
                        ) / 1000.0 as distance_km
                    FROM ngo_resources nr
                    JOIN ngo_users nu ON nr.ngo_id = nu.id
                    WHERE nr.category = :need_type
                    AND nr.quantity > 0
                    AND ST_DWithin(
                        nr.depot_location::geography,
                        ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography,
                        200000
                    )
                    ORDER BY distance_km ASC
                    LIMIT 1
                """),
                {"lat": lat, "lng": lng, "need_type": report.need_type}
            )
            match = nearby.fetchone()

            if not match:
                print(f"No nearby NGO for {report_id} — waitlist")
                await db.execute(
                    update(UserReport)
                    .where(UserReport.id == uuid.UUID(report_id))
                    .values(status=ReportStatus.WAITLIST)
                )
                await db.commit()
                return

            distance_km = float(match.distance_km)
            eta = max(5, int((distance_km / 40) * 60))

            print(f"Matched! NGO={match.ngo_name}, dist={distance_km:.1f}km, eta={eta}min")

            await db.execute(
                update(UserReport)
                .where(UserReport.id == uuid.UUID(report_id))
                .values(
                    status=ReportStatus.MATCHED,
                    matched_ngo_id=match.ngo_id,
                    matched_resource_id=match.resource_id,
                    eta_minutes=eta,
                    distance_km=round(distance_km, 1),
                )
            )
            await db.commit()

        except Exception as e:
            print(f"Matching error {report_id}: {e}")
            import traceback
            traceback.print_exc()