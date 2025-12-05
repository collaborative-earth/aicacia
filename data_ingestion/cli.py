
import fsspec
import logging

from core.app_config import configs
from core.db_manager import db_manager
from core.fs_manager import fs_manager
from data_ingestion.parsing.parsing_handler import ParsingHandler
from data_ingestion.ingestion.ingestion_handler import IngestionHandler
from data_ingestion.parsing.parsers.grobid_parser import GrobidParser


logger = logging.getLogger(__name__)


def test_parsing(dry_run: bool = True) -> None:
    # Configure parameters
    default_parser = GrobidParser(host_url=configs.GROBID_URL)
    # local_folder: str = configs.TMP_LOCAL_FOLDER
    dest_dir: str = configs.PARSED_OUTPUTS_FOLDER
    parsing_handler = ParsingHandler(default_parser=default_parser)
    filepaths = db_manager.get_ready_to_parse_files()

    if dry_run:
        # for parsing without uploading
        parsed_files = parsing_handler.parse_filepaths(filepaths)

        if parsed_files:
            fs_manager.upload_filepaths(
                local_filepaths=[parsed_file.filepath for parsed_file in parsed_files],
                dest_dir=dest_dir
            )
    else:
        # for parsing with uploading
        uploaded_paths = parsing_handler.parse_and_upload(filepaths, dest_dir=dest_dir) 

        for uploaded_path in uploaded_paths:
            logger.info(uploaded_path)


def test_ingestion(dry_run: bool = True) -> None:
    # Configure parameters
    source_fs = fsspec.filesystem(configs.SOURCE_FILESYSTEM)  # 's3' or 'file' for local filesystem

    ingestion_handler = IngestionHandler(source_fs=source_fs)

    filepaths = db_manager.get_ready_to_ingest_files()

    documents = ingestion_handler.get_documents_from_files(filepaths)

    for doc in documents:
        logger.info(f"--- Document length: {len(doc.text)} and metadata: {doc.metadata} ---")


# test_db_connection, test_s3_connection ?


# TODO: Create CLI.. WIP
if __name__ == "__main__":
    logger.info("In the CLI!")
    test_parsing(dry_run=False)  # dry-run should get you till parsing, but no uploads
    # test_ingestion(dry_run=True)  # dry-run should get you till the nodes, but no side-effects
