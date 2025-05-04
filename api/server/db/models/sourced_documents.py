import uuid

from datetime import datetime
from typing import List, Optional, Any
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, Relationship
from server.db.models.base import Base


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
    is_relevant: bool = Field(default=False)


class SourceLink(Base, table=True):
    __tablename__ = "source_links"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    doc_id: uuid.UUID = Field(foreign_key="sourced_documents.doc_id", nullable=False)
    link: str = Field(nullable=False)
    type: str = Field(nullable=False)
    s3_location: Optional[str] = Field()
    document: "SourcedDocument" = Relationship(back_populates="source_links")
