import logging
from typing import Sequence
from pathlib import Path
from core.fs_manager import fs_manager
from data_ingestion.parsing.document_loaders.tei_file_document import TEIFileDocument
from data_ingestion.parsing.parsers.abstract_parser import AbstractParser
from grobid_client.grobid_client import GrobidClient

from core.app_config import configs


logger = logging.getLogger(__name__)


class GrobidParser(AbstractParser):

    TMP_LOCAL_FOLDER = configs.TMP_LOCAL_FOLDER

    PARSING_OPTIONS = {
        "n": 10,
        "generateIDs": False,
        "consolidate_header": False,
        "consolidate_header": False,
        "consolidate_citations": False,
        "include_raw_citations": False,
        "include_raw_affiliations": False,
        "tei_coordinates": False,
        "segment_sentences": False,
        "json_output": False,
        "markdown_output": False,
        "verbose": True
    }

    def __init__(self, host_url: str) -> None:
        super().__init__()
        self.grobid_client = GrobidClient(
            grobid_server=host_url,
        )

    def parse_files(
            self, filepaths: list[str]
    ) -> Sequence[TEIFileDocument]:
        """Parse multiple files using GROBID's batch processing.
        Args:
            filepaths: Sequence of file paths to parse.
        Returns:
            Sequence of GrobidTEIParsedFile instances.
        """

        # Grobid uses files downloaded locally before processing
        local_folder: str = configs.TMP_LOCAL_FOLDER
        downloaded_filepaths: list[str] = fs_manager.download_filepaths(filepaths, local_folder)

        # Create output directory to store GROBID results (TEI XML files)
        output_path = Path(self.TMP_LOCAL_FOLDER).joinpath("grobid_outputs")
        output_path.mkdir(parents=True, exist_ok=True)

        processed_count, error_count, skipped_count =\
            self.grobid_client.process_batch(
                "processFulltextDocument",
                input_path="",
                input_files=downloaded_filepaths,
                output=str(output_path),
                force=True,
                **self.PARSING_OPTIONS
            )
        logger.info(
            f"Processed: {processed_count}, Errors: {error_count}, Skipped: {skipped_count}"
        )

        OUTPUT_EXTENSION = "grobid.tei.xml"
        parsed_docs: Sequence[TEIFileDocument] = []

        for filepath in filepaths:
            parsed_path = output_path.joinpath(Path(filepath).stem + f".{OUTPUT_EXTENSION}")
            if parsed_path.exists():  # Check if the parsed file exists
                parsed_docs.append(
                    TEIFileDocument(
                        filepath=str(parsed_path),
                        metadata={
                            'source_filepath': str(filepath),
                            'parser': 'grobid_tei_parser'
                        }
                    )
                )
            else:
                logger.error(f"MISSING parsed file {parsed_path} for doc {filepath}.")

        return parsed_docs
