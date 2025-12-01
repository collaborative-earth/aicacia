from typing import Sequence
from pathlib import Path
from data_ingestion.parsing.types import AbstractParser, ParsedFile
from grobid_client.grobid_client import GrobidClient

from core.app_config import configs


class GrobidTEIParsedFile(ParsedFile):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.metadata['parser'] = 'grobid_tei_parser'

    @classmethod
    def from_filepath(cls, filepath: str) -> "GrobidTEIParsedFile":
        return cls()


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
    ) -> Sequence[GrobidTEIParsedFile]:
        """Parse multiple files using GROBID's batch processing.
        Args:
            filepaths: Sequence of file paths to parse.
        Returns:
            Sequence of GrobidTEIParsedFile instances.
        """

        # Create output directory if it doesn't exist
        output_path = Path(self.TMP_LOCAL_FOLDER).joinpath("grobid_outputs")
        output_path.mkdir(parents=True, exist_ok=True)

        processed_count, error_count, skipped_count =\
            self.grobid_client.process_batch(
                "processFulltextDocument",
                input_path="",
                input_files=filepaths,
                output=str(output_path),
                force=True,
                **self.PARSING_OPTIONS
            )
        print(f"Processed: {processed_count}, Errors: {error_count}, Skipped: {skipped_count}")

        OUTPUT_EXTENSION = "grobid.tei.xml"
        output_filepaths = (
            output_path.joinpath(Path(fp).stem + f".{OUTPUT_EXTENSION}")
            for fp in filepaths
        )
        return [
            GrobidTEIParsedFile(
                filepath=str(output_filepath),
                metadata={'source_filepath': str(filepaths[i])}
            )
            for i, output_filepath in enumerate(output_filepaths) if output_filepath.exists()
        ]
