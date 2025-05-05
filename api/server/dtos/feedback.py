from pydantic import BaseModel


class FeedbackPostRequest(BaseModel):
    query_id: str
    references_feedback: list[int]
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