import json
import uuid

from typing import Sequence
from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from qdrant_client import QdrantClient
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from server.auth.dependencies import get_current_user
from server.dtos.query import QueryRequest, QueryResponse, Reference
from server.db.models.query import Query
from server.db.models.user import User
from server.db.models.sourced_documents import SourcedDocument
from server.core.config import settings
from server.db.session import get_db_session
from server.core.ai_summary import generate_summary

query_router = APIRouter()

vectordb_client = QdrantClient(
    url=settings.QDRANT_URL,
    https=True,
    api_key=settings.QDRANT_API_KEY
)

embedding_model = HuggingFaceEmbedding(model_name=settings.EMBEDDING_MODEL_NAME)


@query_router.post("/")
def run_user_query(
        request: QueryRequest,
        user: User = Depends(get_current_user),
        db: Session = Depends(get_db_session)
) -> QueryResponse:

    query_id = str(uuid.uuid4())

    # Embed query
    query_embedding = embedding_model.get_text_embedding(request.question)

    # Search in vector store
    vectordb_results = vectordb_client.query_points(
        collection_name=settings.QDRANT_COLLECTION,
        query=query_embedding,
        with_payload=["_node_content", "doc_id"],
        limit=3
    )

    if not vectordb_results.points:
        query = Query(
            query_id=query_id,
            question=request.question,
            references=[],
            summary="No results found!",
            user_id=user.user_id
        )
    else:
        # Retrieve docs metadata
        doc_ids = list({p.payload["doc_id"] for p in vectordb_results.points})
        docs: Sequence[SourcedDocument] = db.exec(
            select(SourcedDocument).where(SourcedDocument.doc_id.in_(doc_ids))).all()

        references = []
        rag_context = []

        for point in vectordb_results.points:
            point_doc_id = uuid.UUID(point.payload["doc_id"])
            doc = next((d for d in docs if d.doc_id == point_doc_id), None)
            title = doc.title if doc else "Unknown"
            url = doc.page_link if doc else "Unknown"
            text = json.loads(point.payload["_node_content"])["text"]

            rag_context.append({"title": title, "url": url, "text": text})
            references.append(Reference(title=title, url=url, score=point.score, chunk=text).model_dump())

        summary = generate_summary(request.question, json.dumps(rag_context))

        query = Query(
            query_id=query_id,
            question=request.question,
            references=references,
            summary=summary,
            user_id=user.user_id,
        )

    db.add(query)
    db.commit()

    return QueryResponse(query_id=query_id, references=query.references, summary=query.summary)
