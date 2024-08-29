import models
from controllers.base_controller import AicaciaProtectedAPI
from fastapi_utils.cbv import cbv
from fastapi_utils.inferring_router import InferringRouter
from sqlmodel import Session, select

hello_router = InferringRouter()


@cbv(hello_router)
class HelloworldController(AicaciaProtectedAPI):

    @hello_router.get("/")
    def get(self) -> str:
        session: Session = self.get_db_session()

        # get all users
        users = session.exec(select(models.User)).all()

        return f"Hello, World! {len(users)} users in the database."
