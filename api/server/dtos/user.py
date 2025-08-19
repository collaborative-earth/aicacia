from pydantic import BaseModel


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
    is_admin: bool


class AdminUserListResponse(BaseModel):
    users: list[dict]
