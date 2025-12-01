

from data_ingestion.parsing.types import AbstractParser, ParsedFile


class PyMuPDFParsedFile(ParsedFile):
    # TODO: Implement PyMuPDFParsedFile specific methods and attributes
    @classmethod
    def from_file(cls, f: str) -> "PyMuPDFParsedFile":
        return cls()


class PyMuPDFParser(AbstractParser):
    # TODO: Implement any necessary initialization parameters
    def parse(self, filepath: str) -> PyMuPDFParsedFile:
        # TODO: Implement PyMuPDF file parsing logic
        return PyMuPDFParsedFile()
