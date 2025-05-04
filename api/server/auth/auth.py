import jwt

from typing import Optional
from datetime import datetime, timedelta, timezone
from server.core.config import settings
from server.db.models.user import User

ONE_DAY = 1 * 24 * 60 * 60


def create_jwt_token(user: User) -> str:
    exp = datetime.now(timezone.utc) + timedelta(seconds=ONE_DAY)

    return jwt.encode(
        {
            "user_id": str(user.user_id),
            "email": user.email,
            "exp": exp,
        },
        settings.SECRET_KEY,
        algorithm="HS256",
    )


def verify_jwt_token(token: str) -> Optional[str]:
    try:
        decoded_token = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        return decoded_token["user_id"]
    except jwt.PyJWTError:
        return None
