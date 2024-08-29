import uuid

import models
from controllers.base_controller import AicaciaProtectedAPI
from fastapi_utils.cbv import cbv
from fastapi_utils.inferring_router import InferringRouter
from pydantic import BaseModel

user_query_router = InferringRouter()


class UserQueryPostRequest(BaseModel):
    question: str


class UserQueryPostResponse(BaseModel):
    query_id: str
    references: list[models.Reference]
    summary: str


@cbv(user_query_router)
class UserQueryController(AicaciaProtectedAPI):

    @user_query_router.post("/")
    def post(self, request: UserQueryPostRequest) -> UserQueryPostResponse:
        # TODO: query vector db for references and summary

        query_id = str(uuid.uuid4())
        query = models.Query(
            query_id=query_id,
            question=request.question,
            references=[models.Reference(title="test", url="test").model_dump()],
            summary="test summary",
            user_id=self.user.user_id,
        )

        session = self.get_db_session()
        session.add(query)
        session.commit()

        return UserQueryPostResponse(
            query_id=query_id,
            references=query.references,
            summary=query.summary,
        )
