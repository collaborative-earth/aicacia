from fastapi import Header, Depends, HTTPException
from sqlmodel import Session, select
from server.auth.auth import verify_jwt_token
from server.db.models.user import User
from server.db.session import get_db_session


def get_current_user(aicacia_api_token: str = Header(None), session: Session = Depends(get_db_session)) -> User:
    if not aicacia_api_token:
        raise HTTPException(status_code=401, detail="Unauthorized: Token missing")

    user_id = verify_jwt_token(aicacia_api_token)

    user = session.exec(select(User).filter(User.user_id == user_id)).first()

    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized: User not found")

    return user
