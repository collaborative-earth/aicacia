import logging
from typing import Sequence

from core.db_manager import session_scope
from data_ingestion.parsing.parsers.abstract_parser import AbstractParser, BaseFileDocument
from core.fs_manager import fs_manager
from data_ingestion.types.current_status_enum import CurrentStatusEnum
from db.models.sourced_documents import TextualRepresentation
from db.repositories.sourced_document_repo import SourcedDocumentRepository


logger = logging.getLogger(__name__)


class ParsingHandler():
    def __init__(self, default_parser: AbstractParser) -> None:
        # assert fs is not None, "A filesystem instance must be provided."

        self.default_parser: AbstractParser = default_parser

    def parse_filepaths(self, filepaths: list[str]) -> Sequence[BaseFileDocument]:
        '''Parse files from given filepaths using the default parser.'''
        parsed_files: Sequence[BaseFileDocument] = (
            self.default_parser.parse_files(filepaths)
        )

        logger.info(
            f"Parsed {len(parsed_files)} out of {len(filepaths)} successfully."
        )

        return parsed_files

    def parse_and_upload(self, filepaths: list[str], dest_dir: str) -> list[str]:  # TODO: IMPROVE
        '''Parse files from given filepaths and upload parsed results to destination directory.'''

        parsed_files: Sequence[BaseFileDocument] = self.parse_filepaths(filepaths)

        uploaded_filepaths: list[str] = []
        if parsed_files:
            self.sourcedocument_repo = SourcedDocumentRepository()

            with session_scope() as session:
                for parsed_file in parsed_files:
                    try:
                        logger.info(f"Source filepath in metadata: {parsed_file.metadata}")
                        if parsed_file.metadata.get("source_filepath") is not None:
                            original_file_path = parsed_file.metadata.get("source_filepath")
                            # Update the status in DB
                            document = self.sourcedocument_repo.get_document_by_s3_path(
                                session=session,
                                s3_path=original_file_path              # TODO: CREATE TYPED dict for metadata
                            )

                            if document:
                                document.current_status = CurrentStatusEnum.TEXT_PARSED.value

                                uploaded_filepath = fs_manager.upload_filepath(
                                    local_filepath=parsed_file.filepath,
                                    dest_dir=dest_dir
                                )
                                document.textual_representation = TextualRepresentation(
                                    doc_id=document.doc_id,
                                    file_path=uploaded_filepath,
                                    parser=parsed_file.metadata.get("parser") # TODO: CREATE TYPED dict for metadata
                                )
                                session.add(document)
                                session.commit()
                    except Exception as e:
                        logger.error(
                            f"Error while updating parsed file for {parsed_file.filepath}: {e}"
                        )
                        session.rollback()

        return uploaded_filepaths
