#!/usr/bin/env python3
"""Convert BEIR format to LlamaIndex format."""

import sys
from pathlib import Path
import argparse
import logging

THIS_FILE = Path(__file__).resolve()
PROJECT_ROOT = THIS_FILE.parents[2]  # adjust if needed
sys.path.insert(0, str(PROJECT_ROOT))

from src.qa_generation.dataset_converters import beir_to_llamaindex

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="Convert BEIR format to LlamaIndex format"
    )

    parser.add_argument(
        "--beir_dir",
        required=True,
        help="BEIR format directory"
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Output LlamaIndex JSON file"
    )
    parser.add_argument(
        "--qgen_prefix",
        default="qgen",
        help="Prefix for queries/qrels"
    )

    args = parser.parse_args()

    try:
        logger.info(f"Converting {args.beir_dir} to LlamaIndex format")
        stats = beir_to_llamaindex(
            beir_dir=args.beir_dir,
            output_path=args.output,
            qgen_prefix=args.qgen_prefix,
        )

        logger.info(
            f"Converted {stats['num_queries']} queries, "
            f"{stats['num_corpus']} documents, "
            f"{stats['num_qrels']} qrels"
        )
        logger.info(f"Saved to {args.output}")
        return 0

    except Exception as e:
        logger.error(f"Conversion failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())