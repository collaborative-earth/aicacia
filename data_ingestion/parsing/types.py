from typing import Optional, Sequence


class ParsedFile:

    def __init__(
        self,
        bytes: Optional[bytes] = None,
        filepath: str = '::mem::',
        metadata: Optional[dict] = None,
    ) -> None:
        self.filepath = filepath
        self.bytes = bytes
        self.metadata = metadata or {}

    def get_file_repr(self) -> str:
        raise NotImplementedError("Subclasses must implement get_file_serialization method")

    def get_formatted_content(self) -> str:
        raise NotImplementedError("Subclasses must implement get_content method")


class AbstractParser:
    def parse_files(self, filepaths: list[str]) -> Sequence[ParsedFile]:
        raise NotImplementedError("Subclasses must implement parse_files method")

    # # abstracts
    # def parse(self, filepath: str) -> ParsedFile:
    #     raise NotImplementedError("Subclasses must implement parse_file method")
    # def parse_bytes(self, file_bytes: bytes) -> ParsedFile:
    #     raise NotImplementedError("Subclasses must implement parse_bytes method")


class TextParsedFile(ParsedFile):
    @classmethod
    def from_file(cls, f: str) -> "TextParsedFile":
        return cls()
