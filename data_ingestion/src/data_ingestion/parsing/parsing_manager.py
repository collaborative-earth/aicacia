import logging
from typing import Sequence
from pathlib import Path
from db.db_manager import session_scope
from data_ingestion.parsing.parsers.abstract_parser import AbstractParser, BaseFileDocument
from core.fs_manager import fs_manager
from data_ingestion.parsing.types import ParseFileInfo
from data_ingestion.custom_types.current_status_enum import CurrentStatusEnum
from db.models.sourced_documents import SourcedDocument, TextualRepresentation
from db.repositories.sourced_document_repo import SourcedDocumentRepository


logger = logging.getLogger(__name__)


class ParsingManager():
    def __init__(self, default_parser: AbstractParser) -> None:
        # assert fs is not None, "A filesystem instance must be provided."

        self.default_parser: AbstractParser = default_parser

    def parse_files(self, files: list[str] | list[ParseFileInfo]) -> Sequence[BaseFileDocument]:
        '''Parse files from given filepaths using the default parser.

        Args:
            files: list of filepaths or list of ParseFileInfo objects. 
            If list of filepaths, the doc_id will be the filename stem and the source_filepath will be the filepath.

        Returns:
            list of BaseFileDocument objects
        '''
        # if files is a list of strings, convert it to a list of ParseFileInfo
        if all(isinstance(fp, str) for fp in files):
            files = [ParseFileInfo(doc_id=Path(fp).stem, source_filepath=fp) for fp in files]
        elif all(isinstance(fp, ParseFileInfo) for fp in files):
            pass
        else:
            raise ValueError("filepaths must be a list of strings or a list of FileInfo objects")

        parsed_files: Sequence[BaseFileDocument] = (
            self.default_parser.parse_files(files)
        )

        logger.info(
            f"Parsed {len(parsed_files)} out of {len(files)} successfully."
        )

        return parsed_files

    def get_id_and_filepath_from_filepath(self, filepath: str) -> dict[str, str]:
        '''Get the ID from the filepath.'''
        return {
            'doc_id': Path(filepath).stem,
            'source_filepath': filepath
        }

    def parse_documents(
            self, dest_dir: str, dry_run: bool = False, batch_size: int = 100
    ) -> list[str]:
        '''Parse documents from the database with status NEW and upload parsed results to destination directory.'''

        # Get all ready to parse documents
        files_info: list[ParseFileInfo] = []
        with session_scope() as session:
            sourced_document_repo = SourcedDocumentRepository()
            parsed_sourced_documents = sourced_document_repo.get_ready_to_parse_files(session)
            files_info = [ParseFileInfo(doc_id=doc.doc_id, source_filepath=doc.s3_path) for doc in parsed_sourced_documents]

        if not files_info:
            logger.info("No documents to parse.")
            return []

        logger.info(f"Found {len(files_info)} documents to parse.")

        source_document_repo = SourcedDocumentRepository()
        updated_document_ids: list[str] = []

        # Process files in batches
        for batch_no, batch in enumerate(range(0, len(files_info), batch_size)):
            logger.info(f"Processing batch {batch_no + 1}...")
            batch_files_info: list[ParseFileInfo] = files_info[batch: batch + batch_size]

            # Parse files in the current batch
            logger.info(f"Parsing files for batch. {batch_no + 1}")
            parsed_files: Sequence[BaseFileDocument] = self.parse_files(batch_files_info)

            if not parsed_files:
                logger.warning(f"No files were successfully parsed in batch {batch_no + 1}.")
                continue
            else:
                logger.info(f"Successfully parsed {len(parsed_files)} files in batch {batch_no + 1}.")
                if dry_run:
                    logger.info("Dry run mode. Skipping upload.")
                    continue
                else:
                    logger.info("Uploading parsed files to destination directory.")

            # Upload parsed_files to destination directory
            uploaded_filepaths = fs_manager.upload_filepaths_in_parallel(
                local_filepaths=[parsed_file.filepath for parsed_file in parsed_files],
                dest_dir=dest_dir  # TODO: consider that maybe multiple corpora are parsed at the same time. pass array or 1 string?
            )

            # log number of successful uploads for the batch
            no_successful_uploads = sum(fp is not None for fp in uploaded_filepaths)
            logger.info(f"Successfully uploaded {no_successful_uploads}/{len(parsed_files)} files in batch {batch_no + 1}.")

            # Update the DB's sourced_documents with their new textual_representation
            doc_id_to_textual_representation: dict[str, TextualRepresentation] = {
                parsed_file.metadata['doc_id']: TextualRepresentation(
                    doc_id=parsed_file.metadata['doc_id'],
                    file_path=uploaded_filepaths[i],
                    parser=parsed_file.metadata['parser']
                )
                for i, parsed_file in enumerate(parsed_files)
                if uploaded_filepaths[i] is not None
            }
            # uploaded_filepaths[i] direclty maps to parsed_files[i]. None means upload failed for that file.

            with session_scope() as session:
                parsed_sourced_documents: Sequence[SourcedDocument] = \
                    source_document_repo.get_documents_by_doc_ids(
                        session=session,
                        doc_ids=doc_id_to_textual_representation.keys()
                    )

                for doc in parsed_sourced_documents:
                    doc.current_status = CurrentStatusEnum.TEXT_PARSED.value
                    doc.textual_representation = doc_id_to_textual_representation[doc.doc_id]
                session.commit()

            updated_document_ids.extend(doc_id_to_textual_representation.keys())
            logger.info(
                f"Updated {len(parsed_sourced_documents)}/{len(batch_files_info)} sourced_documents in batch {batch_no + 1}"
            )

        return updated_document_ids

