import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from geoalchemy2.functions import ST_MakePoint
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_ngo
from app.core.database import get_db
from app.models.ngo_resource import NgoResource, NgoUser
from app.schemas.resource import ResourceCreate, ResourceResponse, ResourceUpdate

router = APIRouter(prefix="/ngo/resources", tags=["ngo-resources"])


@router.post("", status_code=201, response_model=ResourceResponse)
async def add_resource(
    data: ResourceCreate,
    db: AsyncSession = Depends(get_db),
    current_ngo: NgoUser = Depends(get_current_ngo),
):
    """
    NGO admin adds a new resource to their inventory.
    depot_lat/lng are converted to a PostGIS Point for spatial queries.
    """
    resource = NgoResource(
        ngo_id=current_ngo.id,
        category=data.category,
        name=data.name,
        quantity=data.quantity,
        unit=data.unit,
        depot_location=f"SRID=4326;POINT({data.depot_lng} {data.depot_lat})",
        depot_address=data.depot_address,
        depot_name=data.depot_name,
        expiry_date=data.expiry_date,
    )
    db.add(resource)
    await db.flush()

    # Return with lat/lng extracted for the response
    return _enrich_response(resource, data.depot_lat, data.depot_lng)


@router.get("", response_model=list[ResourceResponse])
async def list_resources(
    db: AsyncSession = Depends(get_db),
    current_ngo: NgoUser = Depends(get_current_ngo),
):
    """List all resources for the currently logged-in NGO."""
    from geoalchemy2.shape import to_shape

    result = await db.execute(
        select(NgoResource).where(NgoResource.ngo_id == current_ngo.id)
    )
    resources = result.scalars().all()

    responses = []
    for r in resources:
        try:
            point = to_shape(r.depot_location)
            lat, lng = point.y, point.x
        except Exception:
            lat, lng = None, None
        responses.append(_enrich_response(r, lat, lng))
    return responses


@router.put("/{resource_id}/quantity")
async def update_quantity(
    resource_id: uuid.UUID,
    quantity: int,
    db: AsyncSession = Depends(get_db),
    current_ngo: NgoUser = Depends(get_current_ngo),
):
    """Update stock quantity. Called manually by NGO admin or auto-depleted on dispatch."""
    result = await db.execute(
        select(NgoResource).where(
            NgoResource.id == resource_id,
            NgoResource.ngo_id == current_ngo.id,
        )
    )
    resource = result.scalar_one_or_none()
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")

    resource.quantity = quantity
    return {"updated": True, "new_quantity": quantity}


@router.delete("/{resource_id}", status_code=204)
async def delete_resource(
    resource_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_ngo: NgoUser = Depends(get_current_ngo),
):
    result = await db.execute(
        select(NgoResource).where(
            NgoResource.id == resource_id,
            NgoResource.ngo_id == current_ngo.id,
        )
    )
    resource = result.scalar_one_or_none()
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")

    await db.delete(resource)


def _enrich_response(resource: NgoResource, lat, lng) -> ResourceResponse:
    """Helper: attach extracted lat/lng to the response model."""
    data = {
        "id": resource.id,
        "ngo_id": resource.ngo_id,
        "category": resource.category,
        "name": resource.name,
        "quantity": resource.quantity,
        "unit": resource.unit,
        "depot_lat": lat,
        "depot_lng": lng,
        "depot_address": resource.depot_address,
        "depot_name": resource.depot_name,
        "expiry_date": resource.expiry_date,
        "updated_at": resource.updated_at,
    }
    return ResourceResponse(**data)