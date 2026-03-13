from typing import Annotated

from fastapi import Depends, HTTPException, Path
from sqlmodel import Session

from app.database import get_session
from app.models import Zone


def get_zone(
    zone_id: Annotated[str, Path()],
    session: Annotated[Session, Depends(get_session)],
) -> Zone:
    """Dependency that retrieves a zone by ID or raises 404."""
    zone = session.get(Zone, zone_id)
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")
    return zone


# Type alias for cleaner route signatures
ZoneDep = Annotated[Zone, Depends(get_zone)]
SessionDep = Annotated[Session, Depends(get_session)]
