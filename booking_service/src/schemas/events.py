from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class EventCreate(BaseModel):
    movie_id: str = Field(..., min_length=1, max_length=255)
    movie_title: str | None = Field(None, max_length=512)
    starts_at: datetime
    place: str = Field(..., min_length=1, max_length=512)
    seats_limit: int = Field(..., gt=0, le=10000)
    description: str | None = None


class EventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    movie_id: str
    movie_title: str | None
    host_user_id: UUID
    starts_at: datetime
    place: str
    seats_limit: int
    seats_booked: int
    seats_available: int
    description: str | None
    status: str
    created_at: datetime
    updated_at: datetime
