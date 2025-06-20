from pydantic import BaseModel


class ReferenceFeedback(BaseModel):
    feedback: int
    feedback_reason: str


class FeedbackDetails(BaseModel):
    references_feedback: list[ReferenceFeedback]
    feedback: str
    summary_feedback: int
