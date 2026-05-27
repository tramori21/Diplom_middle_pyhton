import logging

import httpx
from fastapi import HTTPException, status

from core.config import settings

logger = logging.getLogger(__name__)


async def validate_movie(movie_id: str) -> dict | None:
    if not settings.movies_api_validate:
        return None

    url = f"{settings.movies_api_url.rstrip('/')}/api/v1/films/{movie_id}"

    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.get(url)
    except httpx.HTTPError as exc:
        logger.exception("Movies API call failed for movie_id=%s", movie_id)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Movies API unavailable",
        ) from exc

    if response.status_code == status.HTTP_404_NOT_FOUND:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Film not found",
        )

    if response.status_code >= 400:
        logger.warning(
            "Movies API returned unexpected status %s for movie_id=%s",
            response.status_code,
            movie_id,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Movies API error",
        )

    return response.json()