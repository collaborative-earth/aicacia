import enum
from typing import Optional

from pydantic import BaseModel


class Actor(enum.Enum):
    USER = "user"
    AGENT = "agent"

class ChatMessage(BaseModel):
    message: str
    message_from: Actor
    message_id: Optional[str] = None
