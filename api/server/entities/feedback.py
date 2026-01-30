from typing import Optional, Union

from pydantic import BaseModel


class ReferenceFeedback(BaseModel):
    feedback: int
    feedback_reason: str


class FeedbackDetails(BaseModel):
    references_feedback: list[ReferenceFeedback]
    feedback: str
    summary_feedback: int


class ConfigurationFeedbackValue(BaseModel):
    """Single feedback value for a configuration field"""

    field_id: str
    value: Union[int, str]


class ExperimentFeedbackDetails(BaseModel):
    """Stored in feedback_json.experiment_feedback"""

    configuration_feedbacks: dict[str, list[ConfigurationFeedbackValue]]
    # Key: configuration_id, Value: list of field responses


class CombinedFeedbackDetails(BaseModel):
    """Combined structure supporting both legacy and experiment feedback"""

    # Legacy fields (optional for backward compatibility)
    references_feedback: Optional[list[ReferenceFeedback]] = None
    feedback: Optional[str] = None
    summary_feedback: Optional[int] = None
    # New experiment feedback (optional)
    experiment_feedback: Optional[ExperimentFeedbackDetails] = None
