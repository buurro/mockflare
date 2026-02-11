from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import computed_field, field_validator
from sqlmodel import JSON, Column, Field, SQLModel


def generate_uuid() -> str:
    return uuid4().hex


def utcnow() -> datetime:
    return datetime.now(UTC)


class DNSRecordType(StrEnum):
    A = "A"
    AAAA = "AAAA"
    CNAME = "CNAME"
    MX = "MX"
    TXT = "TXT"
    NS = "NS"
    PTR = "PTR"
    SRV = "SRV"
    CAA = "CAA"
    HTTPS = "HTTPS"
    SVCB = "SVCB"


class DNSRecordBase(SQLModel):
    name: str
    type: DNSRecordType
    content: str
    ttl: int = Field(default=1, ge=1, le=86400)
    proxied: bool = False
    comment: str | None = None
    tags: list[str] = Field(default_factory=list, sa_column=Column(JSON))

    @field_validator("tags", mode="before")
    @classmethod
    def parse_tags(cls, v):
        if v is None:
            return []
        return v


class DNSRecord(DNSRecordBase, table=True):
    __tablename__ = "dns_records"

    id: str = Field(default_factory=generate_uuid, primary_key=True)
    zone_id: str = Field(index=True)
    created_on: datetime = Field(default_factory=utcnow)
    modified_on: datetime = Field(default_factory=utcnow)

    @computed_field
    @property
    def proxiable(self) -> bool:
        """Whether this record type can be proxied through Cloudflare."""
        return self.type in (DNSRecordType.A, DNSRecordType.AAAA, DNSRecordType.CNAME)


class DNSRecordCreate(DNSRecordBase):
    pass


class DNSRecordUpdate(SQLModel):
    name: str | None = None
    type: DNSRecordType | None = None
    content: str | None = None
    ttl: int | None = Field(default=None, ge=1, le=86400)
    proxied: bool | None = None
    comment: str | None = None
    tags: list[str] | None = None


class SSLMethod(StrEnum):
    http = "http"
    txt = "txt"
    email = "email"


class SSLStatus(StrEnum):
    initializing = "initializing"
    pending_validation = "pending_validation"
    deleted = "deleted"
    pending_issuance = "pending_issuance"
    pending_deployment = "pending_deployment"
    pending_deletion = "pending_deletion"
    pending_expiration = "pending_expiration"
    expired = "expired"
    active = "active"
    initializing_timed_out = "initializing_timed_out"
    validation_timed_out = "validation_timed_out"
    issuance_timed_out = "issuance_timed_out"
    deployment_timed_out = "deployment_timed_out"
    deletion_timed_out = "deletion_timed_out"
    pending_cleanup = "pending_cleanup"
    staging_deployment = "staging_deployment"
    staging_active = "staging_active"
    deactivating = "deactivating"
    inactive = "inactive"
    backup_issued = "backup_issued"
    holding_deployment = "holding_deployment"


class BundleMethod(StrEnum):
    ubiquitous = "ubiquitous"
    optimal = "optimal"
    force = "force"


class CustomHostnameStatus(StrEnum):
    active = "active"
    pending = "pending"
    active_redeploying = "active_redeploying"
    moved = "moved"
    pending_deletion = "pending_deletion"
    deleted = "deleted"
    pending_blocked = "pending_blocked"
    pending_migration = "pending_migration"
    pending_provisioned = "pending_provisioned"
    test_pending = "test_pending"
    test_active = "test_active"
    test_active_apex = "test_active_apex"
    test_blocked = "test_blocked"
    test_failed = "test_failed"
    provisioned = "provisioned"
    blocked = "blocked"


class SSLSettings(SQLModel):
    method: SSLMethod = SSLMethod.http
    type: str = "dv"
    bundle_method: BundleMethod = BundleMethod.ubiquitous
    status: SSLStatus = SSLStatus.initializing


class SSLSettingsInput(SQLModel):
    method: SSLMethod = SSLMethod.http
    bundle_method: BundleMethod | None = None


class CustomHostnameBase(SQLModel):
    hostname: str


class CustomHostname(CustomHostnameBase, table=True):
    __tablename__ = "custom_hostnames"

    id: str = Field(default_factory=generate_uuid, primary_key=True)
    zone_id: str = Field(index=True)
    status: CustomHostnameStatus = CustomHostnameStatus.pending
    ssl_method: SSLMethod = SSLMethod.http
    ssl_type: str = "dv"
    ssl_bundle_method: BundleMethod = BundleMethod.ubiquitous
    ssl_status: SSLStatus = SSLStatus.initializing
    custom_origin_server: str | None = None
    custom_origin_sni: str | None = None
    custom_metadata: dict[str, Any] = Field(
        default_factory=dict, sa_column=Column(JSON)
    )
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    @field_validator("custom_metadata", mode="before")
    @classmethod
    def parse_metadata(cls, v):
        if v is None:
            return {}
        return v

    def get_ssl(self) -> SSLSettings:
        return SSLSettings(
            method=self.ssl_method,
            type=self.ssl_type,
            bundle_method=self.ssl_bundle_method,
            status=self.ssl_status,
        )


class CustomHostnameCreate(CustomHostnameBase):
    ssl: SSLSettingsInput | None = None
    custom_origin_server: str | None = None
    custom_origin_sni: str | None = None
    custom_metadata: dict[str, Any] | None = None


class CustomHostnameUpdate(SQLModel):
    ssl: SSLSettingsInput | None = None
    custom_origin_server: str | None = None
    custom_origin_sni: str | None = None
    custom_metadata: dict[str, Any] | None = None


class ZoneType(StrEnum):
    full = "full"
    partial = "partial"
    secondary = "secondary"


class ZoneStatus(StrEnum):
    active = "active"
    pending = "pending"
    initializing = "initializing"
    moved = "moved"
    deleted = "deleted"
    deactivated = "deactivated"
    read_only = "read_only"


class Zone(SQLModel, table=True):
    __tablename__ = "zones"

    id: str = Field(default_factory=generate_uuid, primary_key=True)
    name: str = Field(index=True)
    account_id: str = Field(index=True)
    status: ZoneStatus = ZoneStatus.pending
    type: ZoneType = ZoneType.full
    paused: bool = False
    name_servers: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    created_on: datetime = Field(default_factory=utcnow)
    modified_on: datetime = Field(default_factory=utcnow)

    @field_validator("name_servers", mode="before")
    @classmethod
    def parse_name_servers(cls, v: list[str] | None) -> list[str]:
        if v is None:
            return []
        return v


class ZoneCreate(SQLModel):
    name: str
    account_id: str
    type: ZoneType = ZoneType.full


class ZoneUpdate(SQLModel):
    paused: bool | None = None
    type: ZoneType | None = None
