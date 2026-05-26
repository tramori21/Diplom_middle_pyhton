from fastapi import APIRouter

from api.v1 import events

router = APIRouter()
router.include_router(events.router, prefix="/api/v1/events", tags=["events"])
