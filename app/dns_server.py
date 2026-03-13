import logging
import socket

from dnslib import AAAA, CNAME, MX, NS, QTYPE, RR, TXT, A
from dnslib import DNSRecord as DNSPacket
from dnslib.server import BaseResolver, DNSHandler, DNSRecord, DNSServer
from sqlmodel import Session, select

from app.config import settings
from app.models import DNSRecord as DNSRecordModel

logger = logging.getLogger("mockflare")

# Map record type strings to dnslib classes
RECORD_TYPES = {
    "A": (QTYPE.A, A),
    "AAAA": (QTYPE.AAAA, AAAA),
    "CNAME": (QTYPE.CNAME, CNAME),
    "TXT": (QTYPE.TXT, TXT),
    "NS": (QTYPE.NS, NS),
    "MX": (QTYPE.MX, lambda content: MX(content)),
}

# Engine used by the DNS server (can be overridden for testing)
_engine = None


def get_dns_engine():
    """Get the engine for DNS queries. Falls back to default engine."""
    global _engine
    if _engine is None:
        from app.database import engine

        _engine = engine
    return _engine


def set_dns_engine(engine):
    """Set a custom engine (for testing)."""
    global _engine
    _engine = engine


def forward_to_upstream(
    request: DNSRecord, upstream: str, port: int = 53
) -> DNSRecord | None:
    """Forward DNS request to upstream server."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(5)
        sock.sendto(request.pack(), (upstream, port))
        data, _ = sock.recvfrom(4096)
        return DNSPacket.parse(data)
    except (OSError, TimeoutError) as e:
        logger.warning(f"Upstream DNS query failed: {e}")
        return None
    finally:
        sock.close()


class MockflareDNSResolver(BaseResolver):
    """DNS resolver that reads from mockflare's database."""

    def resolve(self, request: DNSRecord, handler: DNSHandler | None) -> DNSRecord:
        reply = request.reply()
        qname = str(request.q.qname).rstrip(".")
        qtype = request.q.qtype  # Numeric QTYPE value

        with Session(get_dns_engine()) as session:
            records = session.exec(
                select(DNSRecordModel).where(DNSRecordModel.name == qname)
            ).all()

            for record in records:
                record_type = str(record.type)
                if record_type not in RECORD_TYPES:
                    continue

                rtype, rdata_cls = RECORD_TYPES[record_type]

                if qtype in (rtype, QTYPE.ANY):
                    reply.add_answer(
                        RR(
                            qname,
                            rtype,
                            rdata=rdata_cls(record.content),
                            ttl=record.ttl,
                        )
                    )

        # Forward to upstream if no local records and upstreams are configured
        if not reply.rr and settings.dns_upstreams:
            for upstream in settings.dns_upstreams:
                upstream_reply = forward_to_upstream(request, upstream)
                if upstream_reply:
                    return upstream_reply

        return reply


def start_dns_server() -> DNSServer:
    """Start the DNS server in a background thread."""
    resolver = MockflareDNSResolver()
    server = DNSServer(
        resolver,
        port=settings.dns_port,
        address=settings.dns_address,
    )
    server.start_thread()
    logger.info(f"DNS server listening on {settings.dns_address}:{settings.dns_port}")
    if settings.dns_upstreams:
        logger.info(f"DNS upstreams: {', '.join(settings.dns_upstreams)}")
    return server
