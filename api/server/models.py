import uuid
from datetime import datetime, timezone
from typing import List, Optional

from pydantic import BaseModel
from sqlalchemy import Column, null
from sqlmodel import JSON, Field, Relationship, SQLModel


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(SQLModel):
    """Base class for models"""

    created_at: datetime = Field(default_factory=utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=utcnow, nullable=False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.updated_at = utcnow()

    def save(self, session):
        self.updated_at = utcnow()
        session.add(self)
        session.commit()


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


class Reference(BaseModel):
    title: str
    url: str


class Query(Base, table=True):
    __tablename__ = "queries"
    query_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.user_id", nullable=False)
    question: str
    references: list[dict] = Field(sa_column=Column(JSON))
    summary: Optional[str] = Field()

    user: "User" = Relationship(back_populates="queries")
    feedbacks: List["Feedback"] = Relationship(back_populates="query")


class FeedbackJSON(BaseModel):
    references_feedback: list[int]
    feedback: str


class Feedback(Base, table=True):
    __tablename__ = "feedbacks"
    feedback_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    query_id: uuid.UUID = Field(foreign_key="queries.query_id", nullable=False)
    user_id: uuid.UUID = Field(foreign_key="users.user_id", nullable=False)
    # TODO: Figure out a way to enforce the structure of the json field.
    feedback_json: dict = Field(sa_column=Column(JSON))

    user: "User" = Relationship(back_populates="feedbacks")
    query: "Query" = Relationship(back_populates="feedbacks")
