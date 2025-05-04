import os
import random
import json
import pymupdf4llm
from typing import Dict, List, Tuple
from llama_index.core.evaluation import EmbeddingQAFinetuneDataset
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core import SimpleDirectoryReader
from llama_index.core.ingestion import IngestionPipeline
from llama_index.core.node_parser import MarkdownNodeParser, MarkdownElementNodeParser
from finetuning.src.node_filters import *
from vectordb.custom_parsers import *

def load_config(config_path: str) -> dict:
    with open(config_path, 'r') as file:
        return json.load(file)


    
def split_dataset(dataset: EmbeddingQAFinetuneDataset, train_ratio: float = 0.8) -> Tuple[EmbeddingQAFinetuneDataset, EmbeddingQAFinetuneDataset]:
    """
    Split a QA dataset into training and validation sets.

    Args:
        dataset (EmbeddingQAFinetuneDataset): The dataset to split.
        train_ratio (float): Proportion of the dataset to include in the training set (default is 0.8).

    Returns:
        Tuple[EmbeddingQAFinetuneDataset, EmbeddingQAFinetuneDataset]: A tuple containing the training and validation datasets.
    """
    query_ids = list(dataset.queries.keys())
    random.shuffle(query_ids)
    split_index = int(len(query_ids) * train_ratio)
    train_query_ids = query_ids[:split_index]
    val_query_ids = query_ids[split_index:]

    train_queries = {qid: dataset.queries[qid] for qid in train_query_ids}
    train_relevant_docs = {qid: dataset.relevant_docs[qid] for qid in train_query_ids}


    val_queries = {qid: dataset.queries[qid] for qid in val_query_ids}
    val_relevant_docs = {qid: dataset.relevant_docs[qid] for qid in val_query_ids}

    # Create corpus data (assuming it is shared between train and val)
    train_corpus = dataset.corpus
    val_corpus = dataset.corpus

    # Create new dataset instances
    train_dataset = EmbeddingQAFinetuneDataset(queries=train_queries,
                                               corpus = train_corpus,
                                               relevant_docs = train_relevant_docs)
    val_dataset = EmbeddingQAFinetuneDataset(queries=val_queries,
                                             corpus = val_corpus,
                                             relevant_docs = val_relevant_docs)

    return train_dataset, val_dataset


def create_nodes_from_tei_path(tei_path: str, chunk_size: int, chunk_overlap: int, apply_filter: bool = True, valid_tags: list = None, reverse: bool = False):
    """Ingest and process TEI documents, returning parsed chunks (nodes).
    
    Args:
        tei_path (str): Path to the directory containing TEI files.
        chunk_size (int): The size of each text chunk.
        chunk_overlap (int): Overlapping tokens between chunks.
        apply_filter (bool): Whether to apply TEINodeFilter.
        valid_tags (list): List of valid TEI tags to keep. If None, uses default.
        
    Returns:
        list: Processed nodes (chunks).
    """
    
    reader = SimpleDirectoryReader(input_dir=tei_path)
    documents = reader.load_data()

    file_parser = TEINodeParser()
    sentence_parser = SentenceSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    # Apply filtering only if specified
    node_filter = TEINodeFilter(valid_tags=valid_tags, reverse=reverse) if apply_filter else None

    # Define transformation steps
    transformations = [file_parser]
    if apply_filter:
        transformations.append(node_filter)
    transformations.append(sentence_parser)

    pipeline = IngestionPipeline(transformations=transformations)
    nodes = pipeline.run(documents=documents)
    
    return nodes

def create_nodes_from_pdf_path(pdf_path: str, chunk_size: int, chunk_overlap: int, use_llm: bool = True):
    """
    Ingest and process PDF documents, returning parsed chunks (nodes).
    
    Args:
        pdf_path (str): Path to the directory containing PDF files.
        chunk_size (int): The size of each text chunk.
        chunk_overlap (int): Overlapping tokens between chunks.
        use_llm (bool): Whether to use a more advanced parser (MarkdownElementNodeParser with LLM) or a simpler parser (MarkdownNodeParser).
        
    Returns:
        list: Processed nodes (chunks).
    """
    # Initialize PDF reader
    llama_reader = pymupdf4llm.LlamaMarkdownReader()
    
    docs = []
    # Process each PDF file in the directory
    for filename in os.listdir(pdf_path):
        if filename.endswith(".pdf"):
            print(f"Processing PDF: {filename}")
            docs.extend(llama_reader.load_data(os.path.join(pdf_path, filename)))

    # Choose the appropriate parser based on `use_llm`
    if use_llm:
        print("Using MarkdownElementNodeParser with LLM for advanced processing.")
        file_parser = MarkdownElementNodeParser(
            summary_query_str="Summarize the information contained in this table",
            ignore_metadata=True
        )
    else:
        print("Using MarkdownNodeParser for simpler processing.")
        file_parser = MarkdownNodeParser()

    # Create a sentence splitter for chunking the documents
    sentence_splitter = SentenceSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap, include_metadata=False)

    # Run the ingestion pipeline with the selected transformations
    pipeline = IngestionPipeline(transformations=[file_parser, sentence_splitter])
    nodes = pipeline.run(documents=docs)

    return nodes
