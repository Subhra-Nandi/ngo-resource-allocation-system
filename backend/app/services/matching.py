import uuid
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from geoalchemy2.functions import ST_Distance, ST_DWithin

from app.models.ngo_resource import NgoResource, NgoUser
from app.models.user_report import ReportStatus, UserReport


def _calculate_eta(distance_deg: float) -> int:
    """Convert PostGIS degree distance to ETA in minutes."""
    distance_km = distance_deg * 111.0
    speed_kmh = 40
    return max(5, int((distance_km / speed_kmh) * 60))


async def find_and_match_ngo(report_id: str, db: AsyncSession):
    """
    GPS nearest NGO finder using PostGIS ST_Distance.
    Finds closest NGO depot with matching resource and stock > 0.
    Updates report with match details.
    """
    try:
        # Fetch report with GPS
        result = await db.execute(
            select(UserReport).where(UserReport.id == uuid.UUID(report_id))
        )
        report = result.scalar_one_or_none()

        if not report or report.user_gps is None:
            print(f"Report {report_id} has no GPS — cannot match")
            await db.execute(
                update(UserReport)
                .where(UserReport.id == uuid.UUID(report_id))
                .values(status=ReportStatus.WAITLIST)
            )
            await db.commit()
            return

        # PostGIS nearest NGO query
        # ST_Distance returns degrees — multiply by 111 for km
        from sqlalchemy import text
        gps_text = f"ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)"

        nearby = await db.execute(
            select(
                NgoResource,
                NgoUser,
                ST_Distance(
                    NgoResource.depot_location,
                    text(gps_text),
                ).label("distance_deg"),
            )
            .join(NgoUser, NgoResource.ngo_id == NgoUser.id)
            .where(
                NgoResource.category == report.need_type,
                NgoResource.quantity > 0,
                ST_DWithin(
                    NgoResource.depot_location,
                    text(gps_text),
                    1.0,  # ~111 km radius
                ),
            )
            .order_by("distance_deg")
            .limit(1)
            .params(
                lat=report.user_gps.latitude if hasattr(report.user_gps, 'latitude') else 0,
                lng=report.user_gps.longitude if hasattr(report.user_gps, 'longitude') else 0,
            )
        )

        match = nearby.first()

        if not match:
            await db.execute(
                update(UserReport)
                .where(UserReport.id == uuid.UUID(report_id))
                .values(status=ReportStatus.WAITLIST)
            )
            await db.commit()
            print(f"No nearby NGO found for report {report_id}")
            return

        resource, ngo, distance_deg = match
        eta = _calculate_eta(float(distance_deg))

        # Update report with match
        await db.execute(
            update(UserReport)
            .where(UserReport.id == uuid.UUID(report_id))
            .values(
                status=ReportStatus.MATCHED,
                matched_ngo_id=ngo.id,
                matched_resource_id=resource.id,
                eta_minutes=eta,
                distance_km=round(float(distance_deg) * 111, 1),
            )
        )
        await db.commit()
        print(f"Report {report_id} matched to NGO {ngo.ngo_name} — ETA {eta} min")

    except Exception as e:
        print(f"Matching error for {report_id}: {e}")
        import traceback
        traceback.print_exc()