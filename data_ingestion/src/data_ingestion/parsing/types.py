from dataclasses import dataclass


@dataclass(frozen=True)
class ParseFileInfo:  # TODO: Maybe just call it FileInfo?
    doc_id: str  # unique identifier for the document
    source_filepath: str  # filepath of the source document used to generate this doc representation