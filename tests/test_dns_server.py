from dnslib import DNSRecord
from sqlmodel import Session

from app.dns_server import MockflareDNSResolver, forward_to_upstream
from app.models import DNSRecord as DNSRecordModel


class TestMockflareDNSResolver:
    def test_resolve_a_record(self, session: Session):
        # Create a DNS record
        record = DNSRecordModel(
            zone_id="test-zone",
            name="example.com",
            type="A",
            content="192.0.2.1",
            ttl=300,
        )
        session.add(record)
        session.commit()

        resolver = MockflareDNSResolver()
        request = DNSRecord.question("example.com", "A")
        reply = resolver.resolve(request, None)

        assert len(reply.rr) == 1
        assert str(reply.rr[0].rdata) == "192.0.2.1"
        assert reply.rr[0].ttl == 300

    def test_resolve_txt_record(self, session: Session):
        record = DNSRecordModel(
            zone_id="test-zone",
            name="example.com",
            type="TXT",
            content="v=spf1 include:example.com ~all",
            ttl=3600,
        )
        session.add(record)
        session.commit()

        resolver = MockflareDNSResolver()
        request = DNSRecord.question("example.com", "TXT")
        reply = resolver.resolve(request, None)

        assert len(reply.rr) == 1
        assert "v=spf1" in str(reply.rr[0].rdata)

    def test_resolve_cname_record(self, session: Session):
        record = DNSRecordModel(
            zone_id="test-zone",
            name="www.example.com",
            type="CNAME",
            content="example.com",
            ttl=300,
        )
        session.add(record)
        session.commit()

        resolver = MockflareDNSResolver()
        request = DNSRecord.question("www.example.com", "CNAME")
        reply = resolver.resolve(request, None)

        assert len(reply.rr) == 1
        assert "example.com" in str(reply.rr[0].rdata)

    def test_resolve_nonexistent_record(self, session: Session):
        resolver = MockflareDNSResolver()
        request = DNSRecord.question("nonexistent.com", "A")
        reply = resolver.resolve(request, None)

        assert len(reply.rr) == 0

    def test_resolve_multiple_records(self, session: Session):
        # Create multiple A records for the same domain
        for ip in ["192.0.2.1", "192.0.2.2", "192.0.2.3"]:
            record = DNSRecordModel(
                zone_id="test-zone",
                name="multi.example.com",
                type="A",
                content=ip,
                ttl=300,
            )
            session.add(record)
        session.commit()

        resolver = MockflareDNSResolver()
        request = DNSRecord.question("multi.example.com", "A")
        reply = resolver.resolve(request, None)

        assert len(reply.rr) == 3

    def test_resolve_wrong_type(self, session: Session):
        record = DNSRecordModel(
            zone_id="test-zone",
            name="example.com",
            type="A",
            content="192.0.2.1",
            ttl=300,
        )
        session.add(record)
        session.commit()

        resolver = MockflareDNSResolver()
        # Query for TXT but only A record exists
        request = DNSRecord.question("example.com", "TXT")
        reply = resolver.resolve(request, None)

        assert len(reply.rr) == 0

    def test_resolve_any_query(self, session: Session):
        # Create both A and TXT records
        a_record = DNSRecordModel(
            zone_id="test-zone",
            name="any.example.com",
            type="A",
            content="192.0.2.1",
            ttl=300,
        )
        txt_record = DNSRecordModel(
            zone_id="test-zone",
            name="any.example.com",
            type="TXT",
            content="test",
            ttl=300,
        )
        session.add(a_record)
        session.add(txt_record)
        session.commit()

        resolver = MockflareDNSResolver()
        request = DNSRecord.question("any.example.com", "ANY")
        reply = resolver.resolve(request, None)

        assert len(reply.rr) == 2


class TestForwardToUpstream:
    def test_forward_invalid_upstream(self):
        request = DNSRecord.question("example.com", "A")
        # Use invalid IP to trigger failure
        result = forward_to_upstream(request, "192.0.2.999", port=53)
        assert result is None
