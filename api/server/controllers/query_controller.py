import json
import uuid

from fastapi import APIRouter, Depends, HTTPException
from server.auth.dependencies import get_current_user
from server.controllers.user_controller import get_admin_user
from server.core.ai_summary import generate_summary
from server.core.rag_utils import get_rag_references_with_context
from server.db.models.feedback import Feedback
from server.db.models.query import Query
from server.db.models.user import User
from server.db.session import get_db_session
from server.dtos.query import (
    QueryListResponse,
    QueryRequest,
    QueryResponse,
    QueryWithFeedbackResponse,
)
from sqlalchemy import func
from sqlmodel import Session, select

query_router = APIRouter()

admin_query_router = APIRouter()


@query_router.post("/")
def run_user_query(
        request: QueryRequest,
        user: User = Depends(get_current_user),
        db: Session = Depends(get_db_session)
) -> QueryResponse:

    query_id = str(uuid.uuid4())

    # Get RAG references and context using shared utility
    rag_result = get_rag_references_with_context(request.question, db, limit=3)

    if not rag_result["references"]:
        query = Query(
            query_id=query_id,
            question=request.question,
            references=[],
            summary="No results found!",
            user_id=user.user_id
        )
    else:
        # Generate summary using rag_context
        summary = generate_summary(request.question, json.dumps(rag_result["rag_context"]))

        query = Query(
            query_id=query_id,
            question=request.question,
            references=rag_result["references"],
            summary=summary,
            user_id=user.user_id,
        )

    db.add(query)
    db.commit()

    return QueryResponse(query_id=query_id, references=query.references, summary=query.summary)


@query_router.get("/list")
def list_queries(
    skip: int = 0,
    limit: int = 10,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> QueryListResponse:
    # Get total count
    total_count = db.exec(
        select(func.count()).select_from(Query).where(Query.user_id == user.user_id)
    ).first()

    # Get paginated queries
    queries = db.exec(
        select(Query)
        .where(Query.user_id == user.user_id)
        .offset(skip)
        .limit(limit)
        .order_by(Query.created_at.desc())
    ).all()

    return QueryListResponse(
        queries=[
            {
                "query_id": str(q.query_id),  # Convert UUID to string
                "question": q.question,
                "created_at": q.created_at,
                "summary": q.summary,
            }
            for q in queries
        ],
        total_count=total_count,
    )


@query_router.get("/{query_id}")
def get_query_with_feedback(
    query_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> QueryWithFeedbackResponse:
    # Get query
    query = db.exec(
        select(Query)
        .where(Query.query_id == query_id)
        .where(Query.user_id == user.user_id)
    ).first()

    if not query:
        raise HTTPException(status_code=404, detail="Query not found")

    # Get feedback if exists
    feedback = db.exec(
        select(Feedback)
        .where(Feedback.query_id == query_id)
        .where(Feedback.user_id == user.user_id)
    ).first()

    return QueryWithFeedbackResponse(
        query_id=str(query.query_id),  # Convert UUID to string
        question=query.question,
        references=query.references,
        summary=query.summary,
        feedback=feedback.feedback_json if feedback else None,
    )


@admin_query_router.get("/users/{user_id}/queries")
def list_user_queries_admin(
    user_id: str,
    skip: int = 0,
    limit: int = 10,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db_session),
) -> QueryListResponse:
    """List queries for specific user - admin only"""
    # Get total count for the specific user
    total_count = db.exec(
        select(func.count()).select_from(Query).where(Query.user_id == user_id)
    ).first()

    # Get paginated queries for the specific user
    queries = db.exec(
        select(Query)
        .where(Query.user_id == user_id)
        .offset(skip)
        .limit(limit)
        .order_by(Query.created_at.desc())
    ).all()

    return QueryListResponse(
        queries=[
            {
                "query_id": str(q.query_id),
                "question": q.question,
                "created_at": q.created_at,
                "summary": q.summary,
            }
            for q in queries
        ],
        total_count=total_count,
    )


@admin_query_router.get("/users/{user_id}/queries/{query_id}")
def get_user_query_with_feedback_admin(
    user_id: str,
    query_id: str,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db_session),
) -> QueryWithFeedbackResponse:
    """Get specific query with feedback for specific user - admin only"""
    # Get query for the specific user
    query = db.exec(
        select(Query).where(Query.query_id == query_id).where(Query.user_id == user_id)
    ).first()

    if not query:
        raise HTTPException(status_code=404, detail="Query not found")

    # Get feedback if exists for this user and query
    feedback = db.exec(
        select(Feedback)
        .where(Feedback.query_id == query_id)
        .where(Feedback.user_id == user_id)
    ).first()

    return QueryWithFeedbackResponse(
        query_id=str(query.query_id),
        question=query.question,
        references=query.references,
        summary=query.summary,
        feedback=feedback.feedback_json if feedback else None,
    )
