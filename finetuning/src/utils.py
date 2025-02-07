
import random
import json
from typing import Dict, List, Tuple
from llama_index.core.evaluation import EmbeddingQAFinetuneDataset
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core import SimpleDirectoryReader
from llama_index.core.ingestion import IngestionPipeline
from src.tei_parser import TEINodeParser
from src.node_filters import *

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

