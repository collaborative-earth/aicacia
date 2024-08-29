import uuid

import models
from controllers.base_controller import AicaciaProtectedAPI
from fastapi import HTTPException
from fastapi_utils.cbv import cbv
from fastapi_utils.inferring_router import InferringRouter
from pydantic import BaseModel
from sqlalchemy import select

feedback_router = InferringRouter()


class FeedbackPostRequest(BaseModel):
    query_id: str
    references_feedback: list[bool]
    feedback: str


class FeedbackPostResponse(BaseModel):
    pass


@cbv(feedback_router)
class FeedbackController(AicaciaProtectedAPI):

    @feedback_router.post("/")
    def post(self, request: FeedbackPostRequest) -> FeedbackPostResponse:

        query = (
            self.get_db_session()
            .exec(
                select(models.Query).filter(models.Query.query_id == request.query_id)
            )
            .first()
        )

        if not query:
            raise HTTPException(status_code=400, detail="Query does not exist")

        if len(request.references_feedback) != len(query[0].references):
            raise HTTPException(
                status_code=400,
                detail="References feedback should have the same length as the references",
            )

        feedback_id = str(uuid.uuid4())
        feedback = models.Feedback(
            feedback_id=feedback_id,
            query_id=request.query_id,
            user_id=self.user.user_id,
            feedback_json=models.FeedbackJSON(
                references_feedback=request.references_feedback,
                feedback=request.feedback,
            ).model_dump(),
        )

        session = self.get_db_session()
        session.add(feedback)
        session.commit()

        return FeedbackPostResponse()
