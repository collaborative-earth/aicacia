from typing import Sequence

from data_ingestion.parsing.document_loaders import BaseFileDocument


# TODO: Make is a Protocol?
class AbstractParser:
    def parse_files(self, filepaths: list[str]) -> Sequence[BaseFileDocument]:
        raise NotImplementedError("Subclasses must implement parse_files method")
