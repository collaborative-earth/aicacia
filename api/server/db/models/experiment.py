import uuid
from typing import Optional

from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field

from server.db.models.base import Base


class Experiment(Base, table=True):
    __tablename__ = "experiments"

    experiment_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(unique=True, index=True)
    description: Optional[str] = Field(default=None)
    is_active: bool = Field(default=False)
    configurations: list[dict] = Field(default_factory=list, sa_column=Column(JSONB))
    feedback_config: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
