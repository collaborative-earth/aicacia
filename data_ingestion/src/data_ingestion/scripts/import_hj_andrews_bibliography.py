#!/usr/bin/env python3
"""
Script to import HJ Andrews Bibliography CSV into sourced_documents table.
By default, downloads PDFs from source URLs and uploads them to S3.

Usage (run from project root):
    # Import metadata AND upload PDFs to S3 (default)
    python data_ingestion/scripts/import_hj_andrews_bibliography.py \
        [--csv-path path/to/file.csv] [--dry-run] [--limit N]

    # Import metadata only (skip S3 upload)
    python data_ingestion/scripts/import_hj_andrews_bibliography.py \
        --skip-s3-upload [--csv-path path/to/file.csv]

Note: The sys.path manipulation below ensures imports work regardless of where
the script is run from.
"""

import csv
import logging
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from db.db_manager import session_scope
from data_ingestion.custom_types.current_status_enum import CurrentStatusEnum
from db.models.sourced_documents import SourcedDocument, SourceLink

logger = logging.getLogger(__name__)


def parse_authors_from_citation(citation: str) -> list[str]:
    """Extract author names from citation string.

    Example: "Abdelnour, Alex G. 2011. Assessing ecosystem..."
    Returns: ["Abdelnour, Alex G."]
    """
    if not citation:
        return []

    # Try to extract author(s) before the year
    # Pattern: LastName, FirstName. Year or LastName, FirstName; LastName, FirstName. Year
    match = re.match(r'^([^0-9]+?)(?:\s+\d{4})', citation)
    if match:
        authors_str = match.group(1).strip()
        # Split by semicolon or comma (if multiple authors)
        authors = [a.strip() for a in re.split(r'[;,]', authors_str) if a.strip()]
        # Clean up trailing periods
        authors = [a.rstrip('.').strip() for a in authors if a.strip()]
        return authors[:5]  # Limit to first 5 authors

    return []


def extract_doi_from_text(text: str) -> Optional[str]:
    """Extract DOI from text if present."""
    if not text:
        return None

    # Look for DOI pattern: 10.xxxx/xxxx
    doi_pattern = r'10\.\d+/[^\s]+'
    match = re.search(doi_pattern, text)
    if match:
        return match.group(0)

    return None


def create_source_links(pdf_link: Optional[str], url: Optional[str]) -> list[SourceLink]:
    """Create SourceLink objects from PDF Link (only PDF, not web URL)."""
    links = []

    if pdf_link:
        links.append(SourceLink(
            link=pdf_link,
            type="pdf"
        ))

    return links


def download_and_upload_pdf(
    doc: SourcedDocument,
    pdf_url: str,
    bucket: str = "aicacia-extracted-data",
    max_retries: int = 3
) -> Optional[str]:
    """Download PDF from URL and upload to S3 with retry logic.

    Args:
        doc: SourcedDocument with doc_id and source_corpus
        pdf_url: URL to download PDF from
        bucket: S3 bucket name
        max_retries: Maximum number of retry attempts

    Returns:
        S3 path if successful, None if failed
    """
    import ssl
    import tempfile
    import time
    import urllib.request

    from core.fs_manager import fs_manager

    temp_file_path = None

    for attempt in range(max_retries):
        try:
            # Download PDF to temp file
            temp_dir = Path(tempfile.gettempdir())
            temp_file_path = temp_dir / f"{doc.doc_id}.pdf"

            if attempt == 0:
                logger.info(f"Downloading PDF for {doc.doc_id} from {pdf_url}")
            else:
                logger.info(f"Retry {attempt}/{max_retries - 1} for {doc.doc_id}")

            # Create SSL context that doesn't verify certificates
            # (andrewsforest.oregonstate.edu has self-signed cert in chain)
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE

            # Download using urlopen with SSL context
            with urllib.request.urlopen(pdf_url, context=ssl_context, timeout=30) as response:
                with open(temp_file_path, 'wb') as out_file:
                    out_file.write(response.read())

            # Verify file was written
            if not temp_file_path.exists() or temp_file_path.stat().st_size == 0:
                raise Exception("Downloaded file is empty or missing")

            # Upload to S3
            dest_dir = f"s3://{bucket}/{doc.source_corpus}"
            s3_path = fs_manager.upload_filepath(str(temp_file_path), dest_dir)

            logger.info(f"Uploaded to {s3_path}")

            # Clean up temp file
            temp_file_path.unlink()

            return s3_path

        except Exception as e:
            logger.warning(f"Attempt {attempt + 1} failed for {doc.doc_id}: {e}")

            # Clean up temp file if it exists
            if temp_file_path and temp_file_path.exists():
                temp_file_path.unlink()

            # If this was the last attempt, log error and return None
            if attempt == max_retries - 1:
                logger.error(
                    f"Failed to download/upload PDF for {doc.doc_id} "
                    f"after {max_retries} attempts: {e}"
                )
                return None

            # Wait before retrying (exponential backoff)
            time.sleep(2 ** attempt)

    return None


