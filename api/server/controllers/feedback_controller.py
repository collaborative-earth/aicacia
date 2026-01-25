import uuid

from fastapi import APIRouter, Depends, HTTPException
from server.auth.dependencies import get_current_user
from server.db.models.feedback import Feedback
from server.db.models.query import Query
from server.db.models.user import User
from server.db.session import get_db_session
from server.dtos.feedback import FeedbackPostRequest, FeedbackPostResponse
from server.dtos.experiment_feedback import (
    ExperimentFeedbackPostRequest,
    ExperimentFeedbackPostResponse,
)
from server.entities.feedback import (
    ConfigurationFeedbackValue,
    ExperimentFeedbackDetails,
    FeedbackDetails,
)
from sqlmodel import Session, select

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
            references_feedback=[
                feedback.model_dump() for feedback in request.references_feedback
            ],
            feedback=request.feedback,
            summary_feedback=request.summary_feedback,
        ).model_dump(),
    )

    db.add(feedback)
    db.commit()

    return FeedbackPostResponse()


@feedback_router.post("/experiment")
def save_experiment_feedback(
    request: ExperimentFeedbackPostRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> ExperimentFeedbackPostResponse:
    """Save feedback for an experiment query (supports multiple configurations)"""

    query = db.exec(select(Query).filter(Query.query_id == request.query_id)).first()

    if not query:
        raise HTTPException(status_code=400, detail="Query does not exist")

    if not query.experiment_id:
        raise HTTPException(
            status_code=400, detail="Query is not associated with an experiment"
        )

    # Check for existing feedback for this query and user
    existing_feedback = db.exec(
        select(Feedback)
        .where(Feedback.query_id == request.query_id)
        .where(Feedback.user_id == user.user_id)
    ).first()

    # Transform feedbacks into configuration-keyed structure
    configuration_feedbacks: dict[str, list[dict]] = {}
    for entry in request.feedbacks:
        if entry.configuration_id not in configuration_feedbacks:
            configuration_feedbacks[entry.configuration_id] = []
        configuration_feedbacks[entry.configuration_id].append(
            ConfigurationFeedbackValue(
                field_id=entry.field_id,
                value=entry.value,
            ).model_dump()
        )

    experiment_feedback = ExperimentFeedbackDetails(
        configuration_feedbacks=configuration_feedbacks
    )

    if existing_feedback:
        # Update existing feedback with new experiment feedback
        feedback_json = existing_feedback.feedback_json or {}
        feedback_json["experiment_feedback"] = experiment_feedback.model_dump()
        existing_feedback.feedback_json = feedback_json
        db.add(existing_feedback)
        feedback_id = str(existing_feedback.feedback_id)
    else:
        # Create new feedback
        feedback_id = str(uuid.uuid4())
        feedback = Feedback(
            feedback_id=feedback_id,
            query_id=request.query_id,
            user_id=user.user_id,
            feedback_json={"experiment_feedback": experiment_feedback.model_dump()},
        )
        db.add(feedback)

    db.commit()

    return ExperimentFeedbackPostResponse(feedback_id=feedback_id)
