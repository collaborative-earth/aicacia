from pydantic import BaseModel


class FeedbackDetails(BaseModel):
    references_feedback: list[int]
    feedback: str
    summary_feedback: int