def download_and_upload_pdf_worker(
    doc_and_url: tuple[SourcedDocument, str],
    bucket: str,
    max_retries: int = 3,
    download_only: bool = False
) -> dict:
    """
    Worker function for parallel PDF download and upload.

    Args:
        doc_and_url: Tuple of (SourcedDocument, pdf_url)
        bucket: S3 bucket name
        max_retries: Number of retry attempts
        download_only: If True, skip S3 upload (for testing)

    Returns dict with keys:
        - 'doc': SourcedDocument
        - 's3_path': str or None
        - 'success': bool
        - 'error': str or None
        - 'download_time': float (seconds)
        - 'file_size': int (bytes)
    """
    import ssl
    import tempfile
    import time as time_module
    import urllib.request

    from core.fs_manager import fs_manager

    doc, pdf_url = doc_and_url

    # Create SSL context once per worker
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    temp_file_path = None
    download_start = time_module.time()

    for attempt in range(max_retries):
        try:
            # Download PDF
            temp_dir = Path(tempfile.gettempdir())
            temp_file_path = temp_dir / f"{doc.doc_id}.pdf"

            logger.info(f"Downloading PDF for {doc.doc_id} from {pdf_url}")

            with urllib.request.urlopen(pdf_url, context=ssl_context, timeout=30) as response:
                with open(temp_file_path, 'wb') as out_file:
                    out_file.write(response.read())

            # Verify file
            if not temp_file_path.exists() or temp_file_path.stat().st_size == 0:
                raise Exception("Downloaded file is empty or missing")

            file_size = temp_file_path.stat().st_size
            download_time = time_module.time() - download_start

            # Upload to S3 (unless download-only mode)
            s3_path = None
            if not download_only:
                dest_dir = f"s3://{bucket}/{doc.source_corpus}"
                s3_path = fs_manager.upload_filepath(str(temp_file_path), dest_dir)
                logger.info(f"Uploaded to {s3_path}")

            # Cleanup
            temp_file_path.unlink()

            return {
                'doc': doc,
                's3_path': s3_path,
                'success': True,
                'error': None,
                'download_time': download_time,
                'file_size': file_size
            }

        except Exception as e:
            # Cleanup
            if temp_file_path and temp_file_path.exists():
                temp_file_path.unlink()

            if attempt == max_retries - 1:
                logger.error(
                    f"Failed to download/upload {doc.doc_id} "
                    f"after {max_retries} attempts: {e}"
                )
                return {
                    'doc': doc,
                    's3_path': None,
                    'success': False,
                    'error': str(e),
                    'download_time': time_module.time() - download_start,
                    'file_size': 0
                }

            # Exponential backoff
            logger.warning(f"Retry {attempt + 1}/{max_retries - 1} for {doc.doc_id}")
            time_module.sleep(2 ** attempt)

    return {
        'doc': doc,
        's3_path': None,
        'success': False,
        'error': 'Max retries exceeded',
        'download_time': time_module.time() - download_start,
        'file_size': 0
    }


