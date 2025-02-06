#%%
import os
import sys
import json
import argparse
import datetime
from pathlib import Path
sys.path.append(".")
sys.path.append("..")
from src.utils import *
from llama_index.finetuning import generate_qa_embedding_pairs
from finetuning.src.qa_generation_marcos_T5 import generate_qa_embedding_pairs_fromT5

"""
This script processes TEI documents to generate a Question-Answer (QA) dataset.
It reads TEI files from a specified directory, applies various transformations to parse and filter the content, 
and splits the text into chunks. For each chunk, the script generates QA pairs using either 
an LLM or a custom T5 model. The resulting QA dataset is saved to a specified file.

Main Steps:
1. Load configuration settings from a JSON file.
2. Ingest and process TEI documents to create document chunks (nodes).
3. Generate and save  QA pairs for each chunk using a specified method.

Usage: Configure paths and parameters in `config.json` and run the script.
"""

def main():
    """Main function to configure and run the ingestion and QA generation pipeline."""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Generate a QA dataset from TEI files")
    parser.add_argument("--tei_path", type=str, help="Path to TEI directory")
    parser.add_argument("--num_questions", type=int, help="Number of questions per chunk")
    parser.add_argument("--output_path", type=str, help="Path to save the output dataset")
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config("config.json")
    
    # Overwrite config with command-line arguments if provided
    tei_path = args.tei_path if args.tei_path else config["paths"]["tei_directory"]
    num_questions = args.num_questions if args.num_questions else config["qa_generation"]["num_questions_per_chunk"]
    output_path = args.output_path if args.output_path else config["paths"]["output_dataset"]

    chunk_size = config["ingestion_pipeline"]["chunk_size"]
    chunk_overlap = config["ingestion_pipeline"]["chunk_overlap"]
    method = config["qa_generation"]["method"]
    prompt_template = config["qa_generation"]["prompt_template"]
    
    # Run ingestion pipeline
    nodes = create_nodes_from_tei_path(tei_path, chunk_size, chunk_overlap,apply_filter=True,valid_tags=['abstract', 'introduction', 'discussion'])
    print(f"Generating questions from {len(nodes)} chunks." )
    
    # Generate QA dataset
    if method == "llm":
        llm = Ollama(model="phi3", request_timeout=140.0)
        qa = generate_qa_embedding_pairs(
            llm=llm,
            nodes=nodes,
            qa_generate_prompt_tmpl=prompt_template,
            num_questions_per_chunk=num_questions,
            output_path=output_path,
            verbose=False
        )
    elif method == "MarcosT5":
        qa = generate_qa_embedding_pairs_fromT5(
            nodes=nodes,
            num_questions_per_chunk=num_questions,
            output_path=output_path,
            verbose=True
        )
        
    print(f"Question-Answer dataset created and saved to {output_path}")
    if save_metadata:
        metadata = {
            "creation_time": datetime.datetime.now().isoformat(),
            "tei_directory": config["paths"]["tei_directory"],
            "output_dataset": output_path,
            "chunk_size": config["ingestion_pipeline"]["chunk_size"],
            "chunk_overlap": config["ingestion_pipeline"]["chunk_overlap"],
            "qa_method": config["qa_generation"]["method"],
            "num_questions_per_chunk": config["qa_generation"]["num_questions_per_chunk"]
        }
        
        metadata_path = output_path.replace(".json", "_metadata.json")
        
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=4)

#%%
if __name__ == "__main__":
    main()
# %%
