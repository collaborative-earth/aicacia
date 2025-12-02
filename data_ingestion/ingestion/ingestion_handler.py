from typing import Sequence, Optional

import fsspec
import fsspec.utils
from llama_index.core.readers import SimpleDirectoryReader
from llama_index.core.schema import Document
from core.db_manager import db_manager
from core.app_config import configs
from data_ingestion.parsing.doc_loaders.tei_doc_loader import TEIDocumentLoader
from data_ingestion.types.llama_reader_wrapper import LlamaReaderWrapper
from fsspec.implementations.local import LocalFileSystem


class IngestionHandler():
    def __init__(self, source_fs: fsspec.AbstractFileSystem) -> None:
        self.source_fs: fsspec.AbstractFileSystem = source_fs

    def get_documents_from_filepaths(self, filepaths: list[str]) -> Sequence[Document]:
        '''Ingest files from given filepaths into the LlamaIndex pipeline and return Documents.'''

        print(f"Getting documents from filepaths: {filepaths}")

        directoryReader = SimpleDirectoryReader(
            input_files=filepaths,
            file_extractor={
                ".xml": LlamaReaderWrapper(TEIDocumentLoader)
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


if __name__ == '__main__':
    print("In IngestionHandler main!")

    # Configure parameters
    local_folder: str = configs.TMP_LOCAL_FOLDER
    source_fs = fsspec.filesystem(configs.SOURCE_FILESYSTEM)  # 's3' or 'file' for local filesystem

    ingestion_handler = IngestionHandler(source_fs=source_fs)

    filepaths = [
        filepath.removeprefix("s3://")  # TODO: ensure proper path handling
        for filepath in db_manager.get_ready_to_ingest_files()
    ]

    documents = ingestion_handler.get_documents_from_filepaths(filepaths)

    for doc in documents:
        print(f"--- Document length: {len(doc.text)} and metadata: {doc.metadata} ---")
