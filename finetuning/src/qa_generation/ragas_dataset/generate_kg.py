#!/usr/bin/env python3
"""
Script to generate Knowledge Graph from S3 data using YAML configuration.

Usage:
    python generate_kg.py --config config.yaml
    python generate_kg.py --config config.yaml --output custom_output.json
    python generate_kg.py --config config.yaml --load-existing kg_aer_v3.json
"""

import argparse
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent.parent.parent))
from kg_from_s3 import KG_fromS3, KGConfig


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate Knowledge Graph from S3 data"
    )
    
    parser.add_argument(
        "--config",
        type=str,
        required=True,
        help="Path to YAML configuration file"
    )
    
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Custom output path (overrides config)"
    )
    
    parser.add_argument(
        "--load-existing",
        type=str,
        default=None,
        help="Load existing KG instead of generating new one"
    )
    
    parser.add_argument(
        "--save-config-template",
        type=str,
        default=None,
        help="Save a configuration template to specified path and exit"
    )
    
    return parser.parse_args()


def create_config_template(output_path: str):
    """Create a template configuration file."""
    config = KGConfig(
        bucket_name="your-bucket-name",
        prefix="your/data/prefix",
    )
    config.to_yaml(output_path)
    print(f"Configuration template saved to: {output_path}")
    print("\nEdit the file and set these environment variables:")
    print("  - AWS_KEY")
    print("  - AWS_SECRET")
    print("  - OPENAI_API_KEY")


def main():
    """Main execution function."""
    args = parse_args()
    
    # Handle template creation
    if args.save_config_template:
        create_config_template(args.save_config_template)
        return 0
    
    # Load configuration
    try:
        config = KGConfig.from_yaml(args.config)
        print(f"Loaded configuration from: {args.config}")
    except Exception as e:
        print(f"Error loading configuration: {e}", file=sys.stderr)
        return 1
    
    # Override output path if provided
    if args.output:
        config.output_path = args.output
        config.auto_version = False
    
    # Validate secrets
    if not config.aws_key or not config.aws_secret:
        print("Error: AWS credentials not found. Set AWS_KEY and AWS_SECRET environment variables.", 
              file=sys.stderr)
        return 1
    
    if not config.openai_api_key and config.llm_provider == "openai":
        print("Error: OpenAI API key not found. Set OPENAI_API_KEY environment variable.", 
              file=sys.stderr)
        return 1
    
    # Initialize generator
    try:
        kg_generator = KG_fromS3(config)
    except Exception as e:
        print(f"Error initializing KG generator: {e}", file=sys.stderr)
        return 1
    
    # Load existing or generate new
    try:
        if args.load_existing:
            print(f"Loading existing knowledge graph from: {args.load_existing}")
            kg_generator.load(args.load_existing)
            output_path = kg_generator.generate_and_save()
            print(f"\n✓ Knowledge graph successfully generated and saved to: {output_path}")
            
        else:
            print("Starting knowledge graph generation...")
            print(f"Bucket: {config.bucket_name}")
            print(f"Prefix: {config.prefix}")
            print(f"Chunk size: {config.chunk_size}")
            print()
            
            output_path = kg_generator.generate_and_save()
            print(f"\n✓ Knowledge graph successfully generated and saved to: {output_path}")
            
    except KeyboardInterrupt:
        print("\n\nGeneration interrupted by user.", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"\nError during generation: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())