import uuid

import models
from controllers.base_controller import AicaciaAPI
from fastapi_utils import set_responses
from pydantic import BaseModel


class UserQueryPostRequest(BaseModel):
    question: str


class UserQueryPostResponse(BaseModel):
    query_id: str
    references: list[models.Reference]
    summary: str


class UserQueryController(AicaciaAPI):

    @set_responses(UserQueryPostResponse, 200)
    def post(self, request: UserQueryPostRequest) -> str:
        # TODO: query vector db for references and summary

        # TODO: user_id should be taken from the token
        query_id = str(uuid.uuid4())
        query = models.Query(
            query_id=query_id,
            question=request.question,
            references=[models.Reference(title="test", url="test").model_dump()],
            summary="test summary",
            user_id="6eaa9bcd-a5dd-4e22-aa6a-0029ed0c2737",
        )

        session = self.get_db_session()
        session.add(query)
        session.commit()

        return UserQueryPostResponse(
            query_id=query_id,
            references=query.references,
            summary=query.summary,
        )
