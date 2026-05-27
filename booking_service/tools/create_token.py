from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from jose import jwt

from core.config import settings


def create_access_token(user_id: str) -> str:
    UUID(user_id)
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=12)).timestamp()),
        "jti": str(uuid4()),
    }
    return jwt.encode(
        payload,
        settings.auth_jwt_secret,
        algorithm=settings.auth_jwt_algorithm,
    )


if __name__ == "__main__":
    demo_user_id = "00000000-0000-0000-0000-000000000001"
    print(create_access_token(demo_user_id))