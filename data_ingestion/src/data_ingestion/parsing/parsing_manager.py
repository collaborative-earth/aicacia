import logging
from functools import wraps
import time
from typing import Sequence
from pathlib import Path
from db.db_manager import session_scope
from data_ingestion.parsing.parsers.abstract_parser import AbstractParser, BaseFileDocument
from core.fs_manager import fs_manager
from data_ingestion.parsing.types import ParseFileErrorInfo, ParseFileInfo
from data_ingestion.custom_types.current_status_enum import CurrentStatusEnum
from db.models.sourced_documents import DataPipelineErrorLog, TextualRepresentation
from db.repositories.parsing_error_log_repo import DataPipelineErrorLogRepository
from db.repositories.textual_representation_repo import TextualRepresentationRepository
from db.repositories.sourced_document_repo import SourcedDocumentRepository
from data_ingestion.parsing.temp_dir_handler import tmp_dir_context


logger = logging.getLogger(__name__)


def cleanup_tmp_dir_after_call(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        finally:
            # Cleanup the temporary directory after the function call.
            tmp_dir_context.teardown()
    return wrapper


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

        return parsed_files

    def _get_id_and_filepath_from_filepath(self, filepath: str) -> dict[str, str]:
        '''Get the ID from the filepath.'''
        return {
            'doc_id': Path(filepath).stem,
            'source_filepath': filepath
        }

    @cleanup_tmp_dir_after_call
    def parse_documents(
            self, dest_dir: str, dry_run: bool = False, batch_size: int = 100
    ) -> list[str]:
        '''Parse documents from the database with status NEW and upload parsed results to destination directory.'''

        start_time = time.time()
        # Get all ready to parse documents
        files_info: list[ParseFileInfo] = []
        with session_scope() as session:
            sourced_document_repo = SourcedDocumentRepository()
            parsed_sourced_documents = sourced_document_repo.get_ready_to_parse_files(session)
            files_info = [
                ParseFileInfo(doc_id=doc.doc_id, source_filepath=doc.s3_path)
                for doc in parsed_sourced_documents
            ]

        if not files_info:
            logger.info("No documents to parse.")
            return []

        logger.info(f"Found {len(files_info)} documents to parse.")

        updated_document_ids: list[str] = []
        all_err_parsed_files: Sequence[ParseFileErrorInfo] = []
        # Process files in batches
        logger.info(f"Processing files in batches of size: {batch_size} .")
        nb_of_batches = (len(files_info) + batch_size - 1) // batch_size
        for batch_no, batch in enumerate(range(0, len(files_info), batch_size)):
            logger.info(
                f"--- Processing batch: [ {batch_no + 1} of {nb_of_batches} ] ---"
                )
            batch_files_info: list[ParseFileInfo] = files_info[batch: batch + batch_size]

            # Parse files in the current batch
            logger.info(f"Starting parsing of {len(batch_files_info)} files.")
            parsed_files_outputs: Sequence[BaseFileDocument | ParseFileErrorInfo] = self.parse_files(batch_files_info)

            ok_parsed_files: Sequence[BaseFileDocument] = []
            err_parsed_files: Sequence[ParseFileErrorInfo] = []
            for parsed_file in parsed_files_outputs:
                if isinstance(parsed_file, ParseFileErrorInfo):
                    err_parsed_files.append(parsed_file)
                else:
                    ok_parsed_files.append(parsed_file)

            logger.info(f"Parsed {len(ok_parsed_files)}/{len(batch_files_info)} files successfully in batch {batch_no + 1} ({len(err_parsed_files)} failures).")

            if dry_run:
                logger.info("Dry run mode. Skipping upload.")
                continue
            else:
                logger.info(f"Uploading parsed files to destination directory ({dest_dir}).")

            # Upload parsed_files to destination directory. (uploaded_filepaths order corresponds to ok_parsed_files order)
            uploaded_filepath = fs_manager.upload_filepaths_in_parallel(
                local_filepaths=[parsed_file.filepath for parsed_file in ok_parsed_files],
                dest_dir=dest_dir  # TODO: consider that maybe multiple corpora are parsed at the same time. pass array or 1 string?
            )

            # log number of successful uploads for the batch
            nb_ok_uploads = sum(fp is not None for fp in uploaded_filepath)
            nb_err_uploads = len(ok_parsed_files) - nb_ok_uploads
            logger.info(f"Successfully uploaded {nb_ok_uploads}/{len(ok_parsed_files)} files in batch {batch_no + 1} ({nb_err_uploads} failed uploads).")

            # Update the DB's sourced_documents with their new textual_representation info
            doc_id_to_textual_representation: dict[str, dict] = {}

            for i, uploaded_filepath in enumerate(uploaded_filepath):
                # None means upload failed for that file and uploaded_filepaths[i] corresponds to parsed_files[i].
                if uploaded_filepath is not None:
                    # Add to the dict only if upload was successful
                    doc_id_to_textual_representation[ok_parsed_files[i].metadata['doc_id']] = {
                        TextualRepresentation.doc_id: ok_parsed_files[i].metadata['doc_id'],
                        TextualRepresentation.file_path: uploaded_filepath,
                        TextualRepresentation.parser: ok_parsed_files[i].metadata['parser']
                    }
                else:
                    # Add to the existing parsing errors if upload failed
                    err_parsed_files.append(ParseFileErrorInfo(
                        doc_id=ok_parsed_files[i].metadata['doc_id'],
                        source_filepath=ok_parsed_files[i].metadata['source_filepath'],
                        error_msg="Upload of parsed file failed.",
                        parser=ok_parsed_files[i].metadata['parser']
                    ))

            textual_representation_repo = TextualRepresentationRepository()
            source_document_repo = SourcedDocumentRepository()
            parsing_error_repo = DataPipelineErrorLogRepository()
            with session_scope() as session:
                # Updating successfully parsed documents' textual representations and statuses in batch
                logger.info(
                    f"Creating textual representations for {len(doc_id_to_textual_representation)} documents and updating their statuses to {CurrentStatusEnum.TEXT_PARSED.value}."
                )
                source_document_repo.bulk_update_status_by_doc_ids(
                    session=session,
                    doc_ids=list(doc_id_to_textual_representation.keys()),
                    new_status=CurrentStatusEnum.TEXT_PARSED.value
                )
                textual_representation_repo.bulk_create(
                    session=session,
                    textual_representations=list(doc_id_to_textual_representation.values())
                )

                if len(err_parsed_files):
                    logger.info(
                        f"Creating parsing error logs for {len(err_parsed_files)} documents and updating their statuses to {CurrentStatusEnum.PARSING_ERROR.value}."
                    )
                    source_document_repo.bulk_update_status_by_doc_ids(
                        session=session,
                        doc_ids=[err_file.doc_id for err_file in err_parsed_files],
                        new_status=CurrentStatusEnum.PARSING_ERROR.value
                    )
                    parsing_error_repo.bulk_create(
                        session=session,
                        logs=[
                            {
                                DataPipelineErrorLog.doc_id: err_file.doc_id,
                                DataPipelineErrorLog.error_msg: err_file.error_msg,
                                DataPipelineErrorLog.parser: err_file.parser,
                                DataPipelineErrorLog.doc_err_status: CurrentStatusEnum.PARSING_ERROR.value,
                            }
                            for err_file in err_parsed_files
                        ]
                    )

                session.commit()

            updated_document_ids.extend(doc_id_to_textual_representation.keys())
            all_err_parsed_files.extend(err_parsed_files)
            logger.info(
                f"Finished processing batch: [ {batch_no + 1} of {nb_of_batches} ]."
            )

        total_time = time.time() - start_time
        logger.info(f"Completed parsing all documents ({len(files_info)}) in {total_time:.2f} seconds ({nb_of_batches} batches).")
        logger.info(f"Number of documents that were parsed successfully: {len(updated_document_ids)} ({len(all_err_parsed_files)} failed).")
        if len(all_err_parsed_files):
            logger.info("Parsing finished with the following errors:")
            for err_file in all_err_parsed_files:
                logger.info(
                    "\n------------------------------------------------------------\n"
                    "------------------------------------------------------------\n"
                    f"Document ID: {err_file.doc_id}\n"
                    f"Source Filepath: {err_file.source_filepath}\n"
                    f"Error message:\n{err_file.error_msg}\n"
                    "------------------------------------------------------------\n"
                )

        return updated_document_ids
