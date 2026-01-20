from dataclasses import dataclass


@dataclass(frozen=True)
class ParseFileInfo:
    doc_id: str  # unique identifier for the document
    source_filepath: str  # filepath of the source document used to generate this doc representation


@dataclass(frozen=True)
class ParseFileErrorInfo:
    doc_id: str
    source_filepath: str
    error_msg: str
    parser: str
