from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_user_id
from api.pagination import Pagination
from db.postgres import get_session
from models.booking import Booking
from models.event import WatchEvent
from schemas.bookings import BookingResponse, MyBookingResponse
from schemas.events import EventCreate, EventResponse
from services.movies import validate_movie

router = APIRouter()


def _active_bookings_subquery():
    return (
        select(
            Booking.event_id.label("event_id"),
            func.count(Booking.id).label("seats_booked"),
        )
        .where(Booking.status == "active")
        .group_by(Booking.event_id)
        .subquery()
    )


async def _active_bookings_count(session: AsyncSession, event_id: UUID) -> int:
    result = await session.execute(
        select(func.count(Booking.id)).where(
            Booking.event_id == event_id,
            Booking.status == "active",
        )
    )
    return int(result.scalar_one())


def _to_event_response(event: WatchEvent, seats_booked: int = 0) -> EventResponse:
    seats_booked = int(seats_booked or 0)
    return EventResponse(
        id=event.id,
        movie_id=event.movie_id,
        movie_title=event.movie_title,
        host_user_id=event.host_user_id,
        starts_at=event.starts_at,
        place=event.place,
        seats_limit=event.seats_limit,
        seats_booked=seats_booked,
        seats_available=max(event.seats_limit - seats_booked, 0),
        description=event.description,
        status=event.status,
        created_at=event.created_at,
        updated_at=event.updated_at,
    )


@router.post("", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def create_event(
    payload: EventCreate,
    user_id: UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
):
    movie_data = await validate_movie(payload.movie_id)
    movie_title = payload.movie_title

    if movie_data and not movie_title:
        movie_title = movie_data.get("title")

    event = WatchEvent(
        movie_id=payload.movie_id,
        movie_title=movie_title,
        host_user_id=user_id,
        starts_at=payload.starts_at,
        place=payload.place,
        seats_limit=payload.seats_limit,
        description=payload.description,
    )

    session.add(event)
    await session.commit()
    await session.refresh(event)

    return _to_event_response(event)


@router.get("", response_model=list[EventResponse])
async def list_events(
    pagination: Pagination = Depends(),
    session: AsyncSession = Depends(get_session),
):
    bookings_count = _active_bookings_subquery()
    result = await session.execute(
        select(
            WatchEvent,
            func.coalesce(bookings_count.c.seats_booked, 0).label("seats_booked"),
        )
        .outerjoin(bookings_count, bookings_count.c.event_id == WatchEvent.id)
        .where(WatchEvent.status == "active")
        .order_by(WatchEvent.starts_at)
        .offset(pagination.offset)
        .limit(pagination.page_size)
    )

    return [_to_event_response(event, seats_booked) for event, seats_booked in result.all()]


@router.get("/bookings/me", response_model=list[MyBookingResponse])
async def my_bookings(
    user_id: UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
):
    bookings_count = _active_bookings_subquery()
    result = await session.execute(
        select(
            Booking,
            WatchEvent,
            func.coalesce(bookings_count.c.seats_booked, 0).label("seats_booked"),
        )
        .join(WatchEvent, Booking.event_id == WatchEvent.id)
        .outerjoin(bookings_count, bookings_count.c.event_id == WatchEvent.id)
        .where(Booking.user_id == user_id)
        .order_by(Booking.created_at.desc())
    )

    items = []
    for booking, event, seats_booked in result.all():
        items.append(
            MyBookingResponse(
                id=booking.id,
                event_id=booking.event_id,
                user_id=booking.user_id,
                status=booking.status,
                created_at=booking.created_at,
                updated_at=booking.updated_at,
                event=_to_event_response(event, seats_booked),
            )
        )

    return items


@router.get("/{event_id}", response_model=EventResponse)
async def get_event(
    event_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    bookings_count = _active_bookings_subquery()
    result = await session.execute(
        select(
            WatchEvent,
            func.coalesce(bookings_count.c.seats_booked, 0).label("seats_booked"),
        )
        .outerjoin(bookings_count, bookings_count.c.event_id == WatchEvent.id)
        .where(
            WatchEvent.id == event_id,
            WatchEvent.status == "active",
        )
    )
    row = result.one_or_none()

    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    event, seats_booked = row
    return _to_event_response(event, seats_booked)


@router.post("/{event_id}/booking", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
async def book_event(
    event_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
):
    async with session.begin():
        event_result = await session.execute(
            select(WatchEvent)
            .where(WatchEvent.id == event_id)
            .with_for_update()
        )
        event = event_result.scalar_one_or_none()

        if not event:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

        if event.status != "active":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Event is not active")

        existing_result = await session.execute(
            select(Booking).where(
                Booking.event_id == event_id,
                Booking.user_id == user_id,
                Booking.status == "active",
            )
        )
        existing = existing_result.scalar_one_or_none()

        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Booking already exists")

        seats_booked = await _active_bookings_count(session, event_id)
        if seats_booked >= event.seats_limit:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="No seats available")

        booking = Booking(event_id=event_id, user_id=user_id)
        session.add(booking)

    await session.refresh(booking)
    return booking


@router.delete("/{event_id}/booking")
async def cancel_my_booking(
    event_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(Booking).where(
            Booking.event_id == event_id,
            Booking.user_id == user_id,
            Booking.status == "active",
        )
    )
    booking = result.scalar_one_or_none()

    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Active booking not found")

    booking.status = "cancelled"
    session.add(booking)
    await session.commit()

    return {"status": "ok"}


@router.patch("/{event_id}/cancel", response_model=EventResponse)
async def cancel_event(
    event_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(select(WatchEvent).where(WatchEvent.id == event_id))
    event = result.scalar_one_or_none()

    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    if event.host_user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only host can cancel event")

    event.status = "cancelled"
    session.add(event)
    await session.commit()
    await session.refresh(event)

    seats_booked = await _active_bookings_count(session, event.id)
    return _to_event_response(event, seats_booked)