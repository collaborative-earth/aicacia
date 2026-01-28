#!/usr/bin/env python3
"""Convert LlamaIndex format to BEIR format."""

import sys
from pathlib import Path
import argparse
import logging
THIS_FILE = Path(__file__).resolve()
PROJECT_ROOT = THIS_FILE.parents[2]  # adjust if needed
sys.path.insert(0, str(PROJECT_ROOT))
from src.qa_generation.dataset_converters import llamaindex_to_beir

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="Convert LlamaIndex format to BEIR format"
    )
    
    parser.add_argument("--input", required=True, help="LlamaIndex JSON file")
    parser.add_argument("--output_dir", required=True, help="Output directory")
    parser.add_argument("--qgen_prefix", default="qgen", help="Prefix for queries/qrels")
    
    args = parser.parse_args()
    
    try:
        logger.info(f"Converting {args.input} to BEIR format")
        stats = llamaindex_to_beir(
            input_path=args.input,
            output_dir=args.output_dir,
            qgen_prefix=args.qgen_prefix
        )
        
        logger.info(f"Converted {stats['num_queries']} queries, "
                   f"{stats['num_corpus']} docs, {stats['num_qrels']} qrels")
        logger.info(f"Saved to {args.output_dir}")
        return 0
        
    except Exception as e:
        logger.error(f"Conversion failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())