import uuid
import bcrypt

from fastapi import Depends
from fastapi import HTTPException, APIRouter
from sqlmodel import Session
from sqlmodel import select
from server.auth.auth import create_jwt_token
from server.auth.dependencies import get_current_user
from server.db.models.user import User
from server.db.session import get_db_session
from server.dtos.user import UserPostRequest, UserPostResponse, UserLoginRequest, UserLoginResponse, UserGetResponse

user_router = APIRouter()

user_info_router = APIRouter()


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _verify_password(password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))


@user_router.post("/")
def register(request: UserPostRequest, db: Session = Depends(get_db_session)) -> UserPostResponse:
    email = request.email.lower()

    existing_user = db.exec(select(User).filter(User.email == email)).first()

    if existing_user:
        raise HTTPException(status_code=400, detail="User with this email already exists")

    hashed_password = _hash_password(request.password)

    user = User(
        user_id=str(uuid.uuid4()),
        email=email,
        password=hashed_password,
        is_verified=True,
        user_json={},
    )

    db.add(user)
    db.commit()
    return UserPostResponse()


@user_router.post("/login")
def login(request: UserLoginRequest, db: Session = Depends(get_db_session)) -> UserLoginResponse:
    email = request.email.lower()

    user: User = db.exec(select(User).filter(User.email == email)).first()

    if not user:
        raise HTTPException(status_code=400, detail="User not found")

    if not _verify_password(request.password, user.password):
        raise HTTPException(status_code=400, detail="Incorrect password")

    token = create_jwt_token(user)

    return UserLoginResponse(token=token)


@user_info_router.get("/")
def get_user_info(user: User = Depends(get_current_user)) -> UserGetResponse:
    return UserGetResponse(email=user.email, user_id=str(user.user_id))
