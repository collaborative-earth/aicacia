import logging
from typing import Sequence

from core.db_manager import session_scope
from data_ingestion.parsing.parsers.abstract_parser import AbstractParser, BaseFileDocument
from core.fs_manager import fs_manager
from data_ingestion.types.current_status_enum import CurrentStatusEnum
from db.models.sourced_documents import SourcedDocument, TextualRepresentation
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

    def parse_and_upload(
            self, filepaths: list[str], dest_dir: str, batch_size: int = 100
    ) -> list[str]:
        '''Parse files from given filepaths and upload parsed results to destination directory.'''

        source_document_repo = SourcedDocumentRepository()
        all_uploaded_paths = []
        # Process files in batches
        for batch_no, batch in enumerate(range(0, len(filepaths), batch_size)):
            logger.info(f"Processing batch {batch_no + 1}...")
            batch_filepaths = filepaths[batch: batch + batch_size]

            # Parse files in the current batch
            logger.info(f"Parsing files for batch. {batch_no + 1}")
            parsed_files: Sequence[BaseFileDocument] = self.parse_filepaths(batch_filepaths)
            if not parsed_files:
                logger.warning(f"No files were successfully parsed in batch {batch_no + 1}.")

            parsed_filename_to_info = {
                parsed_file.filepath:
                {
                    'parsed_file': parsed_file,
                    'source_filepath': parsed_file.metadata['source_filepath'],
                    'uploaded_filepath': None
                }
                for parsed_file in parsed_files
                if "source_filepath" in parsed_file.metadata
            }

            # Get all parsed filespaths to upload
            parsed_paths_to_upload = list(parsed_filename_to_info.keys())
            uploaded_filepaths = fs_manager.upload_filepaths_in_parallel(
                local_filepaths=parsed_paths_to_upload,
                dest_dir=dest_dir
            )
            logger.info(f"Uploaded {len(uploaded_filepaths)} files in batch {batch_no + 1}.")

            for up_fp, parsed_fp in zip(uploaded_filepaths, parsed_paths_to_upload):
                parsed_filename_to_info[parsed_fp]['uploaded_filepath'] = up_fp
                all_uploaded_paths.append(up_fp)

            # Update the DB with the uploaded filepaths and statuses
            source_to_info_map = {
                parsed_file_info['source_filepath']: {
                    'up_fp': parsed_file_info['uploaded_filepath'],
                    'parser': parsed_file_info['parsed_file'].metadata.get("parser")
                }
                for parsed_file_info in parsed_filename_to_info.values()
                if parsed_file_info['uploaded_filepath'] is not None
                # uploaded_filepath will be None if its upload failed
            }

            with session_scope() as session:
                sourced_documents: Sequence[SourcedDocument] = \
                    source_document_repo.get_documents_by_filepaths(
                        session=session,
                        filepaths=list(source_to_info_map.keys())
                    )

                for doc in sourced_documents:
                    doc_updated_info = source_to_info_map[doc.s3_path]
                    doc.current_status = CurrentStatusEnum.TEXT_PARSED.value
                    doc.textual_representation = \
                        TextualRepresentation(
                            doc_id=doc.doc_id,
                            file_path=doc_updated_info['up_fp'],
                            parser=doc_updated_info['parser']
                        )
                session.commit()

                logger.info(
                    f"Updated {len(sourced_documents)}/{len(batch_filepaths)} in batch {batch_no + 1}"
                )

        return all_uploaded_paths
