import uuid

import bcrypt
from fastapi import APIRouter, Depends, HTTPException
from server.auth.auth import create_jwt_token
from server.auth.dependencies import get_current_user
from db.models.user import User
from core.db_manager import get_db_session
from server.dtos.user import (
    AdminUserListResponse,
    UserGetResponse,
    UserLoginRequest,
    UserLoginResponse,
    UserPostRequest,
    UserPostResponse,
)
from sqlmodel import Session, select

user_router = APIRouter()

user_info_router = APIRouter()

admin_router = APIRouter()


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _verify_password(password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))


def get_admin_user(user: User = Depends(get_current_user)) -> User:
    """Dependency to ensure user is admin"""
    is_admin = user.user_json.get("admin", False) if user.user_json else False
    if not is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


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
    is_admin = user.user_json.get("admin", False) if user.user_json else False
    return UserGetResponse(
        email=user.email, user_id=str(user.user_id), is_admin=is_admin
    )


@admin_router.get("/users")
def list_all_users(
    admin_user: User = Depends(get_admin_user), db: Session = Depends(get_db_session)
) -> AdminUserListResponse:
    """List all users - admin only"""
    users = db.exec(select(User)).all()

    user_list = []
    for user in users:
        is_admin = user.user_json.get("admin", False) if user.user_json else False
        user_list.append(
            {
                "user_id": str(user.user_id),
                "email": user.email,
                "is_admin": is_admin,
                "created_at": user.created_at,
            }
        )

    return AdminUserListResponse(users=user_list)
