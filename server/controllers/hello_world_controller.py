import models
from controllers.base_controller import AicaciaAPI
from sqlmodel import Session, select


class HelloworldController(AicaciaAPI):
    def get(self) -> str:
        session: Session = self.get_db_session()

        # get all users
        users = session.exec(select(models.User)).all()

        return f"Hello, World! {len(users)} users in the database."
