from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, col, func, select

from app.database import get_session
from app.models import Zone, ZoneCreate, ZoneStatus, ZoneUpdate, utcnow
from app.schemas import (
    CloudflareListResponse,
    CloudflareResponse,
    DeleteResponse,
    make_list_response,
    make_response,
)

router = APIRouter(prefix="/zones", tags=["Zones"])


@router.get("", response_model=CloudflareListResponse[Zone])
def list_zones(
    session: Annotated[Session, Depends(get_session)],
    name: str | None = None,
    account_id: str | None = None,
    status: ZoneStatus | None = None,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=100, ge=1, le=5000),
) -> Any:
    query = select(Zone)

    if name is not None:
        query = query.where(col(Zone.name).contains(name))
    if account_id is not None:
        query = query.where(Zone.account_id == account_id)
    if status is not None:
        query = query.where(Zone.status == status)

    count_query = select(func.count()).select_from(query.subquery())
    total_count = session.exec(count_query).one()

    query = query.offset((page - 1) * per_page).limit(per_page)
    zones = session.exec(query).all()

    return make_list_response(
        list(zones), page=page, per_page=per_page, total_count=total_count
    )


@router.get("/{zone_id}", response_model=CloudflareResponse[Zone])
def get_zone(
    zone_id: str,
    session: Annotated[Session, Depends(get_session)],
) -> Any:
    zone = session.get(Zone, zone_id)

    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")

    return make_response(zone)


@router.post("", response_model=CloudflareResponse[Zone], status_code=201)
def create_zone(
    data: ZoneCreate,
    session: Annotated[Session, Depends(get_session)],
) -> Any:
    zone = Zone(
        name=data.name,
        account_id=data.account_id,
        type=data.type,
        name_servers=["ns1.mockflare.com", "ns2.mockflare.com"],
    )
    session.add(zone)
    session.commit()
    session.refresh(zone)
    return make_response(zone)


@router.patch("/{zone_id}", response_model=CloudflareResponse[Zone])
def update_zone(
    zone_id: str,
    data: ZoneUpdate,
    session: Annotated[Session, Depends(get_session)],
) -> Any:
    zone = session.get(Zone, zone_id)

    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")

    if data.paused is not None:
        zone.paused = data.paused
    if data.type is not None:
        zone.type = data.type

    zone.modified_on = utcnow()
    session.add(zone)
    session.commit()
    session.refresh(zone)
    return make_response(zone)


@router.delete("/{zone_id}", response_model=CloudflareResponse[DeleteResponse])
def delete_zone(
    zone_id: str,
    session: Annotated[Session, Depends(get_session)],
) -> Any:
    zone = session.get(Zone, zone_id)

    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")

    session.delete(zone)
    session.commit()
    return make_response(DeleteResponse(id=zone_id))
