
from enum import Enum


class CurrentStatusEnum(str, Enum):
    NEW = "NEW"
    DOWNLOADED = "DOWNLOADED"
    TEXT_PARSED = "TEXT_PARSED"
    PARSING_ERROR = "PARSING_ERROR"
    INDEXED = "INDEXED"
