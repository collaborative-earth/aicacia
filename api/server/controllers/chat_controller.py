import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, func, select
from server.auth.dependencies import get_current_user
from server.dtos.chat import ChatResponse, ChatRequest, ThreadListResponse, ThreadSummary
from server.entities.chat import ChatMessage, Actor
from db.models.thread_messages import ThreadMessages
from db.models.user import User
from db.db_manager import get_db_session
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


@chat_router.get("/threads")
def get_user_threads(
        user: User = Depends(get_current_user),
        db: Session = Depends(get_db_session)
) -> ThreadListResponse:
    """Get all chat threads for the current user."""

    # Get distinct thread_ids for the user with message counts and last message time
    stmt = (
        select(
            ThreadMessages.thread_id,
            func.count(ThreadMessages.message_id).label('message_count'),
            func.max(ThreadMessages.created_at).label('last_message_time')
        )
        .where(ThreadMessages.user_id == user.user_id)
        .group_by(ThreadMessages.thread_id)
        .order_by(func.max(ThreadMessages.created_at).desc())
    )

    results = db.exec(stmt).all()

    threads = []
    for thread_id, message_count, last_message_time in results:
        # Get the last message for preview
        last_message_record = (
            db.query(ThreadMessages)
            .filter_by(thread_id=thread_id, user_id=user.user_id)
            .order_by(ThreadMessages.created_at.desc())
            .first()
        )

        if last_message_record:
            threads.append(
                ThreadSummary(
                    thread_id=str(thread_id),
                    last_message=last_message_record.message[:100],  # Truncate for preview
                    last_message_time=last_message_time,
                    message_count=message_count
                )
            )

    return ThreadListResponse(threads=threads)


@chat_router.get("/threads/{thread_id}")
def get_thread_messages(
        thread_id: str,
        user: User = Depends(get_current_user),
        db: Session = Depends(get_db_session)
) -> ChatResponse:
    """Get all messages for a specific thread."""

    # Verify the thread belongs to the user and get all messages
    thread_messages = db.query(ThreadMessages).filter_by(
        thread_id=thread_id,
        user_id=user.user_id
    ).order_by(ThreadMessages.created_at.asc()).all()

    if not thread_messages:
        raise HTTPException(status_code=404, detail="Thread not found")

    chat_messages = [
        ChatMessage(
            message=thread_message.message,
            message_from=thread_message.message_from,
            message_id=str(thread_message.message_id),
        )
        for thread_message in thread_messages
    ]

    return ChatResponse(
        chat_messages=chat_messages,
        thread_id=thread_id,
    )


@chat_router.delete("/threads/{thread_id}")
def delete_thread(
        thread_id: str,
        user: User = Depends(get_current_user),
        db: Session = Depends(get_db_session)
) -> dict:
    """Delete a chat thread and all its messages."""

    # Verify the thread belongs to the user
    thread_messages = db.query(ThreadMessages).filter_by(
        thread_id=thread_id,
        user_id=user.user_id
    ).all()

    if not thread_messages:
        raise HTTPException(status_code=404, detail="Thread not found")

    # Delete all messages in the thread
    for message in thread_messages:
        db.delete(message)

    db.commit()

    return {"status": "success", "message": "Thread deleted successfully"}
