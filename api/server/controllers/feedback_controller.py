import uuid

from fastapi import HTTPException, APIRouter, Depends
from sqlalchemy import select
from sqlmodel import Session, select
from server.auth.dependencies import get_current_user
from server.db.models.feedback import Feedback
from server.db.models.query import Query
from server.db.models.user import User
from server.db.session import get_db_session
from server.dtos.feedback import FeedbackPostRequest, FeedbackPostResponse
from server.entities.feedback import FeedbackDetails

feedback_router = APIRouter()


@feedback_router.post("/")
def save_feedback(request: FeedbackPostRequest,
                  user: User = Depends(get_current_user),
                  db: Session = Depends(get_db_session)) -> FeedbackPostResponse:

    query = db.exec(select(Query).filter(Query.query_id == request.query_id)).first()

    if not query:
        raise HTTPException(status_code=400, detail="Query does not exist")

    if len(request.references_feedback) != len(query.references):
        raise HTTPException(
            status_code=400,
            detail="References feedback should have the same length as the references",
        )

    feedback_id = str(uuid.uuid4())

    feedback = Feedback(
        feedback_id=feedback_id,
        query_id=request.query_id,
        user_id=user.user_id,
        feedback_json=FeedbackDetails(
            references_feedback=request.references_feedback,
            feedback=request.feedback,
            summary_feedback=request.summary_feedback,
        ).model_dump(),
    )

    db.add(feedback)
    db.commit()

    return FeedbackPostResponse()
