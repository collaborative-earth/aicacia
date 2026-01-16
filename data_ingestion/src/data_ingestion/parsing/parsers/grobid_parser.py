import logging
import time
from typing import Sequence
from pathlib import Path
from core.fs_manager import fs_manager
from data_ingestion.parsing.document_loaders.tei_file_document import TEIFileDocument
from data_ingestion.parsing.parsers.abstract_parser import AbstractParser
from grobid_client.grobid_client import GrobidClient

from data_ingestion.parsing.types import ParseFileInfo
from data_ingestion.parsing.temp_dir_handler import tmp_dir_context


logger = logging.getLogger(__name__)


class GrobidParser(AbstractParser):

    PARSING_OPTIONS = {
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

    def __init__(
            self, host_url: str, nb_workers: int = 10, timeout: int = 300, verbose: bool = False
    ) -> None:
        super().__init__()
        self.grobid_client = GrobidClient(
            grobid_server=host_url,
            timeout=timeout,
            verbose=verbose
        )
        self.tmp_dir_path = tmp_dir_context.path
        self.nb_workers = nb_workers

        logger.info(f"GROBID server: {host_url}.")
        logger.info(f"GROBID number of workers: {nb_workers}")
        logger.info(f"GROBID timeout: {timeout}s")
        logger.info(f"GROBID verbose: {verbose}")

    def parse_files(
            self, files_info: list[ParseFileInfo]
    ) -> Sequence[TEIFileDocument]:
        """Parse multiple files using GROBID's batch processing.
        Args:
            filepaths: Sequence of file paths to parse.
        Returns:
            Sequence of GrobidTEIParsedFile instances.
        """

        # Grobid uses files downloaded locally before processing
        logger.info(f"Downloading {len(files_info)} files to the local file system.")
        temp_dir_str: str = str(self.tmp_dir_path)
        filepaths = [file.source_filepath for file in files_info]
        downloaded_filepaths: list[str] = fs_manager.download_filepaths(filepaths, temp_dir_str)

        # Create output directory to store GROBID results (TEI XML files)
        output_path = self.tmp_dir_path.joinpath("grobid_outputs")

        try:
            output_path.mkdir(parents=True, exist_ok=False)
        except FileExistsError:
            logger.warning(f"Output directory {output_path} already exists. Could indicate there was an issue with previous run/cleanup.")
            logger.info("Deleting it and creating a new one.")
            output_path.rmdir()
            output_path.mkdir(parents=True, exist_ok=False)

        logger.info(f"Sending {len(downloaded_filepaths)} files to GROBID for parsing...")
        start = time.perf_counter()
        processed_count, error_count, skipped_count =\
            self.grobid_client.process_batch(
                "processFulltextDocument",
                input_path=temp_dir_str,
                input_files=downloaded_filepaths,
                output=str(output_path),
                force=True,
                n=self.nb_workers,
                **self.PARSING_OPTIONS
            )
        elapsed = time.perf_counter() - start
        logger.info(
            f"GROBID parser parsed: {processed_count}, Errors: {error_count}, Skipped: {skipped_count} in {elapsed:.2f}s"
        )

        OUTPUT_EXTENSION = "grobid.tei.xml"
        outputs: Sequence[TEIFileDocument] = []

        for file_info in files_info:
            parsed_filename = Path(file_info.source_filepath).stem + f".{OUTPUT_EXTENSION}"
            parsed_path = output_path.joinpath(parsed_filename)
            if parsed_path.exists():  # Check if the parsed file exists
                outputs.append(
                    TEIFileDocument(
                        filepath=str(parsed_path),
                        metadata={
                            'doc_id': file_info.doc_id,
                            'source_filepath': str(file_info.source_filepath),
                            'parser': 'grobid_tei_parser',
                        }
                    )
                )
                logger.info(f"Successfully parsed file: {file_info.source_filepath}.")
            else:
                logger.error(f"ERROR parsing file: {file_info.source_filepath}. \nMissing parsed file: {parsed_path}.")

        return outputs
