from datetime import datetime
from typing import Dict, Optional

from pydantic import BaseModel


class Reference(BaseModel):
    title: str
    url: str
    score: float
    chunk: str


class QueryRequest(BaseModel):
    question: str


class QueryResponse(BaseModel):
    query_id: str
    references: list[Reference]
    summary: str


class QueryListItem(BaseModel):
    query_id: str
    question: str
    created_at: datetime
    summary: str


class QueryListResponse(BaseModel):
    queries: list[QueryListItem]
    total_count: int


class QueryWithFeedbackResponse(BaseModel):
    query_id: str
    question: str
    references: list[Reference]
    summary: str
    feedback: Optional[Dict]
