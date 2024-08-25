import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import Column
from sqlmodel import JSON, Field, Relationship, SQLModel


def utcnow() -> datetime:
    return datetime.utc(datetime.UTC)


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
    email: str = Field(nullable=False)
    # TODO: Add structure to the json field.
    user_json: dict = Field(sa_column=Column(JSON))

    queries: List["Query"] = Relationship(back_populates="user")
    feedbacks: List["Feedback"] = Relationship(back_populates="user")


class Query(Base, table=True):
    __tablename__ = "queries"
    query_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.user_id", nullable=False)
    question: str
    references: dict = Field(sa_column=Column(JSON))
    summary: Optional[str] = Field()

    user: "User" = Relationship(back_populates="queries")
    feedbacks: List["Feedback"] = Relationship(back_populates="query")


class Feedback(Base, table=True):
    __tablename__ = "feedbacks"
    feedback_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    query_id: uuid.UUID = Field(foreign_key="queries.query_id", nullable=False)
    user_id: uuid.UUID = Field(foreign_key="users.user_id", nullable=False)
    # TODO: Add structure to the json field.
    feedback_json: dict = Field(sa_column=Column(JSON))

    user: "User" = Relationship(back_populates="feedbacks")
    query: "Query" = Relationship(back_populates="feedbacks")
