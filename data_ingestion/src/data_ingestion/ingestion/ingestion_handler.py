import logging
from typing import Sequence

import fsspec
from llama_index.core.readers import SimpleDirectoryReader
from llama_index.core.schema import Document
from data_ingestion.parsing.document_loaders.tei_file_document import TEIFileDocument
from data_ingestion.custom_types.llama_reader_wrapper import LlamaReaderWrapper


logger = logging.getLogger(__name__)


class IngestionHandler():
    def __init__(self, source_fs: fsspec.AbstractFileSystem) -> None:
        self.source_fs: fsspec.AbstractFileSystem = source_fs

    def get_documents_from_files(self, filepaths: list[str]) -> Sequence[Document]:
        '''Ingest files from given filepaths into the LlamaIndex pipeline and return Documents.'''

        # Removes protocol prefix for SimpleDirectoryReader(fails otherwise), fs argument handles it
        just_filepaths = [fsspec.core.split_protocol(f)[1] for f in filepaths]  # 1 == path part
        directoryReader = SimpleDirectoryReader(
            input_files=just_filepaths,
            file_extractor={
                ".xml": LlamaReaderWrapper(TEIFileDocument)
            },
            required_exts=[".xml"],
            fs=self.source_fs
        )

        documents = directoryReader.load_data(show_progress=True)

        return documents

    def ingest_files(self, filepaths: list[str]) -> None:
        '''Ingest files from given filepaths into the LlamaIndex pipeline.'''

        documents = self.get_documents_from_files(filepaths)

        for doc in documents:
            logger.info(f"--- Document text: {doc.text} ---")
