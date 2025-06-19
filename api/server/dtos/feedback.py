from pydantic import BaseModel


class ReferenceFeedback(BaseModel):
    feedback: int
    feedback_reason: str


class FeedbackPostRequest(BaseModel):
    query_id: str
    references_feedback: list[ReferenceFeedback]
    summary_feedback: int
    feedback: str


class FeedbackPostResponse(BaseModel):
    pass


class ChatFeedbackPostRequest(BaseModel):
    thread_id: str
    message_id: str
    feedback_message: str
    feedback: int


class ChatFeedbackPostResponse(BaseModel):
    pass
