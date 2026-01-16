"""
Parsing CLI commands for the data_ingestion package.
"""

import logging
import click

from core.app_config import configs
from data_ingestion.parsing.parsing_manager import ParsingManager
from data_ingestion.parsing.parsers.grobid_parser import GrobidParser


logger = logging.getLogger(__name__)


@click.group()
def main() -> None:
    """Commands for the data_ingestion module."""
    pass


@main.command(name="parse-documents")
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Run without uploading parsed documents"
)
@click.option(
    "-bz",
    "--batch-size",
    type=int,
    default=100,
    help="Batch size for processing documents"
)
@click.option(
    "-outfolder",
    "--output-folder",
    type=str,
    default="hj_andrews_bibliography_parsed",
    help="Bucket folder name for organized output"
)
def parse_documents(
    dry_run: bool,
    batch_size: int,
    output_folder: str
) -> None:
    """Parse documents from configured directory."""
    logger.info("Starting document parsing...")

    default_parser = GrobidParser(host_url=configs.GROBID_URL)
    parsing_manager = ParsingManager(default_parser=default_parser)

    s3_bucket = configs.S3_BUCKET
    output_folder_full_path = f"{s3_bucket}/{output_folder}"

    logger.info(f"Parsing documents to {output_folder}")
    logger.info(f"Batch size: {batch_size}, Dry run: {dry_run}")

    parsed_documents = parsing_manager.parse_documents(
        dest_dir=output_folder_full_path,
        dry_run=dry_run,
        batch_size=batch_size
    )

    count = len(parsed_documents)

    logger.info(f"✓ Successfully processed {count} document(s)")
if __name__ == "__main__":
    main()
