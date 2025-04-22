import enum
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Any

from pydantic import BaseModel
from sqlalchemy import Column, ForeignKeyConstraint, PrimaryKeyConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import JSON, Field, LargeBinary, Relationship, SQLModel


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
    thread_messages: List["ThreadMessages"] = Relationship(back_populates="user")
    thread_message_feedback: List["ThreadMessageFeedback"] = Relationship(
        back_populates="user"
    )


class Reference(BaseModel):
    title: str
    url: str
    score: float
    chunk: str


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
    summary_feedback: int


class Feedback(Base, table=True):
    __tablename__ = "feedbacks"
    feedback_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    query_id: uuid.UUID = Field(foreign_key="queries.query_id", nullable=False)
    user_id: uuid.UUID = Field(foreign_key="users.user_id", nullable=False)
    # TODO: Figure out a way to enforce the structure of the json field.
    feedback_json: dict = Field(sa_column=Column(JSON))

    user: "User" = Relationship(back_populates="feedbacks")
    query: "Query" = Relationship(back_populates="feedbacks")


class Actor(enum.Enum):
    USER = "user"
    AGENT = "agent"


class ChatMessage(BaseModel):
    message: str
    message_from: Actor
    message_id: Optional[str] = None


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

class SourcedDocument(Base, table=True):
    __tablename__ = "sourced_documents"
    doc_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    title: str = Field(nullable=False)
    source_corpus: str = Field(nullable=False)
    sourced_at: datetime = Field()
    source_links: List["SourceLink"] = Relationship(back_populates="document")
    authors: list[str] = Field(default_factory=list, sa_column=Column(JSONB))
    doi: Optional[str] = Field()
    page_link: Optional[str] = Field()
    abstract: Optional[str] = Field()
    geo_location: Optional[str] = Field()
    revision_date: Optional[datetime] = Field()
    license: Optional[str] = Field()
    tags: list[str] = Field(default_factory=list, sa_column=Column(JSONB))
    references: list[str] = Field(default_factory=list, sa_column=Column(JSONB))
    other_metadata: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSONB))

class SourceLink(Base, table=True):
    __tablename__ = "source_links"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    doc_id: uuid.UUID = Field(foreign_key="sourced_documents.doc_id", nullable=False)
    link: str = Field(nullable=False)
    type: str = Field(nullable=False)
    document: "SourcedDocument" = Relationship(back_populates="source_links")


class Document(Base, table=True):
    __tablename__ = "documents"
    doc_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    title: str = Field(nullable=False)
    raw_content: Optional[bytes] = Field(sa_column=Column(LargeBinary))
    authors: list[str] = Field(sa_column=Column(JSON))
    doi: Optional[str] = Field()
    link: Optional[str] = Field()
    content_hash: Optional[int] = Field()
    corpus_name: Optional[str] = Field()
    sources: list[str] = Field(sa_column=Column(JSON))
    location: Optional[str] = Field()
    sourced_date: Optional[datetime] = Field()
    revision_date: Optional[datetime] = Field()
    references: list[str] = Field(sa_column=Column(JSON))
    generated_metadata: dict = Field(sa_column=Column(JSON))

    chunks: List["DocumentChunk"] = Relationship(back_populates="document")
    tags: List["DocumentTag"] = Relationship(back_populates="document")


class DocumentChunk(Base, table=True):
    __tablename__ = "document_chunks"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    doc_id: uuid.UUID = Field(foreign_key="documents.doc_id", nullable=False)
    sequence_number: Optional[int] = Field()
    content: bytes = Field(sa_column=Column(LargeBinary))
    media_type: str = Field(nullable=False)
    token_offset_position: Optional[int] = Field()
    generated_metadata: dict = Field(sa_column=Column(JSON))

    document: "Document" = Relationship(back_populates="chunks")


class DocumentTag(Base, table=True):
    __tablename__ = "document_tags"
    value: str = Field(primary_key=False, nullable=False)
    doc_id: uuid.UUID = Field(foreign_key="documents.doc_id", nullable=False)
    generated: bool = Field(primary_key=False, nullable=False)

    document: "Document" = Relationship(back_populates="tags")

    __table_args__ = (
        PrimaryKeyConstraint("doc_id", "value", "generated"),
    )


class ThreadMessageFeedbackJSON(BaseModel):
    feedback: int
    feedback_message: str


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
