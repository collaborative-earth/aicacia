import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Column
from sqlmodel import JSON, Field, Relationship
from server.db.models.base import Base

if TYPE_CHECKING:
    from server.db.models.user import User
    from server.db.models.query import Query


class Feedback(Base, table=True):
    __tablename__ = "feedbacks"
    feedback_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    query_id: uuid.UUID = Field(foreign_key="queries.query_id", nullable=False)
    user_id: uuid.UUID = Field(foreign_key="users.user_id", nullable=False)
    # TODO: Figure out a way to enforce the structure of the json field.
    feedback_json: dict = Field(sa_column=Column(JSON))

    user: "User" = Relationship(back_populates="feedbacks")
    query: "Query" = Relationship(back_populates="feedbacks")
