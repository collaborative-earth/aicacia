from typing import Type, Optional, Any, Dict, List
from pathlib import Path
import fsspec
from llama_index.core.readers.base import BaseReader
from llama_index.core.schema import Document

from data_ingestion.parsing.document_loaders import BaseFileDocument


# TODO: make it generic!
class LlamaReaderWrapper(BaseReader):
    def __init__(self, file_loader_cls: Type[BaseFileDocument]) -> None:
        super().__init__()
        self.file_loader_cls: Type[BaseFileDocument] = file_loader_cls

    def load_data(
            self,
            input_file: Path,
            extra_info: Optional[Dict[str, Any]] = None,
            fs: Optional[object] = None,
            **kwargs: Any
    ) -> List[Document]:
        """Uses a FileLoader to return the appropiate list of Documents.
        This method matches the expectations of `SimpleDirectoryReader.load_file`.
        """
        print(f"Loading data from file: {input_file}")

        # open file either using provided fs (fsspec) or local open
        if fs is None:
            fs = fsspec.filesystem('file')  # TODO: get filesystem from path

        # DocumentLoader from filepath
        file_document_loader = self.file_loader_cls.from_filepath(
            filepath=str(input_file),
            fs=fs,
            **kwargs
        )

        # from the DocumentLoader.. get textual representation and metadata
        combined_text = file_document_loader.get_textual_repr()
        metadata = file_document_loader.get_metadata() or {}

        if extra_info:
            # keep extra_info under its own key to avoid clobbering
            metadata["file_info"] = extra_info

        # combined document
        document = Document(text=combined_text, metadata=metadata)

        return [document]
