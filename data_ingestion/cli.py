import fsspec
import logging
from datetime import datetime

from core.app_config import configs
from core.db_manager import session_scope
from core.fs_manager import fs_manager
from data_ingestion.parsing.parsing_handler import ParsingHandler
from data_ingestion.ingestion.ingestion_handler import IngestionHandler
from data_ingestion.parsing.parsers.grobid_parser import GrobidParser
from db.repositories.sourced_document_repo import SourcedDocumentRepository


logger = logging.getLogger(__name__)


def add_mock_data() -> None:

    from db.models.sourced_documents import SourcedDocument  # to avoid circular import
    from data_ingestion.types.current_status_enum import CurrentStatusEnum
    import uuid

    mock1 = SourcedDocument(
        title="Test Doc 1",
        doc_id=uuid.uuid4(),
        source_corpus="Test Corpus",
        sourced_at=datetime.now(),
        source_links=[],
        authors=["Author One", "Author Two"],
        doi="10.1234/mockdoi",
        page_link="http://example.com/page",
        abstract="This is a test document.",
        geo_location="Earth",
        revision_date=datetime.now(),
        license="CC-BY",
        tags=["test", "mock"],
        references=["ref1", "ref2"],
        other_metadata={"key": "value"},
        is_relevant=True,
        current_status=CurrentStatusEnum.DOWNLOADED.value,
        s3_path="s3://k-bckt/aer/04c6508e-7332-11f0-bc9a-0242ac1c000c.pdf"
    )

    mock2 = SourcedDocument(
        title="Test Doc 2",
        doc_id=uuid.uuid4(),
        source_corpus="Test Corpus",
        sourced_at=datetime.now(),
        source_links=[],
        authors=["Author One", "Author Two"],
        doi="10.12345/mockdoi",
        page_link="http://example.com/page2",
        abstract="This is a test document 2.",
        geo_location="Earth",
        revision_date=datetime.now(),
        license="CC-BY",
        tags=["test", "mock"],
        references=["ref1", "ref2"],
        other_metadata={"key": "value"},
        is_relevant=True,
        current_status=CurrentStatusEnum.DOWNLOADED.value,
        s3_path="s3://k-bckt/aer/04c6508e-7332-11f0-bc9a-0242ac1c000c_copy.pdf"
    )

    with session_scope() as session:
        session.add(mock1)
        session.add(mock2)
        session.commit()

    logger.info("Mock data added.")


def test_parsing(dry_run: bool = True) -> None:
    # Configure parameters
    default_parser = GrobidParser(host_url=configs.GROBID_URL)

    # local_folder: str = configs.TMP_LOCAL_FOLDER
    dest_dir: str = configs.PARSED_OUTPUTS_FOLDER
    parsing_handler = ParsingHandler(default_parser=default_parser)

    filepaths: list[str] = []
    with session_scope() as session:
        sourced_document_repo = SourcedDocumentRepository()
        sourced_documents = sourced_document_repo.get_ready_to_parse_files(session)
        filepaths: list[str] = [doc.s3_path for doc in sourced_documents if doc.s3_path is not None]

    if not filepaths:
        logger.info("No files ready to parse.")
        return

    logger.info(f"Found {len(filepaths)} files ready to parse.")
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


# def test_ingestion(dry_run: bool = True) -> None:
#     # Configure parameters
#     source_fs = fsspec.filesystem(configs.SOURCE_FILESYSTEM)  # 's3' or 'file' for local filesystem

#     ingestion_handler = IngestionHandler(source_fs=source_fs)

#     filepaths = db_manager.get_ready_to_ingest_files()

#     documents = ingestion_handler.get_documents_from_files(filepaths)

#     for doc in documents:
#         logger.info(f"--- Document length: {len(doc.text)} and metadata: {doc.metadata} ---")


# test_db_connection, test_s3_connection ?


# TODO: Create CLI.. WIP
if __name__ == "__main__":
    logger.info("In the CLI!")

    # add_mock_data()

    test_parsing(dry_run=False)  # dry-run should get you till parsing, but no uploads
    # test_ingestion(dry_run=True)  # dry-run should get you till the nodes, but no side-effects
    logger.info("Done!")


# "s3://k-bckt/aer/04c6508e-7332-11f0-bc9a-0242ac1c000c.pdf",
# "s3://k-bckt/aer/04c6508e-7332-11f0-bc9a-0242ac1c000c_copy.pdf"
