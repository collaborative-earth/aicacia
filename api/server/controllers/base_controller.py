import models
from fastapi import Depends
from library import auth, db_utils
from sqlmodel import Session


class AicaciaProtectedAPI:

    user: models.User = Depends(auth.authenticate)

    def get_db_session(self) -> Session:
        return db_utils.get_db_session()


class AicaciaPublicAPI:

    def get_db_session(self) -> Session:
        return db_utils.get_db_session()
