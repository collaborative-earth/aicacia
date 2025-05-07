import os
import random
import json
import pymupdf4llm
import uuid
import csv
from copy import deepcopy
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

def merge_datasets(ds1: EmbeddingQAFinetuneDataset, ds2: EmbeddingQAFinetuneDataset):
    """
    Merge two QADataset objects into one, preserving all data and avoiding ID collisions.

    If there are duplicate query or document IDs between the two datasets, new UUIDs are generated
    for the conflicting entries in the second dataset (ds2) to maintain uniqueness.
    """
    merged_queries = deepcopy(ds1.queries)
    merged_corpus = deepcopy(ds1.corpus)
    merged_relevant_docs = deepcopy(ds1.relevant_docs)

    # Track existing IDs
    existing_query_ids = set(merged_queries.keys())
    existing_doc_ids = set(merged_corpus.keys())

    # Map for doc ID renaming
    doc_id_map = {}

    # Merge corpus from ds2
    for doc_id, doc in ds2.corpus.items():
        if doc_id in existing_doc_ids:
            print("IId collision")
            new_doc_id = str(uuid.uuid4())
            doc_id_map[doc_id] = new_doc_id
            merged_corpus[new_doc_id] = doc
            existing_doc_ids.add(new_doc_id)
        else:
            doc_id_map[doc_id] = doc_id
            merged_corpus[doc_id] = doc
            existing_doc_ids.add(doc_id)

    # Merge queries and relevant_docs
    for qid, query in ds2.queries.items():
        new_qid = qid
        if qid in existing_query_ids:
            new_qid = str(uuid.uuid4())
        merged_queries[new_qid] = query

        original_relevant_docs = ds2.relevant_docs[qid]
        remapped_relevant_docs = [doc_id_map[doc_id] for doc_id in original_relevant_docs]
        merged_relevant_docs[new_qid] = remapped_relevant_docs
        existing_query_ids.add(new_qid)

    return EmbeddingQAFinetuneDataset(
        queries=merged_queries,
        corpus=merged_corpus,
        relevant_docs=merged_relevant_docs
    )

def save_qa_dataset_to_beir_format(qa_dataset: EmbeddingQAFinetuneDataset, output_dir, prefix="qgen"):
    """
    Save a QA dataset to BEIR-compatible format.

    Args:
        qa_dataset: An object with `corpus`, `queries`, and `relevant_docs` attributes.
        output_dir (str): Path to output directory.
        prefix (str): Prefix for query and qrels file names.
    """
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(os.path.join(output_dir, "qrels"), exist_ok=True)

    # Save corpus
    corpus_path = os.path.join(output_dir, "corpus.jsonl")
    with open(corpus_path, "w") as f:
        for doc_id, doc_text in qa_dataset.corpus.items():
            beir_doc = {
                "_id": doc_id,
                "title": "",  # Add actual title here if available
                "text": doc_text
            }
            f.write(json.dumps(beir_doc) + "\n")

    # Save queries and build qrels
    queries_path = os.path.join(output_dir, f"{prefix}-queries.jsonl")
    qrels = {}
    with open(queries_path, "w") as f:
        for query_id, query_text in qa_dataset.queries.items():
            line_dict = {
                "_id": query_id,
                "text": query_text,
                "metadata": {}
            }
            f.write(json.dumps(line_dict) + "\n")

            corpus_ids = qa_dataset.relevant_docs.get(query_id, [])
            if corpus_ids:
                qrels[query_id] = {doc_id: 1 for doc_id in corpus_ids} # assuming one relevant doc per query

    # Save qrels
    qrels_path = os.path.join(output_dir, f"qrels/{prefix}-train.tsv")
    with open(qrels_path, "w") as fOut:
        writer = csv.writer(fOut, delimiter="\t", quoting=csv.QUOTE_MINIMAL)
        writer.writerow(["query-id", "corpus-id", "score"])
        for query_id, corpus_dict in qrels.items():
            for corpus_id, score in corpus_dict.items():
                writer.writerow([query_id, corpus_id, score])
                
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
