#%%
import os
import sys
import json
from pathlib import Path
sys.path.append(".")
sys.path.append("..")
from llama_index.core import SimpleDirectoryReader
from llama_index.core import Settings
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.ingestion import IngestionPipeline
from llama_index.core.evaluation import EmbeddingQAFinetuneDataset
from llama_index.finetuning import generate_qa_embedding_pairs
from llama_index.llms.ollama import Ollama

from finetuning.src.tei_parser import TEINodeParser
from finetuning.src.node_filters import TEINodeFilter
from finetuning.src.qa_generation_marcos_T5 import generate_qa_embedding_pairs_fromT5

"""
This script processes TEI documents to generate a Question-Answer (QA) dataset.
It reads TEI files from a specified directory, applies various transformations to parse and filter the content, 
and splits the text into manageable chunks. For each chunk, the script generates QA pairs using either 
an LLM or a custom T5 model. The resulting QA dataset is saved to a specified file.

Main Steps:
1. Load configuration settings from a JSON file.
2. Ingest and process TEI documents to create document chunks (nodes).
3. Generate and save  QA pairs for each chunk using a specified method.

Usage: Configure paths and parameters in `config.json` and run the script.
"""

#%%
def load_config(config_path: str) -> dict:
    with open(config_path, 'r') as file:
        return json.load(file)
    
def create_nodes_from_tei_path(tei_path: str, chunk_size: int, chunk_overlap: int):
    """Ingest and process TEI documents, returning parsed chunks (nodes)."""
    reader = SimpleDirectoryReader(input_dir=tei_path)
    documents = reader.load_data()

    file_parser = TEINodeParser()
    node_filter = TEINodeFilter()
    sentence_parser = SentenceSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    pipeline = IngestionPipeline(transformations=[file_parser, node_filter, sentence_parser])
    nodes = pipeline.run(documents=documents)
    
    return nodes
    

def main():
    """Main function to configure and run the ingestion and QA generation pipeline."""
    config = load_config("config.json")
    
    llm = Ollama(model="phi3", request_timeout=140.0)
    
    # Ingestion pipeline settings
    tei_path = config["paths"]["tei_directory"]
    chunk_size = config["ingestion_pipeline"]["chunk_size"]
    chunk_overlap = config["ingestion_pipeline"]["chunk_overlap"]
    
    # QA generation settings
    method = config["qa_generation"]["method"]
    prompt_template = config["qa_generation"]["prompt_template"]
    num_questions = config["qa_generation"]["num_questions_per_chunk"]
    output_path = config["paths"]["output_dataset"]
    
    # Run ingestion pipeline
    nodes = create_nodes_from_tei_path(tei_path, chunk_size, chunk_overlap)
    print(f"Generating questions from {len(nodes)} chunks." )
    # Generate QA dataset
    if method == "llm":
        qa = generate_qa_embedding_pairs(
            llm=llm,
            nodes=nodes,
            qa_generate_prompt_tmpl=prompt_template,
            num_questions_per_chunk=num_questions,
            output_path=output_path,
            verbose = False
        )
    elif method == "MarcosT5":
        qa = generate_qa_embedding_pairs_fromT5(
            nodes=nodes,
            num_questions_per_chunk=num_questions,
            output_path=output_path,
            verbose = False
        )
        
    print(f"Question-Answer dataset created and saved to {output_path}")
#%%
if __name__ == "__main__":
    main()
# %%
