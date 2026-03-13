import logging
from collections.abc import Generator
from pathlib import Path
from urllib.parse import urlparse

from sqlalchemy import event, inspect, text
from sqlmodel import Session, SQLModel, create_engine

from app.config import settings

logger = logging.getLogger("mockflare")


def _get_engine():
    """Create engine, ensuring PostgreSQL database exists first."""
    if settings.database_url.startswith("postgresql") and settings.create_db:
        _ensure_postgres_database_exists()
    return create_engine(settings.database_url, echo=False)


def _ensure_postgres_database_exists() -> None:
    """Create PostgreSQL database if it doesn't exist."""
    parsed = urlparse(settings.database_url)
    db_name = parsed.path.lstrip("/")

    if not db_name:
        return

    # Connect to default 'postgres' database to create our database
    admin_url = settings.database_url.rsplit("/", 1)[0] + "/postgres"
    admin_engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")

    try:
        with admin_engine.connect() as conn:
            result = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :db_name"),
                {"db_name": db_name},
            )
            if not result.fetchone():
                conn.execute(text(f'CREATE DATABASE "{db_name}"'))
                logger.info(f"Created PostgreSQL database: {db_name}")
    finally:
        admin_engine.dispose()


engine = _get_engine()


# Enable foreign key support for SQLite
if settings.database_url.startswith("sqlite"):

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def _sqlite_db_exists() -> bool:
    """Check if SQLite database file exists."""
    if not settings.database_url.startswith("sqlite"):
        return False

    parsed = urlparse(settings.database_url)
    # Remove leading slash: sqlite:///./rel.db → /./rel.db → ./rel.db
    #                       sqlite:////abs.db → //abs.db → /abs.db
    db_path = parsed.path[1:] if parsed.path.startswith("/") else parsed.path

    if db_path in (":memory:", ""):
        return False

    return Path(db_path).exists()


def _tables_exist() -> bool:
    """Check if tables already exist in the database."""
    inspector = inspect(engine)
    return "zones" in inspector.get_table_names()


def init_database() -> bool:
    """
    Initialize database if needed.

    Returns True if database was newly created, False if it already existed.
    """
    if not settings.create_db:
        return False

    # For SQLite, check if file exists
    if settings.database_url.startswith("sqlite") and not _sqlite_db_exists():
        SQLModel.metadata.create_all(engine)
        return True

    # For other databases, check if tables exist
    if not _tables_exist():
        SQLModel.metadata.create_all(engine)
        return True

    return False


def get_session() -> Generator[Session]:
    with Session(engine) as session:
        yield session
