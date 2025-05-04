import uuid

from typing import List, TYPE_CHECKING
from sqlalchemy import Column, ForeignKeyConstraint, PrimaryKeyConstraint
from sqlmodel import JSON, Field, Relationship
from server.db.models.base import Base

if TYPE_CHECKING:
    from server.db.models.user import User


class ThreadMessages(Base, table=True):
    __tablename__ = "thread_messages"
    thread_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    message_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    user_id: uuid.UUID = Field(foreign_key="users.user_id", nullable=False)
    message_from: str = Field(nullable=False)
    message: str = Field(nullable=False)
    thread_message_json: dict = Field(sa_column=Column(JSON))

    user: "User" = Relationship(back_populates="thread_messages")
    thread_message_feedback: List["ThreadMessageFeedback"] = Relationship(
        back_populates="thread_message"
    )

    __table_args__ = (PrimaryKeyConstraint("thread_id", "message_id"),)


class ThreadMessageFeedback(Base, table=True):
    __tablename__ = "thread_message_feedback"
    thread_id: uuid.UUID = Field(nullable=False, primary_key=True)
    message_id: uuid.UUID = Field(nullable=False, primary_key=True)
    feedback_id: uuid.UUID = Field(primary_key=True)

    user_id: uuid.UUID = Field(foreign_key="users.user_id", nullable=False)
    feedback_json: dict = Field(sa_column=Column(JSON))

    __table_args__ = (
        ForeignKeyConstraint(
            ["thread_id", "message_id"],
            ["thread_messages.thread_id", "thread_messages.message_id"],
        ),
    )

    thread_message: "ThreadMessages" = Relationship(
        back_populates="thread_message_feedback"
    )

    user: "User" = Relationship(back_populates="thread_message_feedback")
