import uuid

import models
from controllers.base_controller import AicaciaProtectedAPI, AicaciaPublicAPI
from fastapi import HTTPException
from fastapi_utils.cbv import cbv
from fastapi_utils.inferring_router import InferringRouter
from library import auth
from pydantic import BaseModel
from sqlmodel import select

user_router = InferringRouter()

user_info_router = InferringRouter()


class UserPostRequest(BaseModel):
    email: str
    password: str


class UserPostResponse(BaseModel):
    pass


class UserLoginRequest(BaseModel):
    email: str
    password: str


class UserLoginResponse(BaseModel):
    token: str


class UserGetResponse(BaseModel):
    email: str
    user_id: str


@cbv(user_router)
class UserController(AicaciaPublicAPI):

    @user_router.post("/")
    def post(self, request: UserPostRequest) -> UserPostResponse:
        session = self.get_db_session()

        email = request.email.lower()

        existing_user = session.exec(
            select(models.User).filter(models.User.email == email)
        ).first()

        if existing_user:
            raise HTTPException(
                status_code=400, detail="User with this email already exists"
            )

        hashed_password = auth.hash_password(request.password)

        user = models.User(
            user_id=str(uuid.uuid4()),
            email=email,
            password=hashed_password,
            is_verified=True,
            user_json={},
        )

        session.add(user)
        session.commit()

        return UserPostResponse()

    @user_router.post("/login")
    def login(self, request: UserLoginRequest) -> UserLoginResponse:
        session = self.get_db_session()

        email = request.email.lower()

        user = session.exec(
            select(models.User).filter(models.User.email == email)
        ).first()

        if not user:
            raise HTTPException(status_code=400, detail="User not found")

        if not auth.verfiy_password(request.password, user.password):
            raise HTTPException(status_code=400, detail="Incorrect password")

        token = auth.create_auth_token(user)

        return UserLoginResponse(token=token)


@cbv(user_info_router)
class UserInfoController(AicaciaProtectedAPI):

    @user_info_router.get("/")
    def get(self) -> UserGetResponse:
        return UserGetResponse(email=self.user.email, user_id=str(self.user.user_id))
