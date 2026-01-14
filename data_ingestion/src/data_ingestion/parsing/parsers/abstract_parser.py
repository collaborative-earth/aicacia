from typing import Sequence

from data_ingestion.parsing.document_loaders import BaseFileDocument
from data_ingestion.parsing.types import ParseFileInfo


# TODO: Make is a Protocol?
class AbstractParser:
    def parse_files(self, files_info: list[ParseFileInfo]) -> Sequence[BaseFileDocument]:
        raise NotImplementedError("Subclasses must implement parse_files method")
