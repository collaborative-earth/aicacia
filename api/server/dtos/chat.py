from typing import Optional
from datetime import datetime
from pydantic import BaseModel
from server.entities.chat import ChatMessage


class ChatRequest(BaseModel):
    message: str
    thread_id: Optional[str] = None


class ChatResponse(BaseModel):
    chat_messages: list[ChatMessage]
    thread_id: str


class ThreadSummary(BaseModel):
    thread_id: str
    last_message: str
    last_message_time: datetime
    message_count: int


class ThreadListResponse(BaseModel):
    threads: list[ThreadSummary]
