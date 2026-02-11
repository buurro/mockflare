import contextlib
from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlmodel import Session, col, func, select

from app.database import get_session
from app.models import (
    CustomHostname,
    CustomHostnameCreate,
    CustomHostnameStatus,
    CustomHostnameUpdate,
    SSLSettings,
    SSLStatus,
    utcnow,
)
from app.schemas import (
    CloudflareListResponse,
    CloudflareResponse,
    DeleteResponse,
    make_list_response,
    make_response,
)

router = APIRouter(
    prefix="/zones/{zone_id}/custom_hostnames", tags=["Custom Hostnames"]
)


def get_status_from_hostname(
    hostname: str,
) -> tuple[CustomHostnameStatus | None, SSLStatus | None]:
    """
    Parse hostname labels to determine desired status values.

    Examples:
        - "ssl-status-pending-deletion.example.com" -> ssl_status=pending_deletion
        - "status-test-active.example.com" -> status=test_active
        - "status-blocked.ssl-status-active.example.com" -> both statuses set
    """
    labels = hostname.lower().split(".")
    custom_hostname_status = None
    ssl_status = None

    for label in labels:
        if label.startswith("ssl-status-"):
            status_value = label[len("ssl-status-") :].replace("-", "_")
            with contextlib.suppress(ValueError):
                ssl_status = SSLStatus(status_value)
        elif label.startswith("status-"):
            status_value = label[len("status-") :].replace("-", "_")
            with contextlib.suppress(ValueError):
                custom_hostname_status = CustomHostnameStatus(status_value)

    return custom_hostname_status, ssl_status


class CustomHostnameResponse(BaseModel):
    id: str
    hostname: str
    status: CustomHostnameStatus
    ssl: SSLSettings
    custom_origin_server: str | None
    custom_origin_sni: str | None
    custom_metadata: dict[str, Any]
    created_at: datetime
    updated_at: datetime


def to_response(ch: CustomHostname) -> CustomHostnameResponse:
    return CustomHostnameResponse(
        id=ch.id,
        hostname=ch.hostname,
        status=ch.status,
        ssl=ch.get_ssl(),
        custom_origin_server=ch.custom_origin_server,
        custom_origin_sni=ch.custom_origin_sni,
        custom_metadata=ch.custom_metadata,
        created_at=ch.created_at,
        updated_at=ch.updated_at,
    )


@router.get("", response_model=CloudflareListResponse[CustomHostnameResponse])
def list_custom_hostnames(
    zone_id: str,
    session: Annotated[Session, Depends(get_session)],
    hostname: str | None = None,
    status: CustomHostnameStatus | None = None,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=100, ge=1, le=5000),
) -> Any:
    query = select(CustomHostname).where(CustomHostname.zone_id == zone_id)

    if hostname is not None:
        query = query.where(col(CustomHostname.hostname).contains(hostname))
    if status is not None:
        query = query.where(CustomHostname.status == status)

    count_query = select(func.count()).select_from(query.subquery())
    total_count = session.exec(count_query).one()

    query = query.offset((page - 1) * per_page).limit(per_page)
    hostnames = session.exec(query).all()

    return make_list_response(
        [to_response(h) for h in hostnames],
        page=page,
        per_page=per_page,
        total_count=total_count,
    )


@router.get(
    "/{custom_hostname_id}", response_model=CloudflareResponse[CustomHostnameResponse]
)
def get_custom_hostname(
    zone_id: str,
    custom_hostname_id: str,
    session: Annotated[Session, Depends(get_session)],
):
    ch = session.exec(
        select(CustomHostname).where(
            CustomHostname.zone_id == zone_id,
            CustomHostname.id == custom_hostname_id,
        )
    ).first()

    if not ch:
        raise HTTPException(status_code=404, detail="Custom hostname not found")

    return make_response(to_response(ch))


@router.post(
    "", response_model=CloudflareResponse[CustomHostnameResponse], status_code=201
)
def create_custom_hostname(
    zone_id: str,
    data: CustomHostnameCreate,
    session: Annotated[Session, Depends(get_session)],
):
    hostname_status, hostname_ssl_status = get_status_from_hostname(data.hostname)

    ch = CustomHostname(
        zone_id=zone_id,
        hostname=data.hostname,
        status=hostname_status or CustomHostnameStatus.active,
        ssl_status=hostname_ssl_status or SSLStatus.active,
        custom_origin_server=data.custom_origin_server,
        custom_origin_sni=data.custom_origin_sni,
        custom_metadata=data.custom_metadata or {},
    )

    if data.ssl:
        ch.ssl_method = data.ssl.method
        if data.ssl.bundle_method:
            ch.ssl_bundle_method = data.ssl.bundle_method

    session.add(ch)
    session.commit()
    session.refresh(ch)
    return make_response(to_response(ch))


@router.patch(
    "/{custom_hostname_id}", response_model=CloudflareResponse[CustomHostnameResponse]
)
def update_custom_hostname(
    zone_id: str,
    custom_hostname_id: str,
    data: CustomHostnameUpdate,
    session: Annotated[Session, Depends(get_session)],
):
    ch = session.exec(
        select(CustomHostname).where(
            CustomHostname.zone_id == zone_id,
            CustomHostname.id == custom_hostname_id,
        )
    ).first()

    if not ch:
        raise HTTPException(status_code=404, detail="Custom hostname not found")

    if data.custom_origin_server is not None:
        ch.custom_origin_server = data.custom_origin_server
    if data.custom_origin_sni is not None:
        ch.custom_origin_sni = data.custom_origin_sni
    if data.custom_metadata is not None:
        ch.custom_metadata = data.custom_metadata
    if data.ssl:
        ch.ssl_method = data.ssl.method
        if data.ssl.bundle_method:
            ch.ssl_bundle_method = data.ssl.bundle_method

    ch.updated_at = utcnow()
    session.add(ch)
    session.commit()
    session.refresh(ch)
    return make_response(to_response(ch))


@router.delete(
    "/{custom_hostname_id}", response_model=CloudflareResponse[DeleteResponse]
)
def delete_custom_hostname(
    zone_id: str,
    custom_hostname_id: str,
    session: Annotated[Session, Depends(get_session)],
):
    ch = session.exec(
        select(CustomHostname).where(
            CustomHostname.zone_id == zone_id,
            CustomHostname.id == custom_hostname_id,
        )
    ).first()

    if not ch:
        raise HTTPException(status_code=404, detail="Custom hostname not found")

    session.delete(ch)
    session.commit()
    return make_response(DeleteResponse(id=custom_hostname_id))
