import uuid

import models
from controllers.base_controller import AicaciaAPI
from fastapi_utils import set_responses
from pydantic import BaseModel


class FeedbackPostRequest(BaseModel):
    query_id: str
    helpful: bool
    feedback: str


class FeedbackPostResponse(BaseModel):
    pass


class FeedbackController(AicaciaAPI):

    @set_responses(FeedbackPostResponse, 200)
    def post(self, request: FeedbackPostRequest) -> str:
        # TODO: user_id should be taken from the token
        feedback_id = str(uuid.uuid4())
        feedback = models.Feedback(
            feedback_id=feedback_id,
            query_id=request.query_id,
            user_id="6eaa9bcd-a5dd-4e22-aa6a-0029ed0c2737",
            feedback_json=models.FeedbackJSON(
                helpful=request.helpful,
                feedback=request.feedback,
            ).model_dump(),
        )

        session = self.get_db_session()
        session.add(feedback)
        session.commit()

        return FeedbackPostResponse()
