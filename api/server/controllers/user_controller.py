import uuid

import models
from controllers.base_controller import AicaciaAPI
from fastapi import HTTPException
from fastapi_utils import set_responses
from library import auth
from pydantic import BaseModel
from sqlmodel import select


class UserPostRequest(BaseModel):
    email: str
    password: str


class UserPostResponse(BaseModel):
    pass


class UserController(AicaciaAPI):

    @set_responses(UserPostResponse, 200)
    def post(self, request: UserPostRequest) -> str:
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


class UserLoginRequest(BaseModel):
    email: str
    password: str


class UserLoginResponse(BaseModel):
    token: str


class UserLoginController(AicaciaAPI):

    @set_responses(UserLoginResponse, 200)
    def post(self, request: UserLoginRequest) -> str:
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
