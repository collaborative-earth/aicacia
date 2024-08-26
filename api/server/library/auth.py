import bcrypt
import jwt
import models
from config import settings


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verfiy_password(password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))


def create_auth_token(user: models.User) -> str:
    return jwt.encode(
        {"user_id": str(user.user_id), "email": user.email},
        settings.SECRET_KEY,
        algorithm="HS256",
    )


def verify_jwt_token(token: str) -> str:
    decoded_token = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    return decoded_token["user_id"]
