import enum
import uuid
from datetime import datetime, timezone

from geoalchemy2 import Geometry
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ReportStatus(str, enum.Enum):
    PENDING = "pending"
    VALIDATING = "validating"
    MATCHED = "matched"
    WAITLIST = "waitlist"
    FLAGGED = "flagged"
    DISPATCHED = "dispatched"
    COMPLETED = "completed"


class ReportSource(str, enum.Enum):
    FIELD_WORKER = "field_worker"
    AFFECTED_USER = "affected_user"


class UserReport(Base):
    __tablename__ = "user_reports"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    source: Mapped[str] = mapped_column(String(30), nullable=False)
    user_gps: Mapped[object] = mapped_column(
        Geometry(geometry_type="POINT", srid=4326), nullable=True
    )
    user_address: Mapped[str | None] = mapped_column(Text)
    location_name: Mapped[str | None] = mapped_column(String(300))
    need_type: Mapped[str | None] = mapped_column(String(50))
    description: Mapped[str | None] = mapped_column(Text)
    severity: Mapped[int | None] = mapped_column(Integer)
    affected_count: Mapped[int | None] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(
        String(30), default=ReportStatus.PENDING, nullable=False
    )
    ai_confidence: Mapped[float | None] = mapped_column()
    ai_flag_reason: Mapped[str | None] = mapped_column(Text)
    matched_ngo_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ngo_users.id"), nullable=True
    )
    matched_resource_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    eta_minutes: Mapped[int | None] = mapped_column(Integer)
    distance_km: Mapped[float | None] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )