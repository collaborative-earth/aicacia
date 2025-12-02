from typing import Sequence

import fsspec
from llama_index.core.readers import SimpleDirectoryReader
from llama_index.core.schema import Document
from data_ingestion.parsing.document_loaders.tei_file_document import TEIFileDocument
from data_ingestion.types.llama_reader_wrapper import LlamaReaderWrapper


class IngestionHandler():
    def __init__(self, source_fs: fsspec.AbstractFileSystem) -> None:
        self.source_fs: fsspec.AbstractFileSystem = source_fs

    def get_documents_from_filepaths(self, filepaths: list[str]) -> Sequence[Document]:
        '''Ingest files from given filepaths into the LlamaIndex pipeline and return Documents.'''

        print(f"Getting documents from filepaths: {filepaths}")

        directoryReader = SimpleDirectoryReader(
            input_files=filepaths,
            file_extractor={
                ".xml": LlamaReaderWrapper(TEIFileDocument)
            },
            fs=self.source_fs
        )

        documents = directoryReader.load_data(show_progress=True)

        return documents

    def ingest_filepaths(self, filepaths: list[str]) -> None:
        '''Ingest files from given filepaths into the LlamaIndex pipeline.'''

        documents = self.get_documents_from_filepaths(filepaths)

        for doc in documents:
            print(f"--- Document text: {doc.text} ---")
