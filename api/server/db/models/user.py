import uuid

from typing import List, TYPE_CHECKING
from sqlalchemy import Column
from sqlmodel import JSON, Field, Relationship
from server.db.models.base import Base

if TYPE_CHECKING:
    from server.db.models.query import Query
    from server.db.models.feedback import Feedback
    from server.db.models.thread_messages import ThreadMessages, ThreadMessageFeedback


class User(Base, table=True):
    __tablename__ = "users"
    user_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    email: str = Field(nullable=False, unique=True, index=True)
    password: str = Field(nullable=True)
    is_verified: bool = Field(nullable=True)
    # TODO: Figure out a way to enforce the structure of the json field.
    user_json: dict = Field(sa_column=Column(JSON))

    queries: List["Query"] = Relationship(back_populates="user")
    feedbacks: List["Feedback"] = Relationship(back_populates="user")
    thread_messages: List["ThreadMessages"] = Relationship(back_populates="user")
    thread_message_feedback: List["ThreadMessageFeedback"] = Relationship(back_populates="user")
