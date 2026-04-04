import uuid
from datetime import date, datetime, timezone

from geoalchemy2 import Geometry
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class NgoUser(Base):
    """NGO admin accounts — one NGO can have multiple admins."""

    __tablename__ = "ngo_users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    ngo_name: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(200), nullable=False)
    contact_phone: Mapped[str | None] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # relationship to resources
    resources: Mapped[list["NgoResource"]] = relationship(
        back_populates="ngo", cascade="all, delete-orphan"
    )


class NgoResource(Base):
    """
    One row = one type of resource at one depot location.
    E.g. 'Rice 5kg packs' at 'Gosaba depot' with quantity=200.
    """

    __tablename__ = "ngo_resources"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    ngo_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ngo_users.id"), nullable=False
    )
    # Resource classification
    category: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # FOOD, MEDICAL, SHELTER, WASH, OTHER
    name: Mapped[str] = mapped_column(Text, nullable=False)  # e.g. "Rice 5kg pack"
    quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    unit: Mapped[str | None] = mapped_column(String(30))  # e.g. "packs", "kits"

    # Depot location (PostGIS Point, WGS84)
    # Stored as GEOMETRY so PostGIS can run ST_Distance queries
    depot_location: Mapped[object] = mapped_column(
        Geometry(geometry_type="POINT", srid=4326), nullable=False
    )
    depot_address: Mapped[str | None] = mapped_column(Text)
    depot_name: Mapped[str | None] = mapped_column(String(200))

    # Metadata
    expiry_date: Mapped[date | None] = mapped_column()
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    ngo: Mapped["NgoUser"] = relationship(back_populates="resources")