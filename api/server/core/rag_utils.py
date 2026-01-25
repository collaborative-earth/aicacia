import json
import uuid
from typing import List, Sequence

from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from qdrant_client import QdrantClient
from server.core.config import settings
from server.db.models.sourced_documents import SourcedDocument
from server.dtos.query import Reference
from sqlmodel import Session, select

vectordb_client = QdrantClient(
    url=settings.QDRANT_URL,
    https=True,
    api_key=settings.QDRANT_API_KEY
)

embedding_model = HuggingFaceEmbedding(model_name=settings.EMBEDDING_MODEL_NAME)


def get_rag_references(message: str, db: Session, limit: int = 3) -> List[dict]:
    """
    Query the vector database for RAG references based on a message.
    
    Args:
        message: The message/query to search for
        db: Database session to fetch document metadata
        limit: Maximum number of references to return (default: 3)
    
    Returns:
        List of Reference dictionaries (as returned by Reference.model_dump())
    """
    result = get_rag_references_with_context(message, db, limit)
    return result["references"]


def get_rag_references_with_context(message: str, db: Session, limit: int = 3) -> dict:
    """
    Query the vector database for RAG references and context based on a message.
    
    Args:
        message: The message/query to search for
        db: Database session to fetch document metadata
        limit: Maximum number of references to return (default: 3)
    
    Returns:
        Dictionary with:
        - "references": List of Reference dictionaries (as returned by Reference.model_dump())
        - "rag_context": List of simplified context dicts with title, url, text (for summary generation)
    """
    # Embed query
    query_embedding = embedding_model.get_text_embedding(message)

    # Search in vector store
    vectordb_results = vectordb_client.query_points(
        collection_name=settings.QDRANT_COLLECTION,
        query=query_embedding,
        with_payload=["_node_content", "doc_id"],
        limit=limit
    )

    if not vectordb_results.points:
        return {"references": [], "rag_context": []}

    # Retrieve docs metadata
    doc_ids = list({p.payload["doc_id"] for p in vectordb_results.points})
    docs: Sequence[SourcedDocument] = db.exec(
        select(SourcedDocument).where(SourcedDocument.doc_id.in_(doc_ids))
    ).all()

    references = []
    rag_context = []
    duplicate_chunk_counter: dict[str, int] = {}

    for point in vectordb_results.points:
        point_doc_id = uuid.UUID(point.payload["doc_id"])
        doc = next((d for d in docs if d.doc_id == point_doc_id), None)
        title = doc.title if doc else "Unknown"
        url = doc.page_link if doc else "Unknown"
        doi = doc.doi if doc else "Unknown"

        if (not url or url == "Unknown") and doi and doi != "Unknown":
            url = f"https://doi.org/{doi}"

        # Ensure url is not None
        url = url or "Unknown"

        text = json.loads(point.payload["_node_content"])["text"]

        # Skip duplicate chunks
        if text in duplicate_chunk_counter:
            duplicate_chunk_counter[text] += 1
            continue
        else:
            duplicate_chunk_counter[text] = 1

        rag_context.append({"title": title, "url": url, "text": text})
        references.append(
            Reference(
                title=title, url=url, score=point.score, chunk=text
            ).model_dump()
        )

    for text, count in duplicate_chunk_counter.items():
        if count > 1:
            print(f"Duplicate chunk found: {text} with count: {count}")

    return {"references": references, "rag_context": rag_context}
