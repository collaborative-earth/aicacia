from typing import Optional, Union

from pydantic import BaseModel


class FeedbackOption(BaseModel):
    """A single option in a radio button feedback field"""

    value: int  # 0, 1, 2, etc.
    label: str  # "Evidence Absence", "Contextual Misalignment", etc.


class FeedbackFieldConfig(BaseModel):
    """Configuration for a single feedback field"""

    field_id: str
    field_type: str  # "radio" | "text"
    label: str  # Question text
    required: bool = True
    options: Optional[list[FeedbackOption]] = None  # For radio type


class ExperimentFeedbackConfig(BaseModel):
    """Feedback configuration stored at experiment level"""

    fields: list[FeedbackFieldConfig]


class ConfigurationFeedbackEntry(BaseModel):
    """A single feedback value for a configuration"""

    configuration_id: str
    field_id: str
    value: Union[int, str]  # Radio value or text


class ExperimentFeedbackPostRequest(BaseModel):
    """Request to submit experiment feedback"""

    query_id: str
    feedbacks: list[ConfigurationFeedbackEntry]


class ExperimentFeedbackPostResponse(BaseModel):
    """Response after submitting feedback"""

    feedback_id: str
