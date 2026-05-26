from fastapi import HTTPException, status
import httpx

from core.config import settings


async def validate_movie(movie_id: str) -> dict | None:
    if not settings.movies_api_validate:
        return None

    url = f"{settings.movies_api_url.rstrip('/')}/api/v1/films/{movie_id}"

    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.get(url)
    except httpx.HTTPError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Movies API unavailable",
        )

    if response.status_code == status.HTTP_404_NOT_FOUND:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Film not found",
        )

    if response.status_code >= 400:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Movies API error",
        )

    return response.json()
