from typing import Annotated

from fastapi import APIRouter, Depends
from sqlmodel import Session, SQLModel

from app.database import get_session
from app.seed import seed_database

router = APIRouter(prefix="/mockflare", tags=["Mockflare"])


@router.post("/reset")
def reset_database(session: Annotated[Session, Depends(get_session)]):
    """Drop all tables and recreate them. Re-seeds if SEED_DATA is set."""
    engine = session.get_bind()
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
    seed_database(engine)
    return {"success": True, "message": "Database reset"}
