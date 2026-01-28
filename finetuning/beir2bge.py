#!/usr/bin/env python3
"""Convert BEIR format with hard negatives to BGE-M3 format."""

import sys
from pathlib import Path
import argparse
import logging
THIS_FILE = Path(__file__).resolve()
PROJECT_ROOT = THIS_FILE.parents[2]  # adjust if needed
sys.path.insert(0, str(PROJECT_ROOT))
from src.qa_generation.dataset_converters import beir_to_bgem3

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="Convert BEIR format with hard negatives to BGE-M3 format"
    )
    
    parser.add_argument("--beir_dir", required=True, help="BEIR format directory")
    parser.add_argument("--output", required=True, help="Output BGE-M3 jsonl file")
    parser.add_argument("--qgen_prefix", default="qgen", help="Prefix for queries/qrels")
    parser.add_argument("--sep", default=" ", help="Separator for title and text")
    parser.add_argument("--retriever", default=None, help="Specific retriever for negatives")
    parser.add_argument("--prompt", default="Represent this sentence for searching relevant passages:",
                       help="Query prompt")
    parser.add_argument("--allow_no_negatives", action="store_true",
                       help="Include queries without hard negatives")
    
    args = parser.parse_args()
    
    try:
        logger.info(f"Converting {args.beir_dir} to BGE-M3 format")
        stats = beir_to_bgem3(
            beir_dir=args.beir_dir,
            output_path=args.output,
            qgen_prefix=args.qgen_prefix,
            sep=args.sep,
            retriever=args.retriever,
            prompt=args.prompt,
            require_hard_negatives=not args.allow_no_negatives
        )
        
        logger.info(f"Converted {stats['total_queries']} queries "
                   f"({stats['queries_with_negatives']} with negatives, "
                   f"{stats['skipped_queries']} skipped)")
        logger.info(f"Avg: {stats['avg_positives']:.1f} pos, "
                   f"{stats['avg_negatives']:.1f} neg per query")
        logger.info(f"Saved to {args.output}")
        return 0
        
    except Exception as e:
        logger.error(f"Conversion failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())