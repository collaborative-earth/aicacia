from pydantic import BaseModel


class ThreadMessageFeedbackDetails(BaseModel):
    feedback: int
    feedback_message: str
