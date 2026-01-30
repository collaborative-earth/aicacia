import sys
from pathlib import Path
import logging

THIS_FILE = Path(__file__).resolve()
PROJECT_ROOT = THIS_FILE.parents[2]  
sys.path.insert(0, str(PROJECT_ROOT))

from src.qa_generation.qa_generationT5 import (
    GenerateQAT5Config,
    GenerateQAT5,
)

# Optional but recommended
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Command-line interface for GenerateQAT5."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate synthetic questions from corpus using T5"
    )

    # Config file or individual arguments
    parser.add_argument(
        "--config",
        type=str,
        help="Path to YAML config file (overrides individual arguments)"
    )

    # Required arguments (if not using config file)
    parser.add_argument("--corpus_path", type=str, help="Path to corpus.jsonl or directory")
    parser.add_argument("--output_dir", type=str, help="Output directory")

    # Query generation parameters
    parser.add_argument("--qgen_prefix", type=str, default="qgen")
    parser.add_argument("--generator", type=str, default="BeIR/query-gen-msmarco-t5-base-v1")
    parser.add_argument("--queries_per_passage", type=int, default=1)
    parser.add_argument("--batch_size_generation", type=int, default=32)

    # Negative mining parameters
    parser.add_argument("--mine_negatives",action="store_false")
    parser.add_argument("--retrievers", nargs="+", default=None)
    parser.add_argument("--retriever_score_functions", nargs="+", default=None)
    parser.add_argument("--negatives_per_query", type=int, default=50)
    parser.add_argument("--filter_questions", action="store_true", help="Filter queries where negative distribution is too similar to positive.")
    parser.add_argument("--new_size", type=int, default=None)

    # Config file generation
    parser.add_argument(
        "--save_config",
        type=str,
        help="Save current arguments as YAML config file and exit"
    )

    args = parser.parse_args()

    # Load from config file or create from arguments
    if args.config:
        logger.info(f"Loading configuration from {args.config}")
        config = GenerateQAT5Config.from_yaml(args.config)
    else:
        if not args.corpus_path or not args.output_dir:
            parser.error("--corpus_path and --output_dir are required (or use --config)")

        config = GenerateQAT5Config(
            corpus_path=args.corpus_path,
            output_dir=args.output_dir,
            qgen_prefix=args.qgen_prefix,
            generator=args.generator,
            queries_per_passage=args.queries_per_passage,
            batch_size_generation=args.batch_size_generation,
            mine_negatives= args.mine_negatives,
            retrievers = args.retrievers,
            retriever_score_functions =args.retriever_score_functions,
            negatives_per_query = args.negatives_per_query,
            new_size = args.new_size,
            filter_questions = args.filter_questions
        )

    # Save config and exit if requested
    if args.save_config:
        config.to_yaml(args.save_config)
        logger.info(f"Configuration saved to {args.save_config}")
        return 0

    # Run pipeline
    try:
        generator = GenerateQAT5(config)
        generator.run()
        return 0
    except Exception as e:
        logger.exception("Failed to generate questions")
        return 1


if __name__ == "__main__":
    sys.exit(main())
