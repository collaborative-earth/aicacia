import logging
from typing import Any, Optional
import fsspec
from fsspec import AbstractFileSystem


logger = logging.getLogger(__name__)


class BaseFileDocument:
    '''Base class for file document loaders/parsers.'''

    def __init__(
        self,
        content: Optional[str] = None,  # TODO: Load lazyly?
        filepath: str = ':memory:',
        metadata: Optional[dict] = None,
    ) -> None:
        self.filepath = filepath
        self.content = content
        self.metadata = metadata or {}

    def get_object(self) -> Any:
        # Subclasses may implement it if any specific object representation is available
        return self.content

    def get_textual_repr(self) -> str:
        # Subclasses may implement this method to return their own textual representation
        return self.content or ""

    def get_metadata(self) -> dict:
        # Subclasses may implement this method to return their own metadata
        return self.metadata

    @classmethod
    def from_filepath(
        cls, filepath: str, fs: Optional[AbstractFileSystem] = None, **kwargs: Any
    ) -> "BaseFileDocument":
        '''Method to instantiate a FileDocumentLoader from a filepath. 
        'utf-8' encoding using fsspec if not specified.'''

        encoding = kwargs.get('encoding', 'utf-8')
        if fs is None:
            fs: AbstractFileSystem = fsspec.filesystem('file')  # TODO: get filesystem from path

        logger.info(f"Loading file-document from filepath: {filepath}")
        with fs.open(filepath, 'r', encoding=encoding) as f:
            content = f.read()
        return cls(filepath=filepath, content=content)