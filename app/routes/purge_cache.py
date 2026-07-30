from fastapi import APIRouter
from pydantic import BaseModel

from app.models import generate_uuid
from app.schemas import CloudflareResponse, make_response

router = APIRouter(prefix="/zones/{zone_id}/purge_cache", tags=["Cache"])


class PurgeCacheResponse(BaseModel):
    id: str


@router.post("", response_model=CloudflareResponse[PurgeCacheResponse])
def purge_cache(
    zone_id: str,
):
    return make_response(PurgeCacheResponse(id=generate_uuid()))
