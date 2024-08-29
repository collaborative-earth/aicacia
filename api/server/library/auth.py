from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
import models
from config import settings
from fastapi import Header, HTTPException
from library.db_utils import get_db_session
from sqlmodel import select

ONE_DAY = 1 * 24 * 60 * 60


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verfiy_password(password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))


def create_auth_token(user: models.User) -> str:

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


def authenticate(aicacia_api_token: str = Header(None)) -> str:
    if not aicacia_api_token:
        raise HTTPException(status_code=401, detail="Unauthorized: Token missing")

    user_id = verify_jwt_token(aicacia_api_token)

    session = get_db_session()

    user = session.exec(select(models.User).filter(models.User.user_id == user_id)).first()

    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized: User not found")

    return user


def verify_jwt_token(token: str) -> str:
    try:
        decoded_token = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

    return decoded_token["user_id"]
