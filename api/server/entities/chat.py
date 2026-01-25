import enum
from typing import List, Optional

from pydantic import BaseModel
from server.dtos.query import Reference


class Actor(enum.Enum):
    USER = "user"
    AGENT = "agent"


class ChatMessage(BaseModel):
    message: str
    message_from: Actor
    message_id: Optional[str] = None
    references: Optional[List[Reference]] = None
