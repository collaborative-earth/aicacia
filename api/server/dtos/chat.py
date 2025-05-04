from typing import Optional
from pydantic import BaseModel
from server.entities.chat import ChatMessage


class ChatRequest(BaseModel):
    message: str
    thread_id: Optional[str] = None


class ChatResponse(BaseModel):
    chat_messages: list[ChatMessage]
    thread_id: str
