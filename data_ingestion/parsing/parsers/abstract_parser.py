from typing import Sequence

from data_ingestion.parsing.doc_loaders import DocumentLoader


# TODO: Make is a Protocol?
class AbstractParser:
    def parse_files(self, filepaths: list[str]) -> Sequence[DocumentLoader]:
        raise NotImplementedError("Subclasses must implement parse_files method")