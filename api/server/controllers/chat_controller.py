import uuid
from typing import Optional

import models
from controllers.base_controller import AicaciaProtectedAPI
from fastapi_utils.cbv import cbv
from fastapi_utils.inferring_router import InferringRouter
from library import aicacia_ai_agent
from pydantic import BaseModel

chat_router = InferringRouter()


class ChatRequest(BaseModel):
    message: str
    thread_id: Optional[str] = None


class ChatResponse(BaseModel):
    chat_messages: list[models.ChatMessage]
    thread_id: str


@cbv(chat_router)
class ChatController(AicaciaProtectedAPI):

    @chat_router.post("/")
    def post(self, request: ChatRequest) -> ChatResponse:
        thread_id = request.thread_id or str(uuid.uuid4())

        session = self.get_db_session()

        # get all messages of the thread.
        thread_messages = (
            session.query(models.ThreadMessages).filter_by(thread_id=thread_id).all()
        )

        chat_history = [
            models.ChatMessage(
                message=thread_message.message,
                message_from=thread_message.message_from,
            )
            for thread_message in thread_messages
        ]

        response = aicacia_ai_agent.get_chat_response(
            message=request.message,
            chat_history=chat_history,
        )

        chat_history.append(
            models.ChatMessage(
                message=request.message,
                message_from=models.Actor.USER,
            )
        )

        chat_history.append(
            models.ChatMessage(
                message=response,
                message_from=models.Actor.AGENT,
            )
        )

        session.add(
            models.ThreadMessages(
                thread_id=thread_id,
                message_id=str(uuid.uuid4()),
                message=request.message,
                message_from=models.Actor.USER.value,
                user_id=self.user.user_id,
            )
        )

        session.add(
            models.ThreadMessages(
                thread_id=thread_id,
                message_id=str(uuid.uuid4()),
                message=response,
                message_from=models.Actor.AGENT.value,
                user_id=self.user.user_id,
            )
        )

        session.commit()

        return ChatResponse(
            chat_messages=chat_history,
            thread_id=thread_id,
        )
