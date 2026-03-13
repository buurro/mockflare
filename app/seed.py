import json
import logging

from pydantic import BaseModel
from sqlmodel import Session, select

from app.config import settings
from app.models import (
    CustomHostname,
    CustomHostnameStatus,
    DNSRecord,
    DNSRecordType,
    SSLStatus,
    Zone,
)

logger = logging.getLogger("mockflare")


class SeedDNSRecord(BaseModel):
    id: str | None = None
    name: str
    type: DNSRecordType
    content: str
    ttl: int = 1
    proxied: bool = False
    comment: str | None = None
    tags: list[str] = []


class SeedCustomHostname(BaseModel):
    id: str | None = None
    hostname: str
    custom_origin_server: str | None = None
    custom_origin_sni: str | None = None
    custom_metadata: dict | None = None
    status: CustomHostnameStatus = CustomHostnameStatus.active
    ssl_status: SSLStatus = SSLStatus.active


class SeedZone(BaseModel):
    id: str | None = None
    name: str
    account_id: str


class SeedZoneData(BaseModel):
    zone: SeedZone
    dns_records: list[SeedDNSRecord] = []
    custom_hostnames: list[SeedCustomHostname] = []


class SeedData(BaseModel):
    zones: list[SeedZoneData]


def get_seed_data() -> SeedData | None:
    """Parse SEED_DATA setting as JSON. Returns None to skip seeding."""
    if not settings.seed_data:
        return None

    data = json.loads(settings.seed_data)
    return SeedData.model_validate(data)


def seed_database(db_engine=None) -> None:
    seed_data = get_seed_data()

    if seed_data is None:
        logger.info("Skipping seed data (SEED_DATA not set)")
        return

    if db_engine is None:
        from app.database import engine

        db_engine = engine

    with Session(db_engine) as session:
        for zone_data in seed_data.zones:
            existing = session.exec(
                select(Zone).where(Zone.name == zone_data.zone.name)
            ).first()

            if existing:
                logger.info(f"Zone {zone_data.zone.name} already exists, skipping")
                continue

            zone_kwargs = {
                "name": zone_data.zone.name,
                "account_id": zone_data.zone.account_id,
                "name_servers": settings.nameservers,
            }
            if zone_data.zone.id:
                zone_kwargs["id"] = zone_data.zone.id
            zone = Zone(**zone_kwargs)
            session.add(zone)
            session.commit()
            session.refresh(zone)
            logger.info(f"Created zone: {zone.name} (id={zone.id})")

            for record in zone_data.dns_records:
                record_kwargs = record.model_dump(exclude={"id"})
                record_kwargs["zone_id"] = zone.id
                if record.id:
                    record_kwargs["id"] = record.id
                dns_record = DNSRecord(**record_kwargs)
                session.add(dns_record)
            session.commit()
            logger.info(
                f"Created {len(zone_data.dns_records)} DNS records for {zone.name}"
            )

            for hostname in zone_data.custom_hostnames:
                hostname_kwargs = {
                    "zone_id": zone.id,
                    "hostname": hostname.hostname,
                    "status": hostname.status,
                    "ssl_status": hostname.ssl_status,
                    "custom_origin_server": hostname.custom_origin_server,
                    "custom_origin_sni": hostname.custom_origin_sni,
                    "custom_metadata": hostname.custom_metadata or {},
                }
                if hostname.id:
                    hostname_kwargs["id"] = hostname.id
                custom_hostname = CustomHostname(**hostname_kwargs)
                session.add(custom_hostname)
            session.commit()
            if zone_data.custom_hostnames:
                logger.info(
                    f"Created {len(zone_data.custom_hostnames)} custom hostnames for {zone.name}"
                )
