from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, col, func, select

from app.database import get_session
from app.models import (
    DNSRecord,
    DNSRecordCreate,
    DNSRecordType,
    DNSRecordUpdate,
    utcnow,
)
from app.schemas import (
    CloudflareListResponse,
    CloudflareResponse,
    DeleteResponse,
    make_list_response,
    make_response,
)

router = APIRouter(prefix="/zones/{zone_id}/dns_records", tags=["DNS Records"])


@router.get("", response_model=CloudflareListResponse[DNSRecord])
def list_dns_records(
    zone_id: str,
    session: Annotated[Session, Depends(get_session)],
    name: str | None = None,
    type: DNSRecordType | None = None,
    content: str | None = None,
    proxied: bool | None = None,
    comment: str | None = None,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=100, ge=1, le=5000),
):
    query = select(DNSRecord).where(DNSRecord.zone_id == zone_id)

    if name is not None:
        query = query.where(DNSRecord.name == name)
    if type is not None:
        query = query.where(DNSRecord.type == type)
    if content is not None:
        query = query.where(col(DNSRecord.content).contains(content))
    if proxied is not None:
        query = query.where(DNSRecord.proxied == proxied)
    if comment is not None:
        query = query.where(col(DNSRecord.comment).contains(comment))

    count_query = select(func.count()).select_from(query.subquery())
    total_count = session.exec(count_query).one()

    query = query.offset((page - 1) * per_page).limit(per_page)
    records = session.exec(query).all()

    return make_list_response(
        list(records), page=page, per_page=per_page, total_count=total_count
    )


@router.get("/{dns_record_id}", response_model=CloudflareResponse[DNSRecord])
def get_dns_record(
    zone_id: str,
    dns_record_id: str,
    session: Annotated[Session, Depends(get_session)],
):
    record = session.exec(
        select(DNSRecord).where(
            DNSRecord.zone_id == zone_id,
            DNSRecord.id == dns_record_id,
        )
    ).first()

    if not record:
        raise HTTPException(status_code=404, detail="DNS record not found")

    return make_response(record)


@router.post("", response_model=CloudflareResponse[DNSRecord], status_code=201)
def create_dns_record(
    zone_id: str,
    record_data: DNSRecordCreate,
    session: Annotated[Session, Depends(get_session)],
):
    record = DNSRecord(
        zone_id=zone_id,
        **record_data.model_dump(),
    )
    session.add(record)
    session.commit()
    session.refresh(record)
    return make_response(record)


@router.put("/{dns_record_id}", response_model=CloudflareResponse[DNSRecord])
def overwrite_dns_record(
    zone_id: str,
    dns_record_id: str,
    record_data: DNSRecordCreate,
    session: Annotated[Session, Depends(get_session)],
):
    record = session.exec(
        select(DNSRecord).where(
            DNSRecord.zone_id == zone_id,
            DNSRecord.id == dns_record_id,
        )
    ).first()

    if not record:
        raise HTTPException(status_code=404, detail="DNS record not found")

    for key, value in record_data.model_dump().items():
        setattr(record, key, value)

    record.modified_on = utcnow()
    session.add(record)
    session.commit()
    session.refresh(record)
    return make_response(record)


@router.patch("/{dns_record_id}", response_model=CloudflareResponse[DNSRecord])
def update_dns_record(
    zone_id: str,
    dns_record_id: str,
    record_data: DNSRecordUpdate,
    session: Annotated[Session, Depends(get_session)],
):
    record = session.exec(
        select(DNSRecord).where(
            DNSRecord.zone_id == zone_id,
            DNSRecord.id == dns_record_id,
        )
    ).first()

    if not record:
        raise HTTPException(status_code=404, detail="DNS record not found")

    update_data = record_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(record, key, value)

    record.modified_on = utcnow()
    session.add(record)
    session.commit()
    session.refresh(record)
    return make_response(record)


@router.delete("/{dns_record_id}", response_model=CloudflareResponse[DeleteResponse])
def delete_dns_record(
    zone_id: str,
    dns_record_id: str,
    session: Annotated[Session, Depends(get_session)],
):
    record = session.exec(
        select(DNSRecord).where(
            DNSRecord.zone_id == zone_id,
            DNSRecord.id == dns_record_id,
        )
    ).first()

    if not record:
        raise HTTPException(status_code=404, detail="DNS record not found")

    session.delete(record)
    session.commit()
    return make_response(DeleteResponse(id=dns_record_id))
