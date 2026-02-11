from fastapi import APIRouter
from sqlmodel import SQLModel

from app.database import engine
from app.seed import seed_database

router = APIRouter(prefix="/mockflare", tags=["Mockflare"])


@router.post("/reset")
def reset_database():
    """Drop all tables and recreate them. Re-seeds if SEED_DATA is set."""
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
    seed_database()
    return {"success": True, "message": "Database reset"}
