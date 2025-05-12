from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from enum import Enum

class DocumentSourceCorpus(Enum):
    WRI = "wri"
    SER = "ser"

@dataclass
class SourceLink:
    link: str
    type: str

@dataclass
class SourcedDocumentMetadata:
    title: str
    source_corpus: DocumentSourceCorpus
    sourced_at: datetime
    source_links: list[SourceLink]
    authors: list[str] = field(default_factory=list)
    doi: str | None = None
    page_link: str | None = None
    abstract: str | None = None
    geo_location: str | None = None
    revision_date: datetime | None = None
    license: str | None = None
    tags: list[str] = field(default_factory=list)
    references: list[str] = field(default_factory=list)
    other_metadata: dict[str, Any] = field(default_factory=dict)