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