def process_documents_parallel(
    documents: list[tuple[SourcedDocument, list[SourceLink]]],
    bucket: str,
    workers: int,
    max_retries: int = 3,
    download_only: bool = False
) -> tuple[list[dict], list[dict]]:
    """
    Process documents in parallel: download PDFs and optionally upload to S3.

    Args:
        download_only: If True, skip S3 upload (for testing)

    Returns:
        (successful_results, failed_results)
    """
    import time
    from concurrent.futures import ThreadPoolExecutor
    from itertools import repeat

    # Prepare work items
    work_items = []
    failed = []

    for doc, source_links in documents:
        # Find PDF link
        pdf_link = None
        for link in source_links:
            if link.type == "pdf" or "pdf" in link.link.lower():
                pdf_link = link.link
                break

        if not pdf_link:
            logger.warning(f"No PDF link for {doc.title}")
            failed.append({'doc': doc, 'reason': 'No PDF link found'})
            continue

        work_items.append((doc, pdf_link))

    mode = "download-only" if download_only else "download and upload"
    logger.info(f"Processing {len(work_items)} documents with {workers} workers ({mode})")

    # Process in parallel
    successful = []
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=workers) as executor:
        results = executor.map(
            download_and_upload_pdf_worker,
            work_items,
            repeat(bucket),
            repeat(max_retries),
            repeat(download_only)
        )

        for result in results:
            if result['success']:
                successful.append(result)
            else:
                failed.append({'doc': result['doc'], 'reason': result['error']})

    elapsed = time.time() - start_time

    # Print statistics
    logger.info(f"Completed: {len(successful)} successful, {len(failed)} failed")
    logger.info(f"Total time: {elapsed:.1f}s")

    if successful:
        avg_time = sum(r['download_time'] for r in successful) / len(successful)
        total_size = sum(r['file_size'] for r in successful)
        logger.info(f"Average download time: {avg_time:.2f}s per document")
        logger.info(f"Total data downloaded: {total_size / (1024*1024):.1f} MB")
        logger.info(f"Throughput: {len(successful) / elapsed:.2f} docs/sec")

    return successful, failed


