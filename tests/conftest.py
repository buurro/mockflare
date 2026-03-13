import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from app.database import get_session
from app.dns_server import set_dns_engine
from app.main import app
from app.models import Zone


@pytest.fixture(name="engine")
def engine_fixture():
    """Create a shared in-memory SQLite engine for tests."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    # Set the DNS engine to use the test engine
    set_dns_engine(engine)
    yield engine
    # Reset the DNS engine after tests
    set_dns_engine(None)
    engine.dispose()


@pytest.fixture(name="session")
def session_fixture(engine):
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture(name="zone")
def zone_fixture(session: Session) -> Zone:
    """Create a test zone for use in tests that require one."""
    zone = Zone(
        id="test-zone-123",
        name="example.com",
        account_id="test-account",
        name_servers=["ns1.mockflare.local", "ns2.mockflare.local"],
    )
    session.add(zone)
    session.commit()
    session.refresh(zone)
    return zone
