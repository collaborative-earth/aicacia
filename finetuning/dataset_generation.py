#%%
import os
import sys
sys.path.append("..")

import json
from pathlib import Path
from llama_index.core import SimpleDirectoryReader
from llama_index.core import Settings
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.ingestion import IngestionPipeline
from llama_index.core.evaluation import EmbeddingQAFinetuneDataset
from llama_index.finetuning import generate_qa_embedding_pairs
from llama_index.llms.ollama import Ollama

from finetuning.src.node_parsers.tei_parser import TEINodeParser
from finetuning.src.node_parsers.node_filters import TEINodeFilter


#%%
def load_config(config_path: str) -> dict:
    with open(config_path, 'r') as file:
        return json.load(file)
    
def create_nodes_from_tei_path(tei_path: str, chunk_size: int, chunk_overlap: int):
    reader = SimpleDirectoryReader(input_dir=tei_path)
    documents = reader.load_data()

    file_parser = TEINodeParser()
    node_filter = TEINodeFilter()
    sentence_parser = SentenceSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    pipeline = IngestionPipeline(transformations=[file_parser, node_filter, sentence_parser])
    nodes = pipeline.run(documents=documents)
    
    return nodes

# Function to generate QA pairs and save them to output_path
def generate_qa_dataset(llm, nodes, prompt_template: str, num_questions: int, output_path: str):
    qa = generate_qa_embedding_pairs(
        llm=llm,
        nodes=nodes,
        qa_generate_prompt_tmpl=prompt_template,
        num_questions_per_chunk=num_questions,
        output_path=output_path
    )
    print(f"Question-Answer dataset created and saved to {output_path}")
    
# Main function
def main():
    # Load configurations from config.json
    config = load_config("config.json")
    
    # Set the LLM model and timeout
    llm = Ollama(model="phi3", request_timeout=140.0)
    
    # Ingestion pipeline settings
    tei_path = config["paths"]["tei_directory"]
    chunk_size = config["ingestion_pipeline"]["chunk_size"]
    chunk_overlap = config["ingestion_pipeline"]["chunk_overlap"]
    
    # QA generation settings
    prompt_template = config["qa_generation"]["prompt_template"]
    num_questions = config["qa_generation"]["num_questions_per_chunk"]
    output_path = config["paths"]["output_dataset"]
    
    # Run ingestion pipeline
    nodes = create_nodes_from_tei_path(tei_path, chunk_size, chunk_overlap)
    
    # Generate QA dataset
    generate_qa_dataset(Settings.llm, nodes, prompt_template, num_questions, output_path)

if __name__ == "__main__":
    main()
# %%
