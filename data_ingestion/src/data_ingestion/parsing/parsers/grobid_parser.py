import logging
import time
from typing import Sequence
from pathlib import Path
import concurrent.futures
from core.fs_manager import fs_manager
from data_ingestion.parsing.document_loaders.tei_file_document import TEIFileDocument
from data_ingestion.parsing.parsers.abstract_parser import AbstractParser
from grobid_client.grobid_client import GrobidClient

from data_ingestion.parsing.types import ParseFileInfo, ParseFileErrorInfo
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
        "flavor": None,
        "start": -1,
        "end": -1
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
    ) -> Sequence[TEIFileDocument | ParseFileErrorInfo]:
        """Parse multiple files using GROBID's batch processing.
        Args:
            filepaths: Sequence of file paths to parse.
        Returns:
            Sequence of GrobidTEIParsedFile instances.
            Same order as input files.
        """

        batch_processing_output: dict[str, TEIFileDocument | ParseFileErrorInfo] =\
            self.process_batch(
                files_info=files_info,
                max_workers=self.nb_workers
            )

        sorted_outputs: list[TEIFileDocument | ParseFileErrorInfo] = []
        for file_info in files_info:
            sorted_outputs.append(batch_processing_output[file_info.doc_id])
        return sorted_outputs

    def process_batch(
            self, files_info: list[ParseFileInfo], max_workers: int = 10
    ) -> dict[str, TEIFileDocument | ParseFileErrorInfo]:
        ''' Modified from the original batch processing (GrobidClient.process_batch) to allow for better error handling '''
        batch_start_time = time.time()

        # Grobid uses files downloaded locally before processing
        logger.info(f"Downloading {len(files_info)} files to the local file system.")
        temp_dir_str: str = str(self.tmp_dir_path)
        filepaths = [file.source_filepath for file in files_info]
        downloaded_filepaths: list[str] = fs_manager.download_filepaths(filepaths, temp_dir_str)

        # Create output directory to store GROBID results (TEI XML files)
        output_path = self.tmp_dir_path.joinpath("grobid_outputs")
        output_path.mkdir(parents=True, exist_ok=True)

        processed_count = 0
        error_count = 0

        outputs: dict[str, TEIFileDocument | ParseFileErrorInfo] = {}
        logger.info(f"Sending {len(downloaded_filepaths)} files to GROBID for parsing...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures_to_file_info = {}
            for pdf_file, file_info in zip(downloaded_filepaths, files_info):
                # Submit each file to the executor
                future = executor.submit(
                    self.grobid_client.process_pdf,
                    "processFulltextDocument",
                    pdf_file=pdf_file,
                    **self.PARSING_OPTIONS
                )
                futures_to_file_info[future] = file_info

            # Wait for the result and update counts
            PARSER_NAME = "grobid_tei_parser"
            grobid_server_url = self.grobid_client.config["grobid_server"]

            for future in concurrent.futures.as_completed(futures_to_file_info):
                file_info = futures_to_file_info[future]

                pdf_file, status, text = future.result()

                if status != 200 or text is None:
                    # Log the error and create a ParseFileErrorInfo instance
                    err_file = ParseFileErrorInfo(
                        doc_id=file_info.doc_id,
                        source_filepath=file_info.source_filepath,
                        error_msg=f"GROBID processing (on {grobid_server_url}) for file: {file_info.source_filepath}, failed with status {status}: {text}",
                        parser=PARSER_NAME
                    )
                    outputs[file_info.doc_id] = err_file
                    error_count += 1
                    logger.warning(f"WARNING parsing file: {file_info.source_filepath} failed with error {status}: {text}")
                else:
                    # Save the output TEI XML to the specified output path
                    processed_count += 1
                    output_filename = (
                        Path(pdf_file).stem + ".grobid.tei.xml"
                    )  # Output filename is same as input but with .grobid.tei.xml extension
                    output_filepath = Path(output_path).joinpath(output_filename)
                    with open(output_filepath, "w", encoding="utf-8") as tei_file:
                        tei_file.write(text)

                    parsed_file = TEIFileDocument(
                        filepath=str(output_filepath),
                        metadata={
                            'doc_id': file_info.doc_id,
                            'source_filepath': file_info.source_filepath,
                            'parser': PARSER_NAME,
                        }
                    )
                    outputs[file_info.doc_id] = parsed_file
                    processed_count += 1
                    logger.info(f"Successfully parsed file: {file_info.source_filepath}")

        batch_elapsed = time.time() - batch_start_time
        if self.grobid_client.verbose:
            logger.info(
                f"Batch processed: {processed_count}, Errors: {error_count} in {batch_elapsed:.2f} seconds."
            )

        return outputs
