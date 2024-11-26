import uuid

import models
from controllers.base_controller import AicaciaProtectedAPI
from fastapi import HTTPException
from fastapi_utils.cbv import cbv
from fastapi_utils.inferring_router import InferringRouter
from pydantic import BaseModel
from sqlalchemy import select

chat_feedback_router = InferringRouter()


class ChatFeedbackPostRequest(BaseModel):
    thread_id: str
    message_id: str
    feedback_message: str
    feedback: int


class ChatFeedbackPostResponse(BaseModel):
    pass


@cbv(chat_feedback_router)
class ChatFeedbackController(AicaciaProtectedAPI):

    @chat_feedback_router.post("/")
    def post(self, request: ChatFeedbackPostRequest) -> ChatFeedbackPostResponse:

        session = self.get_db_session()

        thread_message = session.exec(
            select(models.ThreadMessages).filter(
                models.ThreadMessages.message_id == request.message_id,
                models.ThreadMessages.thread_id == request.thread_id,
            )
        ).first()

        if not thread_message:
            raise HTTPException(status_code=400, detail="thread message does not exist")

        chat_feedback = models.ThreadMessageFeedback(
            feedback_id=str(uuid.uuid4()),
            message_id=request.message_id,
            thread_id=request.thread_id,
            user_id=self.user.user_id,
            feedback_json=models.ThreadMessageFeedbackJSON(
                feedback=request.feedback,
                feedback_message=request.feedback_message,
            ).model_dump(),
        )

        session.add(chat_feedback)
        session.commit()

        return ChatFeedbackPostResponse()
