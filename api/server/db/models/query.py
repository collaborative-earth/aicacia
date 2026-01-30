import uuid

from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import Column
from sqlmodel import JSON, Field, Relationship
from server.db.models.base import Base

if TYPE_CHECKING:
    from server.db.models.user import User
    from server.db.models.feedback import Feedback


class Query(Base, table=True):
    __tablename__ = "queries"
    query_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.user_id", nullable=False)
    experiment_id: Optional[uuid.UUID] = Field(
        foreign_key="experiments.experiment_id", nullable=True
    )
    question: str
    references: list[dict] = Field(sa_column=Column(JSON))
    summary: Optional[str] = Field()
    experiment_responses: Optional[list[dict]] = Field(
        default=None, sa_column=Column(JSON)
    )

    user: "User" = Relationship(back_populates="queries")
    feedbacks: List["Feedback"] = Relationship(back_populates="query")
