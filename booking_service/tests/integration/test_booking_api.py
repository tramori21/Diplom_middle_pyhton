from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import httpx
import pytest
from jose import jwt

BASE_URL = "http://127.0.0.1:8010"
SECRET = "change_me"
ALGORITHM = "HS256"


def create_token(user_id: str) -> str:
    UUID(user_id)
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=12)).timestamp()),
        "jti": str(uuid4()),
    }
    return jwt.encode(payload, SECRET, algorithm=ALGORITHM)


@pytest.fixture()
def user_headers() -> dict[str, str]:
    token = create_token("00000000-0000-0000-0000-000000000001")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def other_user_headers() -> dict[str, str]:
    token = create_token("00000000-0000-0000-0000-000000000002")
    return {"Authorization": f"Bearer {token}"}


def test_health() -> None:
    response = httpx.get(f"{BASE_URL}/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_booking_flow(user_headers: dict[str, str]) -> None:
    create_response = httpx.post(
        f"{BASE_URL}/api/v1/events",
        headers=user_headers,
        json={
            "movie_id": f"movie-{uuid4()}",
            "movie_title": "Demo Movie",
            "starts_at": "2026-06-01T19:00:00Z",
            "place": "Demo cinema",
            "seats_limit": 1,
            "description": "Demo watch event",
        },
    )

    assert create_response.status_code == 201

    event = create_response.json()
    event_id = event["id"]

    assert event["seats_limit"] == 1
    assert event["seats_booked"] == 0
    assert event["seats_available"] == 1
    assert event["status"] == "active"

    detail_response = httpx.get(f"{BASE_URL}/api/v1/events/{event_id}")

    assert detail_response.status_code == 200
    assert detail_response.json()["id"] == event_id

    booking_response = httpx.post(
        f"{BASE_URL}/api/v1/events/{event_id}/booking",
        headers=user_headers,
    )

    assert booking_response.status_code == 201
    assert booking_response.json()["status"] == "active"

    duplicate_response = httpx.post(
        f"{BASE_URL}/api/v1/events/{event_id}/booking",
        headers=user_headers,
    )

    assert duplicate_response.status_code == 409

    my_bookings_response = httpx.get(
        f"{BASE_URL}/api/v1/events/bookings/me",
        headers=user_headers,
    )

    assert my_bookings_response.status_code == 200
    assert len(my_bookings_response.json()) >= 1

    cancel_booking_response = httpx.delete(
        f"{BASE_URL}/api/v1/events/{event_id}/booking",
        headers=user_headers,
    )

    assert cancel_booking_response.status_code == 200
    assert cancel_booking_response.json() == {"status": "ok"}

    rebooking_response = httpx.post(
        f"{BASE_URL}/api/v1/events/{event_id}/booking",
        headers=user_headers,
    )

    assert rebooking_response.status_code == 201

    cancel_event_response = httpx.patch(
        f"{BASE_URL}/api/v1/events/{event_id}/cancel",
        headers=user_headers,
    )

    assert cancel_event_response.status_code == 200
    assert cancel_event_response.json()["status"] == "cancelled"

    cancelled_event_booking_response = httpx.post(
        f"{BASE_URL}/api/v1/events/{event_id}/booking",
        headers=user_headers,
    )

    assert cancelled_event_booking_response.status_code == 409


def test_only_host_can_cancel_event(
    user_headers: dict[str, str],
    other_user_headers: dict[str, str],
) -> None:
    create_response = httpx.post(
        f"{BASE_URL}/api/v1/events",
        headers=user_headers,
        json={
            "movie_id": f"movie-{uuid4()}",
            "movie_title": "Demo Movie",
            "starts_at": "2026-06-02T19:00:00Z",
            "place": "Demo cinema",
            "seats_limit": 5,
            "description": "Demo watch event",
        },
    )

    assert create_response.status_code == 201

    event_id = create_response.json()["id"]

    forbidden_response = httpx.patch(
        f"{BASE_URL}/api/v1/events/{event_id}/cancel",
        headers=other_user_headers,
    )

    assert forbidden_response.status_code == 403