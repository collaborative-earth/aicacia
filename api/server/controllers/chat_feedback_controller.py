import uuid

from fastapi import HTTPException, APIRouter, Depends
from sqlmodel import Session, select
from server.auth.dependencies import get_current_user
from db.models.thread_messages import ThreadMessages, ThreadMessageFeedback
from db.models.user import User
from db.db_manager import get_db_session
from server.dtos.feedback import ChatFeedbackPostRequest, ChatFeedbackPostResponse
from server.entities.thread_message import ThreadMessageFeedbackDetails

chat_feedback_router = APIRouter()


@chat_feedback_router.post("/")
def save_chat_feedback(
        request: ChatFeedbackPostRequest,
        user: User = Depends(get_current_user),
        db: Session = Depends(get_db_session)
) -> ChatFeedbackPostResponse:

    thread_message = db.exec(
        select(ThreadMessages).filter(
            ThreadMessages.message_id == request.message_id,
            ThreadMessages.thread_id == request.thread_id,
        )).first()

    if not thread_message:
        raise HTTPException(status_code=400, detail="thread message does not exist")

    chat_feedback = ThreadMessageFeedback(
        feedback_id=str(uuid.uuid4()),
        message_id=request.message_id,
        thread_id=request.thread_id,
        user_id=user.user_id,
        feedback_json=ThreadMessageFeedbackDetails(
            feedback=request.feedback,
            feedback_message=request.feedback_message,
        ).model_dump(),
    )

    db.add(chat_feedback)
    db.commit()

    return ChatFeedbackPostResponse()
