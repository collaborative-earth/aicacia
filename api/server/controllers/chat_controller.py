import uuid

from fastapi import APIRouter, Depends
from sqlmodel import Session
from server.auth.dependencies import get_current_user
from server.dtos.chat import ChatResponse, ChatRequest
from server.entities.chat import ChatMessage, Actor
from server.db.models.thread_messages import ThreadMessages
from server.db.models.user import User
from server.db.session import get_db_session
from server.core.ai_agent import get_chat_response

chat_router = APIRouter()


@chat_router.post("/")
def generate_chat_response(
        request: ChatRequest,
        user: User = Depends(get_current_user),
        db: Session = Depends(get_db_session)
) -> ChatResponse:

    thread_id = request.thread_id or str(uuid.uuid4())

    # get all messages of the thread.
    thread_messages = db.query(ThreadMessages).filter_by(thread_id=thread_id).all()

    chat_history = [
        ChatMessage(
            message=thread_message.message,
            message_from=thread_message.message_from,
            message_id=str(thread_message.message_id),
        )
        for thread_message in thread_messages
    ]

    response = get_chat_response(
        message=request.message,
        chat_history=chat_history,
    )

    chat_history.append(
        ChatMessage(
            message=request.message,
            message_from=Actor.USER,
        )
    )

    chat_history.append(
        ChatMessage(
            message=response,
            message_from=Actor.AGENT,
        )
    )

    db.add(
        ThreadMessages(
            thread_id=thread_id,
            message_id=str(uuid.uuid4()),
            message=request.message,
            message_from=Actor.USER.value,
            user_id=user.user_id,
        )
    )

    db.add(
        ThreadMessages(
            thread_id=thread_id,
            message_id=str(uuid.uuid4()),
            message=response,
            message_from=Actor.AGENT.value,
            user_id=user.user_id,
        )
    )

    db.commit()

    thread_messages = db.query(ThreadMessages).filter_by(thread_id=thread_id).all()

    chat_history = [
        ChatMessage(
            message=thread_message.message,
            message_from=thread_message.message_from,
            message_id=str(thread_message.message_id),
        )
        for thread_message in thread_messages
    ]

    return ChatResponse(
        chat_messages=chat_history,
        thread_id=thread_id,
    )
