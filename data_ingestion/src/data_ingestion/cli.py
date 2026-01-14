import logging

from core.app_config import configs
from data_ingestion.parsing.document_loaders import BaseFileDocument
from data_ingestion.parsing.parsing_manager import ParsingManager
from data_ingestion.ingestion.ingestion_handler import IngestionHandler
from data_ingestion.parsing.parsers.grobid_parser import GrobidParser


logger = logging.getLogger(__name__)


def test_parsing(dry_run: bool = True, filepaths: list[str] = []) -> None:
    # Configure parameters
    default_parser = GrobidParser(host_url=configs.GROBID_URL)

    dest_dir: str = configs.PARSED_OUTPUTS_FOLDER
    parsing_manager = ParsingManager(default_parser=default_parser)

    if not filepaths:
        logger.info("No files ready to parse.")
        return

    logger.info(f"Found {len(filepaths)} files ready to parse.")

    # Parse files
    parsed_files = parsing_manager.parse_files(filepaths)
    for parsed_file in parsed_files:
        logger.info(f"Parsed file: {parsed_file.metadata.get('source_filepath', '')} - {parsed_file.filepath}")


def test_document_parsing(dry_run) -> None:
    # Configure parameters
    default_parser = GrobidParser(host_url=configs.GROBID_URL)

    dest_dir: str = configs.PARSED_OUTPUTS_FOLDER
    parsing_manager = ParsingManager(default_parser=default_parser)

    bucket_folder_name = "hj_andrews_bibliography_parsed"   # TODO: make this a parameter
    parsed_documents: list[str] = parsing_manager.parse_documents(
        dest_dir=dest_dir, 
        dry_run=dry_run,
        batch_size=100
    )
    for parsed_document in parsed_documents:
        logger.info(f"Parsed document: {parsed_document}")


def main():
    logger.info("In the CLI!")

    # test_parsing(dry_run=True)  # dry-run should get you till parsing, but no uploads
    test_document_parsing(dry_run=True)  # dry-run should get you till parsing, but no uploads
    # test_ingestion(dry_run=True)  # dry-run should get you till the nodes, but no side-effects
    logger.info("Done!")


# TODO: Create CLI.. WIP
if __name__ == "__main__":
    main()

