from typing import Any, Optional
import fsspec
from fsspec import AbstractFileSystem


# TODO: make abstract base class
class DocumentLoader:

    def __init__(
        self,
        content: Optional[str] = None,
        filepath: str = ':memory:',
        metadata: Optional[dict] = None,
    ) -> None:
        self.filepath = filepath
        self.content = content
        self.metadata = metadata or {}

    def get_object(self) -> Any:
        # Subclasses must implement it if an onject representation is available
        return self.content

    def get_textual_repr(self) -> str:
        raise NotImplementedError("Subclasses must implement get_content method")

    def get_metadata(self) -> dict:
        return self.metadata

    @classmethod
    def from_filepath(
        cls, filepath: str, fs: Optional[AbstractFileSystem] = None, **kwargs: Any
    ) -> "DocumentLoader":
        '''Method to instantiate a FileDocumentLoader from a filepath. 
        'utf-8' encoding using fsspec if not specified.'''

        encoding = kwargs.get('encoding', 'utf-8')
        if fs is None:
            fs: AbstractFileSystem = fsspec.filesystem('file')  # TODO: get filesystem from path

        print("Loading document from filepath:", filepath)
        with fs.open(filepath, 'r', encoding=encoding) as f:
            content = f.read()
        return cls(filepath=filepath, content=content)