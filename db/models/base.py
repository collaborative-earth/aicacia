from datetime import datetime, timezone
from sqlmodel import Field, SQLModel


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
