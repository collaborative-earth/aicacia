from typing import Optional

from pydantic import BaseModel

from server.dtos.query import Reference


class ExperimentConfiguration(BaseModel):
    """Configuration schema that matches the JSON stored in experiments.configurations"""

    configuration_id: str
    name: str
    llm_model: Optional[str] = None  # None = no LLM, just RAG
    embedding_model: str
    collection_name: str
    temperature: float = 0.5
    limit: int = 3


class ConfigurationResponse(BaseModel):
    """Response from running a single configuration"""

    configuration_id: str
    references: list[Reference]  # Empty if no vectordb results
    summary: Optional[str] = None  # None if no LLM configured


class ExperimentQueryResponse(BaseModel):
    """Response from running a query against an experiment"""

    query_id: str
    experiment_id: str
    responses: list[ConfigurationResponse]  # Randomized order