def import_csv_to_database(
    csv_path: str,
    source_corpus: str = "hj_andrews_bibliography",
    dry_run: bool = False,
    limit: Optional[int] = None,
    skip_s3_upload: bool = False,
    s3_bucket: str = "aicacia-extracted-data",
    workers: int = 10,
    download_only: bool = False
) -> None:
    """Import CSV file into sourced_documents table.

    Args:
        csv_path: Path to the CSV file (relative to project root or absolute)
        source_corpus: Name of the source corpus
        dry_run: If True, don't actually insert, just log what would be inserted
        limit: Maximum number of documents to process (None for all)
        skip_s3_upload: If True, skip downloading and uploading PDFs to S3
        s3_bucket: S3 bucket name for uploads
    """
    # Resolve CSV path relative to project root if not absolute
    csv_file = Path(csv_path)
    if not csv_file.is_absolute():
        csv_file = project_root / csv_file

    if not csv_file.exists():
        logger.error(f"CSV file not found: {csv_file}")
        sys.exit(1)

    logger.info(f"Reading CSV file: {csv_path}")
    if limit:
        logger.info(f"Limiting to first {limit} documents")

    documents: list[tuple[SourcedDocument, list[SourceLink]]] = []
    skipped = 0

    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is row 1)
            # Stop if limit reached
            if limit and len(documents) >= limit:
                logger.info(f"Reached limit of {limit} documents, stopping")
                break

            try:
                # Required fields
                title = row.get('Title', '').strip()
                if not title:
                    logger.warning(f"Row {row_num}: Skipping - missing title")
                    skipped += 1
                    continue

                # Extract authors from Citation
                authors = parse_authors_from_citation(row.get('Citation', ''))

                # Extract DOI from Citation or Abstract if present
                citation = row.get('Citation', '')
                abstract = row.get('Abstract', '')
                doi = extract_doi_from_text(citation) or extract_doi_from_text(abstract)

                # Create source links
                pdf_link = row.get('PDF Link', '').strip() or None
                url = row.get('URL', '').strip() or None
                source_links = create_source_links(pdf_link, url)

                # Build document
                doc = SourcedDocument(
                    title=title,
                    source_corpus=source_corpus,
                    sourced_at=datetime.now(),
                    authors=authors,
                    doi=doi,
                    page_link=url,
                    abstract=row.get('Abstract', '').strip() or None,
                    tags=[row.get('Publication Type', '').strip()] if row.get('Publication Type') else [],
                    other_metadata={
                        'publication_number': row.get('Publication Number', '').strip() or None,
                        'citation': citation,
                        'csv_id': row.get('ID', '').strip() or None,
                    },
                    current_status=CurrentStatusEnum.NEW.value,  # Pre-parsing status
                    s3_path=None,  # Will be set when PDF is downloaded
                    is_relevant=True,  # Assume all are relevant
                )

                documents.append((doc, source_links))

            except Exception as e:
                logger.error(f"Row {row_num}: Error processing row - {e}", exc_info=True)
                skipped += 1
                continue

    logger.info(f"Processed {len(documents)} documents, skipped {skipped} rows")

    if dry_run:
        logger.info("DRY RUN - Would insert the following documents:")
        for doc, links in documents[:5]:  # Show first 5
            logger.info(f"  - {doc.title} ({len(links)} links)")
        if len(documents) > 5:
            logger.info(f"  ... and {len(documents) - 5} more")
        return

    # Insert into database
    logger.info("Inserting documents into database...")

    # Log database connection info (without password)
    from core.app_config import configs
    logger.info(f"Database Host: {configs.POSTGRES_HOST}")
    logger.info(f"Database Port: {configs.POSTGRES_PORT}")
    logger.info(f"Database User: {configs.POSTGRES_USER}")
    logger.info(f"Database Name: {configs.POSTGRES_DB}")
    logger.info(f"Password length: {len(configs.POSTGRES_PASSWORD)} chars")
    logger.info(
        f"Password (masked): {configs.POSTGRES_PASSWORD[:2]}..."
        f"{configs.POSTGRES_PASSWORD[-2:]}"
    )

    # Track failures and duplicates
    failed_documents = []
    duplicate_documents = []

    # Query existing documents BEFORE parallel processing
    with session_scope() as session:
        existing_titles = set(
            title for (title,) in session.query(SourcedDocument.title)
            .filter(SourcedDocument.source_corpus == source_corpus)
            .all()
        )

    logger.info(
        f"Found {len(existing_titles)} existing documents in "
        f"corpus '{source_corpus}'"
    )

    # Filter out duplicates
    filtered_documents = []

    for doc, source_links in documents:
        if doc.title in existing_titles:
            logger.info(f"Skipping duplicate document: '{doc.title}'")
            duplicate_documents.append({
                'title': doc.title,
                'reason': 'Duplicate title in corpus'
            })
        else:
            filtered_documents.append((doc, source_links))

    logger.info(
        f"Processing {len(filtered_documents)} new documents "
        f"(skipped {len(duplicate_documents)} duplicates)"
    )

    # Process PDFs in parallel (unless --skip-s3-upload)
    if not skip_s3_upload:
        successful_results, failed_docs = process_documents_parallel(
            documents=filtered_documents,
            bucket=s3_bucket,
            workers=workers,
            max_retries=3,
            download_only=download_only
        )
        failed_documents.extend(failed_docs)

        # If download-only mode, stop here (don't insert to DB)
        if download_only:
            logger.info("=" * 80)
            logger.info("DOWNLOAD-ONLY MODE SUMMARY")
            logger.info("=" * 80)
            logger.info(f"Successfully downloaded: {len(successful_results)} PDFs")
            logger.info(f"Failed: {len(failed_documents)}")
            logger.info("Skipping database insertion (--download-only mode)")
            return
    else:
        # Skip S3, treat all as successful
        successful_results = [
            {'doc': doc, 's3_path': None, 'success': True}
            for doc, _ in filtered_documents
        ]

    # Insert successful documents to database
    logger.info("Inserting documents into database...")

    with session_scope() as session:
        batch_size = 50
        inserted_count = 0

        for i, result in enumerate(successful_results):
            try:
                doc = result['doc']
                s3_path = result.get('s3_path')

                # Update document with S3 path
                if s3_path:
                    doc.s3_path = s3_path

                # Add document
                session.add(doc)
                session.flush()  # Flush to get doc_id

                # Find original source_links from filtered_documents
                original_links = next(
                    (links for d, links in filtered_documents
                     if d.doc_id == doc.doc_id),
                    []
                )

                # Add source links
                for link in original_links:
                    link.doc_id = doc.doc_id
                    # Update PDF link with S3 location if available
                    if s3_path and (link.type == "pdf" or
                                    "pdf" in link.link.lower()):
                        link.s3_location = s3_path
                    session.add(link)

                # Commit in batches
                if (i + 1) % batch_size == 0:
                    session.commit()
                    inserted_count += batch_size
                    logger.info(
                        f"Inserted {inserted_count}/{len(successful_results)} "
                        f"documents..."
                    )

            except Exception as e:
                logger.error(
                    f"Error inserting document '{doc.title}': {e}",
                    exc_info=True
                )
                failed_documents.append({
                    'doc_id': str(doc.doc_id),
                    'title': doc.title,
                    'reason': f'Database error: {str(e)}'
                })
                session.rollback()
                continue

        # Commit remaining
        session.commit()
        successful_count = len(successful_results)
        logger.info(f"Successfully inserted {successful_count} documents")

    # Print summary
    logger.info("=" * 80)
    logger.info("IMPORT SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Total documents processed: {len(documents)}")
    logger.info(f"Successfully inserted: {successful_count}")
    logger.info(f"Duplicates skipped: {len(duplicate_documents)}")
    logger.info(f"Failed: {len(failed_documents)}")

    if duplicate_documents:
        logger.info("")
        logger.info("Duplicate Documents (skipped):")
        logger.info("-" * 80)
        for dup in duplicate_documents:
            logger.info(f"Title: {dup['title']}")
            logger.info(f"Reason: {dup['reason']}")
            logger.info("-" * 80)

    if failed_documents:
        logger.info("")
        logger.info("Failed Documents:")
        logger.info("-" * 80)
        for failed in failed_documents:
            # Handle both formats: parallel processing failures and DB insertion failures
            if 'doc' in failed:
                doc = failed['doc']
                logger.info(f"Doc ID: {doc.doc_id}")
                logger.info(f"Title: {doc.title}")
            else:
                logger.info(f"Doc ID: {failed.get('doc_id', 'Unknown')}")
                logger.info(f"Title: {failed.get('title', 'Unknown')}")
            logger.info(f"Reason: {failed['reason']}")
            logger.info("-" * 80)


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Import HJ Andrews Bibliography CSV into sourced_documents')
    parser.add_argument(
        '--csv-path',
        type=str,
        default='HJ Andrews Bibliography.xlsx - publications2.csv',
        help='Path to the CSV file (default: HJ Andrews Bibliography.xlsx - publications2.csv)'
    )
    parser.add_argument(
        '--source-corpus',
        type=str,
        default='hj_andrews_bibliography',
        help='Source corpus name (default: hj_andrews_bibliography)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Dry run - show what would be inserted without actually inserting'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='Limit the number of documents to process (useful for testing)'
    )
    parser.add_argument(
        '--skip-s3-upload',
        action='store_true',
        help='Skip downloading PDFs and uploading to S3 (metadata only)'
    )
    parser.add_argument(
        '--s3-bucket',
        type=str,
        default='aicacia-extracted-data',
        help='S3 bucket name (default: aicacia-extracted-data)'
    )
    parser.add_argument(
        '--workers',
        type=int,
        default=10,
        help='Number of parallel workers for PDF downloads (default: 10)'
    )
    parser.add_argument(
        '--download-only',
        action='store_true',
        help='Dry-run: download PDFs in parallel but skip S3 upload and DB insertion (for testing)'
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    import_csv_to_database(
        csv_path=args.csv_path,
        source_corpus=args.source_corpus,
        dry_run=args.dry_run,
        limit=args.limit,
        skip_s3_upload=args.skip_s3_upload,
        s3_bucket=args.s3_bucket,
        workers=args.workers,
        download_only=args.download_only
    )


if __name__ == '__main__':
    main()
